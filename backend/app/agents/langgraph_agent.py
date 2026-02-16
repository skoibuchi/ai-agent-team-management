"""
LangGraphベースのAgent実装（標準ReActエージェント使用）
"""
from typing import Dict, Any, List
import os
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

# Watsonxは条件付きインポート
try:
    from langchain_ibm import WatsonxLLM
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False


class LangGraphAgent:
    """
    LangGraphベースのAgent実装
    
    LangGraphの標準ReActエージェント（create_react_agent）を使用して、
    タスクを自律的に分析・実行します。
    
    特徴:
    - LangChain標準のツールを使用
    - Function Calling自動対応
    - メモリ機能（会話履歴保持）
    - ReActパターン（Reasoning + Acting）
    - ステートフルな実行管理
    """
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        llm_provider: str,
        llm_config: Dict[str, Any],
        tools: List[Any],
        enable_memory: bool = True,
        db_path: str | None = None
    ):
        """
        Args:
            agent_config: エージェント設定
            llm_provider: LLMプロバイダー名
            llm_config: LLM設定
            tools: 利用可能なツール一覧（LangChain BaseToolのリスト）
            enable_memory: メモリ機能を有効にするか
            db_path: SQLiteデータベースファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        self.config = agent_config
        self.llm = self._create_llm(llm_provider, llm_config)
        self.tools = tools
        self.enable_memory = enable_memory
        
        # メモリの設定（SqliteSaverで永続化）
        if enable_memory:
            # データベースファイルのパスを設定
            if db_path is None:
                # デフォルト: backend/data/agent_memory.db
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                os.makedirs(data_dir, exist_ok=True)
                db_path = os.path.join(data_dir, "agent_memory.db")
            
            # SqliteSaverを作成（会話履歴を永続化）
            # SQLite接続文字列を使用してインスタンス化
            import sqlite3
            conn = sqlite3.connect(db_path, check_same_thread=False)
            self.checkpointer = SqliteSaver(conn)
        else:
            self.checkpointer = None
        
        # ReActエージェントの作成
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )
    
    def _create_llm(self, provider: str, config: Dict[str, Any]):
        """
        LLMインスタンスを作成
        
        Args:
            provider: LLMプロバイダー名
            config: LLM設定
            
        Returns:
            LLMインスタンス
        """
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        model = config.get("model", "")
        
        if provider == "openai":
            # base_urlが指定されている場合（GitHub Models等）
            base_url = config.get("base_url")
            kwargs = {
                "model": model or "gpt-4",
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_key": config.get("api_key", "")
            }
            if base_url:
                kwargs["base_url"] = base_url
            return ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model or "claude-3-5-sonnet-20241022",
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=config.get("api_key", "")
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model or "gemini-2.0-flash-exp",
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=config.get("api_key", "")
            )
        elif provider == "ollama":
            return ChatOllama(
                model=model or "llama2",
                temperature=temperature,
                base_url=config.get("base_url", "http://localhost:11434")
            )
        elif provider == "watsonx":
            # WatsonxLLMはFunction Calling（bind_tools）をサポートしていないため、
            # create_react_agentでは使用できません
            raise ValueError(
                "watsonx.ai is not currently supported with LangGraph ReAct agent. "
                "WatsonxLLM does not support Function Calling (bind_tools method). "
                "Please use OpenAI, Anthropic, or Gemini providers instead."
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def execute(self, task: str, thread_id: str = "default", auto_mode: bool = False) -> Dict[str, Any]:
        """
        タスクを実行
        
        Args:
            task: 実行するタスクの説明
            thread_id: スレッドID（会話履歴の識別子）
            auto_mode: 自動実行モード
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # 設定（メモリ有効時はthread_idを使用）
            config = {}
            if self.enable_memory:
                config = {"configurable": {"thread_id": thread_id}}
            
            # モードに応じたシステムプロンプトを追加
            if auto_mode:
                mode_instruction = """[自動実行モード]
あなたは自律的にタスクを完了する必要があります。
不明な情報がある場合は、合理的な仮定を立てて進めてください。
human_inputツールは使用しないでください。"""
            else:
                mode_instruction = """[対話実行モード - 最重要指示]

あなたは対話型エージェントです。以下のルールに**絶対に**従ってください：

【ルール1】不明な情報がある場合は、**必ず**human_inputツールを呼び出してください
【ルール2】直接回答を返すことは**完全に禁止**されています
【ルール3】質問が必要な場合は、human_inputツールを使用する以外の選択肢はありません

必須のツール使用ケース：
- ファイルパスが不明 → human_input("ファイルパスを教えてください")
- 処理方法が不明 → human_input("どのように処理しますか？")
- 確認が必要 → human_input("〜してもよろしいですか？")
- 詳細が不明確 → human_input("詳細を教えてください")

【重要な例】
タスク: "ファイルを読み取り、要約し、出力する"

✅ 正しい対応:
Action: human_input
Action Input: {"question": "読み取るファイルのパスを教えてください"}

❌ 誤った対応（絶対禁止）:
"まず、読み取るファイルのパスを教えていただけますか？"

human_inputツールを使わずに質問を返すことは、このシステムでは機能しません。
必ずツールを使用してください。"""
            
            # タスクにモード指示を追加
            enhanced_task = f"{mode_instruction}\n\n【タスク】\n{task}"
            
            # エージェントを実行
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=enhanced_task)]},
                config=config
            )
            
            # 結果を整形
            messages = result.get("messages", [])
            final_message = messages[-1] if messages else None
            
            return {
                "success": True,
                "result": final_message.content if final_message else "タスクを完了しました",
                "messages": [
                    {
                        "role": msg.type,
                        "content": msg.content
                    }
                    for msg in messages
                ],
                "steps": len(messages)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"タスクの実行に失敗しました: {str(e)}",
                "result": None
            }
    
    def execute_with_streaming(
        self,
        task: str,
        thread_id: str = "default",
        callback=None,
        auto_mode: bool = False
    ) -> Dict[str, Any]:
        """
        タスクをストリーミング実行（リアルタイムログ記録用）
        
        Args:
            task: 実行するタスクの説明
            thread_id: スレッドID
            callback: イベントコールバック関数
            auto_mode: 自動実行モード（Trueの場合、ユーザー確認なしで実行）
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # 設定
            config = {}
            if self.enable_memory:
                config = {"configurable": {"thread_id": thread_id}}
            
            # モードに応じた強力なシステムプロンプトを追加
            if auto_mode:
                mode_instruction = """[自動実行モード]
