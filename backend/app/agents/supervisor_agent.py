"""
Supervisor Pattern Implementation
複数のワーカーエージェントを統括し、タスクを適切に分配・実行します。
"""
from typing import List, Dict, Any, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
import operator
from app.models import Agent
from app.tools import ToolRegistry

# Watsonxは条件付きインポート
try:
    from langchain_ibm import WatsonxLLM
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


class SupervisorState(Dict):
    """Supervisorの状態管理"""
    messages: Annotated[List, operator.add]
    next: str
    task_description: str
    worker_results: Dict[str, Any]


class SupervisorAgent:
    """
    Supervisor Pattern implementation
    複数のワーカーエージェントを統括し、タスクを適切に分配・実行します。
    """
    
    def __init__(self, supervisor: Agent, workers: List[Agent],
                 tool_registry: ToolRegistry, checkpointer: SqliteSaver):
        """
        Args:
            supervisor: Supervisorエージェント
            workers: ワーカーエージェントのリスト
            tool_registry: ツールレジストリ
            checkpointer: チェックポインター（状態保存用）
        """
        self.supervisor = supervisor
        self.workers = {w.name: w for w in workers}
        self.tool_registry = tool_registry
        self.checkpointer = checkpointer
        
        # Supervisorの選択肢（ワーカー名 + FINISH）
        self.options = list(self.workers.keys()) + ["FINISH"]
        
        # グラフの構築
        self.graph = self._build_graph()
    
    def _create_supervisor_prompt(self) -> str:
        """Supervisor用のシステムプロンプトを作成"""
        worker_descriptions = "\n".join([
            f"- {name}: {agent.description or agent.role or 'General worker'}"
            for name, agent in self.workers.items()
        ])
        
        return f"""You are a supervisor managing a team of workers with the following roles:

{worker_descriptions}

Your responsibilities:
1. Analyze the given task and break it down into subtasks if needed
2. Assign each subtask to the most appropriate worker
3. Monitor worker progress and results
4. Coordinate between workers when needed
5. Synthesize final results and decide when the task is complete

Available workers: {', '.join(self.workers.keys())}

When you're ready to assign work, respond with:
- The name of the worker to assign the task to
- OR "FINISH" if the task is complete

Always explain your reasoning for each decision."""
    
    def _create_supervisor_node(self):
        """Supervisorノードを作成（次のワーカーを選択）"""
        llm = self._create_llm(
            self.supervisor.llm_provider,
            self.supervisor.llm_model,
            self.supervisor.llm_config or {}
        )
        
        system_prompt = self._create_supervisor_prompt()
        
        def supervisor_node(state: SupervisorState) -> Dict:
            """Supervisorが次のアクションを決定"""
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            
            # LLMに次のワーカーを選択させる
            response = llm.invoke(messages)
            
            # 応答から次のワーカーを抽出
            next_worker = self._extract_next_worker(response.content)
            
            return {
                "messages": [AIMessage(content=response.content)],
                "next": next_worker
            }
        
        return supervisor_node
    
    def _extract_next_worker(self, content: str) -> str:
        """LLMの応答から次のワーカー名を抽出"""
        content_upper = content.upper()
        
        # FINISHが含まれているかチェック
        if "FINISH" in content_upper:
            return "FINISH"
        
        # ワーカー名が含まれているかチェック
        for worker_name in self.workers.keys():
            if worker_name.upper() in content_upper:
                return worker_name
        
        # デフォルトは最初のワーカー
        return list(self.workers.keys())[0] if self.workers else "FINISH"
    
    def _create_llm(self, provider: str, model: str, config: Dict[str, Any]):
        """
        LLMインスタンスを作成
        
        Args:
            provider: LLMプロバイダー名
            model: モデル名
            config: LLM設定
            
        Returns:
            LLMインスタンス
        """
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        if provider == "openai":
            base_url = config.get("base_url")
            api_key = config.get("api_key", "dummy")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                base_url=base_url
            )
        elif provider == "anthropic":
            api_key = config.get("api_key", "dummy")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        elif provider == "gemini":
            api_key = config.get("api_key", "dummy")
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=api_key
            )
        elif provider == "ollama":
            base_url = config.get("base_url", "http://localhost:11434")
            return ChatOllama(
                model=model,
                temperature=temperature,
                base_url=base_url
            )
        elif provider == "watsonx":
            if not WATSONX_AVAILABLE:
                raise ValueError("Watsonx is not available. Please install langchain-ibm.")
            
            url = config.get("url", "https://us-south.ml.cloud.ibm.com")
            api_key = config.get("api_key", "dummy")
            project_id = config.get("project_id", "")
            
            return WatsonxLLM(
                model_id=model,
                url=url,
                apikey=api_key,
                project_id=project_id,
                params={
                    "temperature": temperature,
                    "max_new_tokens": max_tokens
                }
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _create_worker_node(self, worker_name: str):
        """ワーカーノードを作成"""
        worker = self.workers[worker_name]
        
        # ワーカーのLLMを取得
        llm = self._create_llm(
            worker.llm_provider,
            worker.llm_model,
            worker.llm_config or {}
        )
        
        # ワーカーのツールを取得
        tools = []
        if worker.tool_names:
            for tool_name in worker.tool_names:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    tools.append(tool)
        
        # ワーカーエージェントを作成
        worker_agent = create_react_agent(
            llm,
            tools=tools,
            state_modifier=f"""You are {worker.name}.
Role: {worker.role or 'Worker agent'}
Description: {worker.description or 'Execute assigned tasks'}

Execute the task assigned to you by the supervisor and report your results."""
        )
        
        def worker_node(state: SupervisorState) -> Dict:
            """ワーカーがタスクを実行"""
            result = worker_agent.invoke(state)
            
            # 結果を保存
            worker_results = state.get("worker_results", {})
            worker_results[worker_name] = result
            
            return {
                "messages": result["messages"],
                "worker_results": worker_results,
                "next": "supervisor"  # 次はSupervisorに戻る
            }
        
        return worker_node
    
    def _build_graph(self) -> StateGraph:
        """LangGraphのグラフを構築"""
        workflow = StateGraph(SupervisorState)
        
        # Supervisorノードを追加
        workflow.add_node("supervisor", self._create_supervisor_node())
        
        # 各ワーカーノードを追加
        for worker_name in self.workers.keys():
            workflow.add_node(worker_name, self._create_worker_node(worker_name))
        
        # エッジを追加
        # 各ワーカーからSupervisorへ
        for worker_name in self.workers.keys():
            workflow.add_edge(worker_name, "supervisor")
        
        # Supervisorから各ワーカーまたはFINISHへの条件付きエッジ
        def route_supervisor(state: SupervisorState) -> str:
            """Supervisorの決定に基づいてルーティング"""
            next_node = state.get("next", "FINISH")
            if next_node == "FINISH":
                return END
            return next_node
        
        workflow.add_conditional_edges(
            "supervisor",
            route_supervisor,
            {worker: worker for worker in self.workers.keys()} | {"FINISH": END}
        )
        
        # 開始ノードを設定
        workflow.set_entry_point("supervisor")
        
        # グラフをコンパイル
        return workflow.compile(checkpointer=self.checkpointer)
    
    def invoke(self, task_description: str, thread_id: str) -> Dict[str, Any]:
        """
        タスクを実行
        
        Args:
            task_description: タスクの説明
            thread_id: スレッドID（状態管理用）
        
        Returns:
            実行結果
        """
        initial_state = {
            "messages": [HumanMessage(content=task_description)],
            "next": "supervisor",
            "task_description": task_description,
            "worker_results": {}
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.graph.invoke(initial_state, config)
        
        return result
    
    def stream(self, task_description: str, thread_id: str):
        """
        タスクをストリーミング実行
        
        Args:
            task_description: タスクの説明
            thread_id: スレッドID（状態管理用）
        
        Yields:
            実行の各ステップ
        """
        initial_state = {
            "messages": [HumanMessage(content=task_description)],
            "next": "supervisor",
            "task_description": task_description,
            "worker_results": {}
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        for step in self.graph.stream(initial_state, config):
            yield step
