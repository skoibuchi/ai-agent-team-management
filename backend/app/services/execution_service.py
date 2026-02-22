"""
タスク実行サービス
LangGraphAgentを使用した自律的なタスク実行
"""
from datetime import datetime
from typing import Dict, Any, List
import threading
import os
import sqlite3
from app import db
from app.models import Task, Agent, ExecutionLog, TaskInteraction
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService
from app.agents.langgraph_agent import LangGraphAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.dynamic_team_agent import DynamicTeamAgent
from app.tools import ToolRegistry, create_human_input_tool
from app.websocket.events import (
    emit_task_interaction_new,
    emit_task_started,
    emit_task_progress,
    emit_task_completed,
    emit_task_failed
)
from langgraph.checkpoint.sqlite import SqliteSaver


class ExecutionService:
    """
    タスク実行サービス
    
    LangGraphAgentを使用して、ReActパターンによる
    自律的なタスク実行を行います。
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.tool_service = ToolService()
        # タスクIDとスレッドのマッピング
        self.running_threads = {}
    
    def execute_task_async(self, task_id: int):
        """タスクをバックグラウンドスレッドで実行"""
        def run_in_thread():
            # 新しいアプリケーションコンテキストを作成
            from app import create_app, socketio
            app = create_app()
            with app.app_context():
                # SocketIOのアプリケーションコンテキストも設定
                with app.test_request_context():
                    try:
                        self.execute_task(task_id)
                    except Exception as e:
                        print(f"Error in background task execution: {e}")
                        import traceback
                        traceback.print_exc()
                    finally:
                        # スレッド終了時にマッピングから削除
                        if task_id in self.running_threads:
                            del self.running_threads[task_id]
        
        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=run_in_thread, daemon=False, name=f"task-{task_id}")
        self.running_threads[task_id] = thread
        thread.start()
        
        print(f"Task {task_id} started in thread: {thread.name}")
        
        return {"message": "Task execution started in background"}
    
    def execute_task(self, task_id: int) -> Dict[str, Any]:
        """
        タスクを実行
        
        Args:
            task_id: タスクID
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        if not task.assigned_to:
            raise ValueError('Task must be assigned to an agent')
        
        agent = Agent.query.get(task.assigned_to)
        if not agent:
            raise ValueError(f'Agent {task.assigned_to} not found')
        
        # Dynamic Team Patternの場合（team_member_idsとleader_agent_idが設定されている）
        if task.team_member_ids and task.leader_agent_id:
            return self._execute_with_dynamic_team(task)
        
        # Supervisorエージェントの場合、チーム実行モードを使用
        if agent.agent_type == 'supervisor':
            return self._execute_with_supervisor(task, agent)
        
        try:
            # タスク開始
            task.status = 'running'
            task.started_at = datetime.utcnow()
            agent.status = 'running'
            db.session.commit()
            
            # WebSocketでタスク開始イベントを送信
            emit_task_started(task.id, agent.id)
            
            # 実行ログを作成
            self._log_action(task.id, agent.id, 'task_started', 'started')
            
            # 利用可能なツールを取得
            tools = self._get_available_tools(agent, task)
            
            # HumanInputToolを追加（task_idを設定）
            human_input_tool = create_human_input_tool(task.id)
            tools.append(human_input_tool)
            
            # LangGraphAgentを作成
            # エージェントのllm_configが空の場合、設定画面のLLM設定を使用
            llm_config = agent.llm_config or {}
            
            if not llm_config or not llm_config.get('api_key'):
                # 設定画面からLLM設定を取得
                from app.models.llm_setting import LLMSetting
                llm_setting = LLMSetting.query.filter_by(
                    provider=agent.llm_provider,
                    is_active=True
                ).first()
                
                if llm_setting:
                    print(f"Using LLM settings from Settings screen for provider: {agent.llm_provider}")
                    # llm_setting.configをベースにして、追加の設定をマージ
                    llm_config = dict(llm_setting.config) if llm_setting.config else {}
                    llm_config.update({
                        'api_key': llm_setting.get_api_key(),  # 復号化メソッドを使用
                        'base_url': llm_setting.base_url,
                        'model': agent.llm_model or llm_setting.default_model,
                        'temperature': llm_config.get('temperature', 0.7) if llm_config else 0.7,
                        'max_tokens': llm_config.get('max_tokens', 2000) if llm_config else 2000
                    })
                else:
                    print(f"Warning: No LLM settings found for provider: {agent.llm_provider}")
            
            print(f"Creating LangGraphAgent with:")
            print(f"  - Provider: {agent.llm_provider}")
            print(f"  - Model: {llm_config.get('model', agent.llm_model)}")
            print(f"  - Config keys: {list(llm_config.keys())}")
            print(f"  - Has api_key: {'api_key' in llm_config}")
            print(f"  - Has base_url: {'base_url' in llm_config}")
            
            # データベースパスを設定（タスクごとに異なるthread_idを使用するため、共通のDBを使用）
            import os
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "agent_memory.db")
            
            langgraph_agent = LangGraphAgent(
                agent_config={
                    'name': agent.name,
                    'role': agent.role,
                    'description': agent.description
                },
                llm_provider=agent.llm_provider,
                llm_config=llm_config,
                tools=tools,
                enable_memory=True,
                db_path=db_path
            )
            
            # タスクを実行
            self._log_action(
                task.id,
                agent.id,
                'agent_execution_started',
                'running',
                input_data={'task': task.description}
            )
            
            # インタラクション記録用のコールバック
            def log_interaction(event: Dict[str, Any]):
                """エージェントのイベントをTaskInteractionとして記録"""
                msg_type = event.get('type')
                content = event.get('content', '')
                message = event.get('message')
                
                # メッセージタイプに応じてインタラクションタイプを決定
                interaction_type = 'info'
                metadata: Dict[str, Any] = {}
                
                if msg_type == 'ai':
                    # AIの思考・応答
                    if message and hasattr(message, 'tool_calls') and getattr(message, 'tool_calls', None):
                        # ツール呼び出し
                        interaction_type = 'tool_call'
                        tool_calls = getattr(message, 'tool_calls', [])
                        metadata = {
                            'tool_calls': [
                                {
                                    'name': tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None),
                                    'args': tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', None),
                                    'id': tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                                }
                                for tc in tool_calls
                            ]
                        }
                    else:
                        # エージェントの思考
                        interaction_type = 'agent_thinking'
                elif msg_type == 'tool':
                    # ツール実行結果
                    interaction_type = 'tool_result'
                    if message and hasattr(message, 'name'):
                        metadata['tool_name'] = getattr(message, 'name', None)
                elif msg_type == 'human':
                    # ユーザー入力
                    interaction_type = 'info'
                
                # TaskInteractionを記録
                self._log_interaction(
                    task_id=task.id,
                    interaction_type=interaction_type,
                    content=str(content),
                    metadata=metadata
                )
            
            # タスクを実行（thread_idはタスクIDを使用）
            print("Starting task execution:")
            print(f"  - Task ID: {task.id}")
            print(f"  - Description: {task.description}")
            print(f"  - Auto mode: {task.auto_mode}")
            print(f"  - Available tools: {[tool.name for tool in tools]}")
            
            # 実行前にキャンセルチェック
            db.session.refresh(task)
            if task.status == 'cancelled':
                print(f"Task {task.id} was cancelled before execution")
                raise Exception("Task was cancelled")
            
            # ストリーミング実行でログ記録
            # thread_idにタイムスタンプを追加して一意性を保証（再起動後のID重複を防ぐ）
            thread_id = f"task-{task.id}-{int(task.created_at.timestamp())}"
            result = langgraph_agent.execute_with_streaming(
                task=task.description,
                thread_id=thread_id,
                callback=log_interaction,
                auto_mode=task.auto_mode
            )
            
            # 実行後にキャンセルチェック
            db.session.refresh(task)
            if task.status == 'cancelled':
                print(f"Task {task.id} was cancelled during execution")
                raise Exception("Task was cancelled")
            
            print("Task execution completed:")
            print(f"  - Result: {result}")
            
            # 結果に応じて処理を分岐
            if result.get('success'):
                # 成功時の処理
                self._log_interaction(
                    task_id=task.id,
                    interaction_type='result',
                    content=result.get('result', 'タスクを完了しました'),
                    metadata={'steps': result.get('steps', 0)}
                )
                
                # タスク完了
                task.status = 'completed'
                task.completed_at = datetime.utcnow()
                task.result = result
                agent.status = 'idle'
                
                # 完了ログ
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self._log_action(
                    task.id,
                    agent.id,
                    'task_completed',
                    'success',
                    output_data=result,
                    execution_time=execution_time
                )
                
                db.session.commit()
                
                # WebSocketでタスク完了イベントを送信（エラーが発生してもタスクステータスには影響させない）
                try:
                    emit_task_completed(task.id, result)
                except Exception as ws_error:
                    print(f"WebSocket emit error (task completed): {ws_error}")
            else:
                # 失敗時の処理
                error_message = result.get('error', 'タスクの実行に失敗しました')
                
                self._log_interaction(
                    task_id=task.id,
                    interaction_type='error',
                    content=error_message,
                    metadata={'result': result}
                )
                
                # タスク失敗
                task.status = 'failed'
                task.completed_at = datetime.utcnow()
                task.error_message = error_message
                task.result = result
                agent.status = 'idle'
                
                # エラーログ
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self._log_action(
                    task.id,
                    agent.id,
                    'task_failed',
                    'failed',
                    error_message=error_message,
                    execution_time=execution_time
                )
                
                db.session.commit()
                
                # WebSocketでタスク失敗イベントを送信
                emit_task_failed(task.id, error_message)
            
            return result
        
        except Exception as e:
            # キャンセルされた場合の処理
            if "cancelled" in str(e).lower() or task.status == 'cancelled':
                print(f"Task {task.id} was cancelled")
                
                # タスクがまだcancelledでない場合は設定
                if task.status != 'cancelled':
                    task.status = 'cancelled'
                
                task.completed_at = datetime.utcnow()
                task.error_message = 'Task was cancelled by user'
                agent.status = 'idle'
                
                # キャンセルログ
                self._log_interaction(
                    task_id=task.id,
                    interaction_type='info',
                    content='タスクがキャンセルされました'
                )
                
                self._log_action(
                    task.id,
                    agent.id,
                    'task_cancelled',
                    'failed',
                    error_message='Task cancelled by user'
                )
                
                db.session.commit()
                
                # WebSocketでタスク失敗イベントを送信
                emit_task_failed(task.id, 'Task cancelled by user')
                
                return {'success': False, 'error': 'Task cancelled by user'}
            
            # その他のエラー処理
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            agent.status = 'idle'
            
            # エラーログ
            self._log_action(
                task.id,
                agent.id,
                'task_failed',
                'failed',
                error_message=str(e)
            )
            
            db.session.commit()
            
            # WebSocketでタスク失敗イベントを送信
            emit_task_failed(task.id, str(e))
            
            raise
    
    def _get_available_tools(self, agent: Agent, task: Task) -> List[Any]:
        """
        エージェントとタスクが使用可能なツールを取得
        
        Args:
            agent: エージェント
            task: タスク
            
        Returns:
            List[Any]: ツール一覧（LangChain BaseToolのリスト）
        """
        # エージェントのデフォルトツール
        tool_names = set(agent.tool_names_list)
        
        # タスク固有のツールを追加
        if task.additional_tool_names_list:
            tool_names.update(task.additional_tool_names_list)
        
        # ツール名が指定されていない場合は空のリストを返す（ツール使用不可）
        # 注意: human_inputツールは別途ExecutionServiceで追加されます
        if not tool_names:
            print(f"No tools assigned to agent '{agent.name}'. Agent will run without tools (except human_input).")
            return []
        
        # ToolRegistryから指定されたツールを取得
        tools = []
        for name in tool_names:
            tool = ToolRegistry.get_tool(name)
            if tool:
                # HumanInputToolの場合はtask_idを設定
                if name == 'human_input' and hasattr(tool, 'task_id'):
                    tool.task_id = task.id
                tools.append(tool)
            else:
                print(f"Warning: Tool '{name}' not found in ToolRegistry")
        
        print(f"Agent '{agent.name}' using tools: {[t.name for t in tools]}")
        return tools
    
    def _log_action(
        self,
        task_id: int,
        agent_id: int,
        action: str,
        status: str,
        input_data: Dict[str, Any] | None = None,
        output_data: Dict[str, Any] | None = None,
        error_message: str | None = None,
        execution_time: float | None = None
    ):
        """
        実行ログを記録
        
        Args:
            task_id: タスクID
            agent_id: エージェントID
            action: アクション名
            status: ステータス
            input_data: 入力データ
            output_data: 出力データ
            error_message: エラーメッセージ
            execution_time: 実行時間（秒）
        """
        log = ExecutionLog(
            task_id=task_id,
            agent_id=agent_id,
            action=action,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            execution_time=execution_time
        )
        db.session.add(log)
        db.session.commit()
    
    def _log_interaction(
        self,
        task_id: int,
        interaction_type: str,
        content: str,
        metadata: Dict[str, Any] | None = None,
        requires_response: bool = False
    ):
        """
        タスクインタラクションを記録
        
        Args:
            task_id: タスクID
            interaction_type: インタラクションタイプ
            content: コンテンツ
            metadata: メタデータ
            requires_response: ユーザー応答が必要か
        """
        interaction = TaskInteraction(
            task_id=task_id,
            interaction_type=interaction_type,
            content=content,
            metadata=metadata or {},
            requires_response=requires_response,
            created_at=datetime.utcnow()
        )
        db.session.add(interaction)
        
        # Taskのupdated_atを更新して差分取得APIで検知できるようにする
        task = Task.query.get(task_id)
        if task:
            task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # WebSocketでリアルタイム配信
        try:
            emit_task_interaction_new(task_id, interaction)
        except Exception as e:
            # WebSocket配信エラーは無視（ログ記録は成功している）
            print(f"WebSocket emit error: {e}")
    
    def monitor_execution(self, task_id: int) -> Dict[str, Any]:
        """
        実行状況を監視
        
        Args:
            task_id: タスクID
            
        Returns:
            Dict[str, Any]: 実行状況
        """
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        return {
            'task_id': task.id,
            'status': task.status,
            'progress': task.get_progress(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'logs': [
                log.to_dict() 
                for log in task.execution_logs.order_by(ExecutionLog.created_at).all()
            ]
        }
    
    def cancel_task(self, task_id: int):
        """
        タスクをキャンセル
        
        Args:
            task_id: タスクID
        """
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        if task.status != 'running':
            raise ValueError(f'Task {task_id} is not running')
        
        task.status = 'cancelled'
        task.completed_at = datetime.utcnow()
        
        if task.assigned_to:
            agent = Agent.query.get(task.assigned_to)
            if agent:
                agent.status = 'idle'
        
        self._log_action(
            task.id,
            task.assigned_to,
            'task_cancelled',
            'cancelled'
        )
        
        db.session.commit()

    
    def _execute_with_supervisor(self, task: Task, supervisor: Agent) -> Dict[str, Any]:
        """
        Supervisorエージェントを使用してタスクを実行
        
        Args:
            task: タスク
            supervisor: Supervisorエージェント
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # タスク開始
            task.status = 'running'
            task.started_at = datetime.utcnow()
            supervisor.status = 'running'
            db.session.commit()
            
            # WebSocketでタスク開始イベントを送信
            emit_task_started(task.id, supervisor.id)
            
            # 実行ログを作成
            self._log_action(task.id, supervisor.id, 'supervisor_task_started', 'started')
            
            # Supervisorのワーカーを取得
            workers = supervisor.workers
            if not workers:
                raise ValueError(f'Supervisor {supervisor.name} has no workers assigned')
            
            print(f"Supervisor '{supervisor.name}' managing {len(workers)} workers:")
            for worker in workers:
                print(f"  - {worker.name} ({worker.role})")
                
                # データベースパスを設定
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "agent_memory.db")
            
            # SqliteSaverを作成
            conn = sqlite3.connect(db_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
            
            # SupervisorAgentを作成（ToolRegistryはクラスメソッドで使用されるため、インスタンスは不要）
            # 各ワーカーのLLM設定を取得して設定
            for worker in workers:
                if not worker.llm_config or not worker.llm_config.get('api_key'):
                    worker.llm_config = self._get_llm_config(worker)
            
            supervisor_agent = SupervisorAgent(
                supervisor=supervisor,
                workers=list(workers),
                tool_registry=ToolRegistry(),
                checkpointer=checkpointer
            )
            
            # インタラクション記録用のコールバック
            def log_interaction(step: Dict[str, Any]):
                """Supervisorのステップをログ記録"""
                # ステップの内容を解析してログ記録
                node_name = list(step.keys())[0] if step else 'unknown'
                node_data = step.get(node_name, {})
                
                if node_name == 'supervisor':
                    # Supervisorの決定
                    messages = node_data.get('messages', [])
                    if messages:
                        last_message = messages[-1]
                        content = getattr(last_message, 'content', str(last_message))
                        self._log_interaction(
                            task_id=task.id,
                            interaction_type='agent_thinking',
                            content=f"[Supervisor] {content}",
                            metadata={'node': 'supervisor'}
                        )
                elif node_name in [w.name for w in workers]:
                    # ワーカーの実行
                    messages = node_data.get('messages', [])
                    if messages:
                        last_message = messages[-1]
                        content = getattr(last_message, 'content', str(last_message))
                        self._log_interaction(
                            task_id=task.id,
                            interaction_type='info',
                            content=f"[Worker: {node_name}] {content}",
                            metadata={'node': node_name, 'worker': True}
                        )
            
            # タスクを実行
            print("Starting supervisor task execution:")
            print(f"  - Task ID: {task.id}")
            print(f"  - Description: {task.description}")
            print(f"  - Supervisor: {supervisor.name}")
            
            # 実行前にキャンセルチェック
            db.session.refresh(task)
            if task.status == 'cancelled':
                print(f"Task {task.id} was cancelled before execution")
                raise Exception("Task was cancelled")
            
            # ストリーミング実行でログ記録
            thread_id = f"supervisor-task-{task.id}-{int(task.created_at.timestamp())}"
            
            for step in supervisor_agent.stream(task.description, thread_id):
                # ステップをログ記録
                log_interaction(step)
                
                # キャンセルチェック
                db.session.refresh(task)
                if task.status == 'cancelled':
                    print(f"Task {task.id} was cancelled during execution")
                    raise Exception("Task was cancelled")
            
            # 最終結果を取得
            result = supervisor_agent.invoke(task.description, thread_id)
            
            print("Supervisor task execution completed:")
            print(f"  - Result: {result}")
            
            # 成功時の処理
            self._log_interaction(
                task_id=task.id,
                interaction_type='info',
                content='タスクが正常に完了しました（Supervisor Pattern）'
            )
            
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result = result
            supervisor.status = 'idle'
            
            # 成功ログ
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self._log_action(
                task.id,
                supervisor.id,
                'supervisor_task_completed',
                'completed',
                output_data=result,
                execution_time=execution_time
            )
            
            db.session.commit()
            
            # WebSocketでタスク完了イベントを送信（エラーが発生してもタスクステータスには影響させない）
            try:
                emit_task_completed(task.id, result)
            except Exception as ws_error:
                print(f"WebSocket emit error (supervisor task completed): {ws_error}")
            
            return {'success': True, 'result': result}
        
        except Exception as e:
            # キャンセルされた場合の処理
            if "cancelled" in str(e).lower() or task.status == 'cancelled':
                print(f"Supervisor task {task.id} was cancelled")
                
                if task.status != 'cancelled':
                    task.status = 'cancelled'
                
                task.completed_at = datetime.utcnow()
                task.error_message = 'Task was cancelled by user'
                supervisor.status = 'idle'
                
                self._log_interaction(
                    task_id=task.id,
                    interaction_type='info',
                    content='タスクがキャンセルされました（Supervisor Pattern）'
                )
                
                self._log_action(
                    task.id,
                    supervisor.id,
                    'supervisor_task_cancelled',
                    'failed',
                    error_message='Task cancelled by user'
                )
                
                db.session.commit()
                emit_task_failed(task.id, 'Task cancelled by user')
                
                return {'success': False, 'error': 'Task cancelled by user'}
            
            # その他のエラー処理
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            supervisor.status = 'idle'
            
            self._log_action(
                task.id,
                supervisor.id,
                'supervisor_task_failed',
                'failed',
                error_message=str(e)
            )
            
            db.session.commit()
            emit_task_failed(task.id, str(e))
            
            raise
    
    def _get_llm_config(self, agent: Agent) -> Dict[str, Any]:
        """
        エージェントのLLM設定を取得
        
        Args:
            agent: エージェント
            
        Returns:
            Dict[str, Any]: LLM設定
        """
        llm_config = agent.llm_config or {}
        
        if not llm_config or not llm_config.get('api_key'):
            # 設定画面からLLM設定を取得
            from app.models.llm_setting import LLMSetting
            llm_setting = LLMSetting.query.filter_by(
                provider=agent.llm_provider,
                is_active=True
            ).first()
            
            if llm_setting:
                llm_config = dict(llm_setting.config) if llm_setting.config else {}
                llm_config.update({
                    'api_key': llm_setting.get_api_key(),
                    'base_url': llm_setting.base_url,
                    'model': agent.llm_model or llm_setting.default_model,
                    'temperature': llm_config.get('temperature', 0.7) if llm_config else 0.7,
                    'max_tokens': llm_config.get('max_tokens', 2000) if llm_config else 2000
                })
        
        return llm_config

    
    def _execute_with_dynamic_team(self, task: Task) -> Dict[str, Any]:
        """
        Dynamic Team Patternを使用してタスクを実行
        
        Args:
            task: タスク
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # リーダーエージェントを取得
            leader = Agent.query.get(task.leader_agent_id)
            if not leader:
                raise ValueError(f'Leader agent {task.leader_agent_id} not found')
            
            # チームメンバーを取得
            member_ids = task.team_member_ids_list
            if not member_ids:
                raise ValueError('No team members assigned')
            
            members = Agent.query.filter(Agent.id.in_(member_ids)).all()
            if len(members) != len(member_ids):
                raise ValueError('Some team members not found')
            
            # タスク開始
            task.status = 'running'
            task.started_at = datetime.utcnow()
            leader.status = 'running'
            db.session.commit()
            
            # WebSocketでタスク開始イベントを送信
            emit_task_started(task.id, leader.id)
            
            # 実行ログを作成
            self._log_action(task.id, leader.id, 'dynamic_team_task_started', 'started')
            
            print(f"Dynamic Team: Leader '{leader.name}' managing {len(members)} members:")
            for member in members:
                print(f"  - {member.name} ({member.role})")
            
            # データベースパスを設定
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "agent_memory.db")
            
            # SqliteSaverを作成
            conn = sqlite3.connect(db_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
            
            # リーダーとメンバーのLLM設定を取得してLLMインスタンスを作成
            leader_llm_config = self._get_llm_config(leader)
            
            # リーダーのLLMインスタンスを作成
            if leader.llm_provider == 'openai':
                from langchain_openai import ChatOpenAI
                leader_llm = ChatOpenAI(
                    model=leader_llm_config.get('model', 'gpt-4'),
                    api_key=leader_llm_config.get('api_key'),
                    base_url=leader_llm_config.get('base_url'),
                    temperature=leader_llm_config.get('temperature', 0.7),
                    max_tokens=leader_llm_config.get('max_tokens', 2000)
                )
            elif leader.llm_provider == 'anthropic':
                from langchain_anthropic import ChatAnthropic
                leader_llm = ChatAnthropic(
                    model=leader_llm_config.get('model', 'claude-3-sonnet-20240229'),
                    api_key=leader_llm_config.get('api_key'),
                    temperature=leader_llm_config.get('temperature', 0.7),
                    max_tokens=leader_llm_config.get('max_tokens', 2000)
                )
            else:
                raise ValueError(f'Unsupported LLM provider for Dynamic Team: {leader.llm_provider}')
            
            # メンバーのLLMインスタンスとツールを作成
            member_llms = {}
            member_configs = {}
            member_tools = {}
            for member in members:
                member_llm_config = self._get_llm_config(member)
                
                if member.llm_provider == 'openai':
                    from langchain_openai import ChatOpenAI
                    member_llms[member.id] = ChatOpenAI(
                        model=member_llm_config.get('model', 'gpt-4'),
                        api_key=member_llm_config.get('api_key'),
                        base_url=member_llm_config.get('base_url'),
                        temperature=member_llm_config.get('temperature', 0.7),
                        max_tokens=member_llm_config.get('max_tokens', 2000)
                    )
                elif member.llm_provider == 'anthropic':
                    from langchain_anthropic import ChatAnthropic
                    member_llms[member.id] = ChatAnthropic(
                        model=member_llm_config.get('model', 'claude-3-sonnet-20240229'),
                        api_key=member_llm_config.get('api_key'),
                        temperature=member_llm_config.get('temperature', 0.7),
                        max_tokens=member_llm_config.get('max_tokens', 2000)
                    )
                else:
                    raise ValueError(f'Unsupported LLM provider for Dynamic Team member: {member.llm_provider}')
                
                member_configs[member.id] = {
                    'name': member.name,
                    'role': member.role,
                    'description': member.description
                }
                
                # 各メンバーのツールを取得
                member_tools[member.id] = self._get_available_tools(member, task)
            
            # リーダーのツールを取得
            leader_tools = self._get_available_tools(leader, task)
            
            # DynamicTeamAgentを作成
            team_agent = DynamicTeamAgent(
                leader_llm=leader_llm,
                member_llms=member_llms,
                leader_agent_config={
                    'name': leader.name,
                    'role': leader.role,
                    'description': leader.description
                },
                member_agent_configs=member_configs,
                leader_tools=leader_tools,
                member_tools=member_tools,
                task_id=task.id,
                checkpointer=checkpointer
            )
            
            # タスクを実行
            print("Starting dynamic team task execution:")
            print(f"  - Task ID: {task.id}")
            print(f"  - Description: {task.description}")
            print(f"  - Leader: {leader.name}")
            
            # 実行前にキャンセルチェック
            db.session.refresh(task)
            if task.status == 'cancelled':
                print(f"Task {task.id} was cancelled before execution")
                raise Exception("Task was cancelled")
            
            # ストリーミング実行でログ記録
            final_state = None
            print("Starting stream_execute loop...")
            step_count = 0
            for step in team_agent.stream_execute(task.description):
                step_count += 1
                print(f"Stream step {step_count}: {list(step.keys()) if step else 'empty'}")
                
                # ステップをログ記録
                node_name = list(step.keys())[0] if step else 'unknown'
                node_data = step.get(node_name, {})
                final_state = node_data  # 最後のステップを保存
                
                print(f"Node: {node_name}, has messages: {'messages' in node_data}")
                
                if 'messages' in node_data:
                    messages = node_data['messages']
                    if messages:
                        last_message = messages[-1]
                        content = getattr(last_message, 'content', str(last_message))
                        print(f"Logging interaction: [{node_name}] {content[:100]}...")
                        self._log_interaction(
                            task_id=task.id,
                            interaction_type='info',
                            content=f"[{node_name}] {content}",
                            metadata={'node': node_name}
                        )
                
                # キャンセルチェック
                db.session.refresh(task)
                if task.status == 'cancelled':
                    print(f"Task {task.id} was cancelled during execution")
                    raise Exception("Task was cancelled")
            
            print(f"Stream execute completed. Total steps: {step_count}")
            
            # 最終結果を取得（stream_executeの最後のステートから）
            # messagesをJSON化可能な形式に変換
            messages = final_state.get('messages', []) if final_state else []
            serializable_messages = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    serializable_messages.append({
                        'type': msg.__class__.__name__,
                        'content': msg.content
                    })
                else:
                    serializable_messages.append(str(msg))
            
            result = {
                'success': True,
                'result': final_state.get('final_result', '') if final_state else '',
                'messages': serializable_messages,
                'leader_plan': final_state.get('leader_plan', '') if final_state else '',
                'member_results': final_state.get('member_results', {}) if final_state else {}
            }
            
            print("Dynamic team task execution completed:")
            print(f"  - Result: {result}")
            
            # 成功時の処理
            self._log_interaction(
                task_id=task.id,
                interaction_type='result',
                content='タスクが正常に完了しました（Dynamic Team Pattern）'
            )
            
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result = result
            leader.status = 'idle'
            
            # 成功ログ
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self._log_action(
                task.id,
                leader.id,
                'dynamic_team_task_completed',
                'completed',
                output_data=result,
                execution_time=execution_time
            )
            
            db.session.commit()
            
            # WebSocketでタスク完了イベントを送信（エラーが発生してもタスクステータスには影響させない）
            try:
                emit_task_completed(task.id, result)
            except Exception as ws_error:
                print(f"WebSocket emit error (task completed): {ws_error}")
            
            return {'success': True, 'result': result}
        
        except Exception as e:
            # キャンセルされた場合の処理
            if "cancelled" in str(e).lower() or task.status == 'cancelled':
                print(f"Dynamic team task {task.id} was cancelled")
                
                if task.status != 'cancelled':
                    task.status = 'cancelled'
                
                task.completed_at = datetime.utcnow()
                task.error_message = 'Task was cancelled by user'
                
                if task.leader_agent_id:
                    leader = Agent.query.get(task.leader_agent_id)
                    if leader:
                        leader.status = 'idle'
                
                self._log_interaction(
                    task_id=task.id,
                    interaction_type='info',
                    content='タスクがキャンセルされました（Dynamic Team Pattern）'
                )
                
                self._log_action(
                    task.id,
                    task.leader_agent_id,
                    'dynamic_team_task_cancelled',
                    'failed',
                    error_message='Task cancelled by user'
                )
                
                db.session.commit()
                emit_task_failed(task.id, 'Task cancelled by user')
                
                return {'success': False, 'error': 'Task cancelled by user'}
            
            # その他のエラー処理
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            
            if task.leader_agent_id:
                leader = Agent.query.get(task.leader_agent_id)
                if leader:
                    leader.status = 'idle'
            
            self._log_action(
                task.id,
                task.leader_agent_id,
                'dynamic_team_task_failed',
                'failed',
                error_message=str(e)
            )
            
            db.session.commit()
            emit_task_failed(task.id, str(e))
            
            raise