あなたは自律的にタスクを完了する必要があります。
不明な情報がある場合は、合理的な仮定を立てて進めてください。
human_inputツールは使用しないでください。"""
            else:
                mode_instruction = """[対話実行モード - 最重要指示]

あなたは対話型エージェントです。以下のルールに**絶対に**従ってください：

【ルール1】不明な情報がある場合は、**必ず**human_inputツールを呼び出してください
【ルール2】直接回答を返すことは**完全に禁止**されています
【ルール3】質問が必要な場合は、human_inputツールを使用する以外の選択肢はありません

必須のツール使用ケース：
- ファイルパスが不明 → human_input("ファイルパスを教えてください")
- 処理方法が不明 → human_input("どのように処理しますか？")
- 確認が必要 → human_input("〜してもよろしいですか？")
- 詳細が不明確 → human_input("詳細を教えてください")

【重要な例】
タスク: "ファイルを読み取り、要約し、出力する"

✅ 正しい対応:
Action: human_input
Action Input: {"question": "読み取るファイルのパスを教えてください"}

❌ 誤った対応（絶対禁止）:
"まず、読み取るファイルのパスを教えていただけますか？"

human_inputツールを使わずに質問を返すことは、このシステムでは機能しません。
必ずツールを使用してください。"""
            
            # タスクにモード指示を追加
            enhanced_task = f"{mode_instruction}\n\n【タスク】\n{task}"
            
            # ストリーミング実行
            all_messages = []
            print(f"[DEBUG] Starting agent.stream with enhanced_task length: {len(enhanced_task)}")
            print(f"[DEBUG] Enhanced task preview: {enhanced_task[:200]}...")
            print(f"[DEBUG] Config: {config}")
            print(f"[DEBUG] Agent type: {type(self.agent)}")
            print(f"[DEBUG] LLM type: {type(self.llm)}")
            
            event_count = 0
            for event in self.agent.stream(
                {"messages": [HumanMessage(content=enhanced_task)]},
                config=config,
                stream_mode="values"
            ):
                event_count += 1
                print(f"[DEBUG] Event #{event_count} received")
                messages = event.get("messages", [])
                print(f"[DEBUG] Event has {len(messages)} total messages")
                
                if messages:
                    # 新しいメッセージのみを処理
                    new_messages = messages[len(all_messages):]
                    print(f"[DEBUG] Processing {len(new_messages)} new messages")
                    
                    for msg in new_messages:
                        msg_content = str(msg.content)
                        print(f"[DEBUG] New message - Type: {msg.type}, Content length: {len(msg_content)}")
                        
                        # ツール呼び出しをチェック
                        if hasattr(msg, 'tool_calls'):
                            tool_calls = getattr(msg, 'tool_calls', [])
                            if tool_calls:
                                print(f"[DEBUG] Message has {len(tool_calls)} tool calls")
                                for tc in tool_calls:
                                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown')
                                    print(f"[DEBUG] Tool call: {tool_name}")
                        
                        # 内容の一部を表示（デバッグ用）
                        if len(msg_content) > 0:
                            preview = msg_content[:100] + "..." if len(msg_content) > 100 else msg_content
                            print(f"[DEBUG] Content preview: {preview}")
                        
                        # コールバックを呼び出し
                        if callback:
                            callback({
                                "type": msg.type,
                                "content": msg.content,
                                "message": msg
                            })
                    all_messages = messages
            
            print(f"[DEBUG] Agent.stream completed. Total events: {event_count}, Total messages: {len(all_messages)}")
            
            # 最終結果
            final_message = all_messages[-1] if all_messages else None
            
            return {
                "success": True,
                "result": final_message.content if final_message else "タスクを完了しました",
                "messages": [
                    {
                        "role": msg.type,
                        "content": msg.content
                    }
                    for msg in all_messages
                ],
                "steps": len(all_messages)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"タスクの実行に失敗しました: {str(e)}",
                "result": None
            }
    
    def execute_with_history(
        self,
        task: str,
        thread_id: str,
        previous_messages: List[Dict[str, str]] | None = None
    ) -> Dict[str, Any]:
        """
        会話履歴を考慮してタスクを実行
        
        Args:
            task: 実行するタスクの説明
            thread_id: スレッドID
            previous_messages: 以前のメッセージ（オプション）
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        # メモリが有効な場合は自動的に履歴が保持される
        return self.execute(task, thread_id)
    
    def get_conversation_history(self, thread_id: str) -> List[Dict[str, str]]:
        """
        会話履歴を取得
        
        Args:
            thread_id: スレッドID
            
        Returns:
            List[Dict[str, str]]: 会話履歴
        """
        if not self.enable_memory or not self.checkpointer:
            return []
        
        try:
            # チェックポイントから履歴を取得
            config = {"configurable": {"thread_id": thread_id}}
            state = self.checkpointer.get(config)
            
            if state and "messages" in state:
                return [
                    {
                        "role": msg.type,
                        "content": msg.content
                    }
                    for msg in state["messages"]
                ]
            return []
        except Exception:
            return []
    
    def clear_conversation_history(self, thread_id: str):
        """
        会話履歴をクリア
        
        Args:
            thread_id: スレッドID
        """
        if not self.enable_memory or not self.checkpointer:
            return
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            self.checkpointer.put(config, {"messages": []})
        except Exception:
            pass
