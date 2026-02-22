"""
Dynamic Team Agent
動的チーム編成パターンの実装

タスクごとに異なるチームメンバーとリーダーを指定して実行します。
"""
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
from operator import add


class TeamState(TypedDict):
    """チーム実行の状態"""
    messages: Annotated[List[BaseMessage], add]
    leader_plan: str
    member_results: Dict[str, str]  # agent_name -> result
    final_result: str
    next_action: str


class DynamicTeamAgent:
    """
    動的チーム編成エージェント
    
    タスクごとに異なるチームメンバーとリーダーを指定して、
    協調的にタスクを実行します。
    
    特徴:
    - タスクごとにチームメンバーを動的に選択
    - リーダーエージェントが全体を調整
    - 各メンバーが専門性を活かして貢献
    """
    
    def __init__(
        self,
        leader_llm: BaseChatModel,
        member_llms: Dict[int, BaseChatModel],
        leader_agent_config: Dict[str, Any],
        member_agent_configs: Dict[int, Dict[str, Any]],
        leader_tools: List[BaseTool],
        member_tools: Dict[int, List[BaseTool]],
        task_id: int,
        checkpointer: Optional[SqliteSaver] = None
    ):
        """
        Args:
            leader_llm: リーダーエージェントのLLM
            member_llms: メンバーエージェントのLLM辞書 {agent_id: llm}
            leader_agent_config: リーダーエージェントの設定
            member_agent_configs: メンバーエージェントの設定辞書 {agent_id: config}
            leader_tools: リーダーが使用可能なツールのリスト
            member_tools: メンバーが使用可能なツールの辞書 {agent_id: tools}
            task_id: タスクID
            checkpointer: チェックポイント保存用
        """
        self.leader_llm = leader_llm
        self.member_llms = member_llms
        self.leader_agent_config = leader_agent_config
        self.member_agent_configs = member_agent_configs
        self.leader_tools = leader_tools
        self.member_tools = member_tools
        self.task_id = task_id
        self.checkpointer = checkpointer
        
        # グラフを構築
        print(f"[DynamicTeamAgent] Initializing for task {task_id}")
        print(f"[DynamicTeamAgent] Leader: {leader_agent_config.get('name')}")
        print(f"[DynamicTeamAgent] Members: {[c.get('name') for c in member_agent_configs.values()]}")
        self.graph = self._build_graph()
        print("[DynamicTeamAgent] Graph built successfully")
    
    def _build_graph(self) -> StateGraph:
        """
        動的チーム実行グラフを構築
        
        フロー:
        1. リーダーがタスクを分析し、各メンバーに指示
        2. 各メンバーが並行して作業
        3. リーダーが結果を統合
        4. 必要に応じて追加作業を指示
        """
        # グラフ作成
        workflow = StateGraph(TeamState)
        
        # リーダーノード: タスク分析と計画
        def leader_plan_node(state: TeamState) -> Dict[str, Any]:
            """リーダーがタスクを分析し、各メンバーに作業を割り当て"""
            print("\n=== Leader Plan Node ===")
            messages = state["messages"]
            print(f"Input messages: {len(messages)}")
            
            # リーダーのシステムプロンプト
            leader_prompt = f"""あなたは{self.leader_agent_config['name']}です。
役割: {self.leader_agent_config['role']}

チームメンバー:
"""
            for agent_id, config in self.member_agent_configs.items():
                leader_prompt += f"- {config['name']} ({config['role']})\n"
            
            leader_prompt += """
タスクを分析し、各メンバーに適切な作業を割り当ててください。
各メンバーの専門性を活かした効率的な作業分担を考えてください。

作業計画を以下の形式で出力してください:
【作業計画】
1. メンバーA: 担当作業の説明
2. メンバーB: 担当作業の説明
...
"""
            
            # SystemMessageを先頭に追加
            messages_with_system = [SystemMessage(content=leader_prompt)] + messages
            
            print("[Leader] Invoking LLM...")
            response = self.leader_llm.invoke(messages_with_system)
            plan = response.content if hasattr(response, 'content') else str(response)
            print(f"[Leader] Plan generated: {plan[:100]}...")
            
            # 新しいメッセージのみを返す（addで既存のものと結合される）
            return {
                "messages": [AIMessage(content=f"[リーダー計画]\n{plan}")],
                "leader_plan": plan,
                "next_action": "execute_members"
            }
        
        # メンバー実行ノード
        def execute_members_node(state: TeamState) -> Dict[str, Any]:
            """各メンバーが並行して作業を実行"""
            print("\n=== Execute Members Node ===")
            messages = state["messages"]
            leader_plan = state["leader_plan"]
            member_results = {}
            new_messages = []
            
            for agent_id, config in self.member_agent_configs.items():
                member_name = config['name']
                print(f"[Member] Processing: {member_name}")
                
                # メンバーのシステムプロンプト
                member_prompt = f"""あなたは{member_name}です。
役割: {config['role']}

リーダーからの指示:
{leader_plan}

あなたの担当部分を実行してください。
"""
                
                # メンバーエージェントで作業を実行
                member_llm = self.member_llms.get(agent_id)
                member_tools = self.member_tools.get(agent_id, [])
                
                if not member_llm:
                    print(f"[Member] Warning: No LLM found for {member_name}")
                    continue
                
                print(f"[Member] {member_name} has {len(member_tools)} tools")
                
                # ツールがある場合はcreate_react_agentを使用
                if member_tools:
                    from langgraph.prebuilt import create_react_agent
                    
                    # システムメッセージを追加
                    member_messages = [SystemMessage(content=member_prompt)] + messages
                    
                    # メンバーエージェントを作成
                    member_agent = create_react_agent(
                        member_llm,
                        member_tools
                    )
                    
                    # エージェントを実行
                    print(f"[Member] {member_name} invoking agent with tools...")
                    agent_result = member_agent.invoke(
                        {"messages": member_messages},
                        config={"configurable": {"thread_id": f"member_{agent_id}"}}
                    )
                    
                    # 最後のメッセージを取得
                    result_messages = agent_result.get("messages", [])
                    if result_messages:
                        last_message = result_messages[-1]
                        member_result = last_message.content if hasattr(last_message, 'content') else str(last_message)
                    else:
                        member_result = "作業を完了しました。"
                else:
                    # ツールがない場合はLLMを直接呼び出し
                    member_messages = [SystemMessage(content=member_prompt)] + messages
                    
                    print(f"[Member] {member_name} invoking LLM (no tools)...")
                    response = member_llm.invoke(member_messages)
                    member_result = response.content if hasattr(response, 'content') else str(response)
                
                print(f"[Member] {member_name} result: {member_result[:100]}...")
                
                member_results[member_name] = member_result
                new_messages.append(AIMessage(content=f"[{member_name}の作業結果]\n{member_result}"))
            
            return {
                "messages": new_messages,
                "member_results": member_results,
                "next_action": "leader_review"
            }
        
        # リーダーレビューノード
        def leader_review_node(state: TeamState) -> Dict[str, Any]:
            """リーダーがメンバーの結果をレビューし、統合"""
            print("\n=== Leader Review Node ===")
            messages = state["messages"]
            member_results = state["member_results"]
            
            # リーダーのレビュープロンプト
            review_prompt = f"""あなたは{self.leader_agent_config['name']}です。

チームメンバーの作業結果:
"""
            for member_name, result in member_results.items():
                review_prompt += f"\n【{member_name}】\n{result}\n"
            
            review_prompt += """
これらの結果をレビューし、統合してください。
追加作業が必要な場合は「追加作業が必要」と明記してください。
完了している場合は最終結果をまとめてください。
"""
            
            # SystemMessageを先頭に追加
            review_messages = [SystemMessage(content=review_prompt)] + messages
            
            print("[Leader] Reviewing results...")
            response = self.leader_llm.invoke(review_messages)
            final_result = response.content if hasattr(response, 'content') else str(response)
            print(f"[Leader] Review: {final_result[:100]}...")
            
            # 追加作業が必要かどうかを判断
            needs_more_work = "追加作業が必要" in final_result or "再度" in final_result or "もう一度" in final_result
            next_action = "execute_members" if needs_more_work else "end"
            
            print(f"[Leader] Next action: {next_action}")
            
            return {
                "messages": [AIMessage(content=f"[リーダーレビュー]\n{final_result}")],
                "final_result": final_result,
                "next_action": next_action
            }
        
        # ノードを追加
        workflow.add_node("leader_plan", leader_plan_node)
        workflow.add_node("execute_members", execute_members_node)
        workflow.add_node("leader_review", leader_review_node)
        
        # エッジを追加
        workflow.set_entry_point("leader_plan")
        workflow.add_edge("leader_plan", "execute_members")
        workflow.add_edge("execute_members", "leader_review")
        
        # 条件付きエッジ: レビュー後の分岐
        def should_continue(state: TeamState) -> str:
            next_action = state.get("next_action", "end")
            return next_action if next_action != "end" else END
        
        workflow.add_conditional_edges(
            "leader_review",
            should_continue,
            {
                "execute_members": "execute_members",
                END: END
            }
        )
        
        # チェックポイント付きでコンパイル
        if self.checkpointer:
            print("[DynamicTeamAgent] Compiling graph WITH checkpointer")
            return workflow.compile(checkpointer=self.checkpointer)
        else:
            print("[DynamicTeamAgent] Compiling graph WITHOUT checkpointer")
            return workflow.compile()
    
    def execute(self, task_description: str, user_message: Optional[str] = None) -> Dict[str, Any]:
        """
        タスクを実行
        
        Args:
            task_description: タスクの説明
            user_message: ユーザーからの追加メッセージ（オプション）
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        # 初期メッセージ
        messages = [HumanMessage(content=task_description)]
        if user_message:
            messages.append(HumanMessage(content=user_message))
        
        # グラフを実行
        config = {"configurable": {"thread_id": f"task_{self.task_id}"}}
        result = self.graph.invoke(
            {
                "messages": messages,
                "leader_plan": "",
                "member_results": {},
                "final_result": "",
                "next_action": ""
            },
            config=config
        )
        
        return {
            "success": True,
            "result": result.get("final_result", ""),
            "messages": result.get("messages", []),
            "leader_plan": result.get("leader_plan", ""),
            "member_results": result.get("member_results", {})
        }
    
    def stream_execute(self, task_description: str, user_message: Optional[str] = None):
        """
        タスクをストリーミング実行
        
        Args:
            task_description: タスクの説明
            user_message: ユーザーからの追加メッセージ（オプション）
            
        Yields:
            Dict[str, Any]: 実行ステップごとの結果
        """
        print(f"\n{'='*60}")
        print(f"[DynamicTeamAgent] Starting stream execution")
        print(f"[DynamicTeamAgent] Task: {task_description[:100]}...")
        print(f"{'='*60}\n")
        
        # 初期メッセージ
        messages = [HumanMessage(content=task_description)]
        if user_message:
            messages.append(HumanMessage(content=user_message))
        
        # グラフをストリーミング実行
        config = {"configurable": {"thread_id": f"task_{self.task_id}"}}
        initial_state = {
            "messages": messages,
            "leader_plan": "",
            "member_results": {},
            "final_result": "",
            "next_action": ""
        }
        
        print(f"[DynamicTeamAgent] Initial state prepared")
        print(f"[DynamicTeamAgent] Config: {config}")
        
        step_count = 0
        try:
            # stream_mode="updates"を指定して、各ノードの更新を取得
            for step in self.graph.stream(initial_state, config=config, stream_mode="updates"):
                step_count += 1
                node_name = list(step.keys())[0] if step else "unknown"
                print(f"\n[DynamicTeamAgent] Step {step_count}: {node_name}")
                print(f"[DynamicTeamAgent] Step data keys: {list(step.get(node_name, {}).keys())}")
                yield step
            
            print(f"\n[DynamicTeamAgent] Stream completed. Total steps: {step_count}")
        except Exception as e:
            print(f"\n[DynamicTeamAgent] ERROR in stream: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"{'='*60}\n")
