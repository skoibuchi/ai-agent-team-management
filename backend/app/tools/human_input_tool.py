"""
Human Input Tool
エージェントがユーザーに質問して応答を待つツール
"""
from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from app import db
from app.models import TaskInteraction
from datetime import datetime


class HumanInputSchema(BaseModel):
    """Human Input Toolの入力スキーマ"""
    question: str = Field(description="ユーザーに尋ねる質問")


class HumanInputTool(BaseTool):
    """
    ユーザーに質問して応答を待つツール
    
    エージェントがタスク実行中に不明な情報がある場合、
    このツールを使用してユーザーに質問できます。
    """
    
    name: str = "human_input"
    description: str = """【最優先ツール】ユーザーに質問して応答を待つツール。
    
    【重要】対話モードでは、不明な情報がある場合は必ずこのツールを使用してください。
    直接回答を返すことは禁止されています。
    
    必須使用ケース:
    - ファイルパスが不明な場合 → このツールで質問
    - 処理方法の選択が必要な場合 → このツールで質問
    - ユーザーの意図を確認したい場合 → このツールで質問
    - タスクの詳細が不明確な場合 → このツールで質問
    
    入力:
    - question: ユーザーに尋ねる質問（必須）
    
    出力:
    - ユーザーの応答テキスト
    
    例:
    タスク: "ファイルを読み取り、要約し、出力する"
    正しい使用: human_input(question="読み取るファイルのパスを教えてください")
    誤った対応: 直接「ファイルパスを教えてください」と返答 ← 絶対に禁止
    """
    args_schema: Type[BaseModel] = HumanInputSchema
    task_id: Optional[int] = None
    
    def _run(self, question: str) -> str:
        """
        ユーザーに質問して応答を待つ（ポーリング方式）
        
        Args:
            question: ユーザーに尋ねる質問
            
        Returns:
            str: ユーザーの応答
            
        Raises:
            ValueError: task_idが設定されていない場合
        """
        if not self.task_id:
            raise ValueError("task_id must be set before using HumanInputTool")
        
        # タスクの自動モードをチェック
        from app.models import Task
        task = Task.query.get(self.task_id)
        if task and task.auto_mode:
            # 自動モードの場合はスキップ
            skip_message = f"[自動モード] 質問「{question}」をスキップしました。エージェントが自動的に判断します。"
            
            # スキップインタラクションを記録
            skip_interaction = TaskInteraction(
                task_id=self.task_id,
                interaction_type='info',
                content=skip_message,
                extra_data={'skipped_question': question, 'reason': 'auto_mode'},
                requires_response=False,
                created_at=datetime.utcnow()
            )
            db.session.add(skip_interaction)
            db.session.commit()
            
            return skip_message
        
        # 質問を作成
        interaction = TaskInteraction(
            task_id=self.task_id,
            interaction_type='question',
            content=question,
            extra_data={},
            requires_response=True,
            created_at=datetime.utcnow()
        )
        db.session.add(interaction)
        db.session.commit()
        
        # WebSocketで通知
        from app.websocket.events import emit_task_interaction_new
        try:
            emit_task_interaction_new(self.task_id, interaction)
        except Exception as e:
            print(f"WebSocket emit error: {e}")
        
        # ユーザーの応答を待つ（ポーリング）
        import time
        print(f"Waiting for user response to question: {question}")
        
        while True:
            # キャンセルチェック
            db.session.refresh(task)
            if task.status == 'cancelled':
                print(f"Task {self.task_id} was cancelled while waiting for user input")
                raise Exception("Task was cancelled")
            
            # 応答をチェック
            db.session.refresh(interaction)
            if interaction.response:
                print(f"Received user response: {interaction.response}")
                
                # ユーザー応答インタラクションを記録
                response_interaction = TaskInteraction(
                    task_id=self.task_id,
                    interaction_type='user_response',
                    content=interaction.response,
                    extra_data={'question': question},
                    requires_response=False,
                    created_at=datetime.utcnow()
                )
                db.session.add(response_interaction)
                db.session.commit()
                
                return interaction.response
            
            # 1秒待機
            time.sleep(1)
    
    async def _arun(self, question: str) -> str:
        """非同期実行（現在は同期実行を呼び出し）"""
        return self._run(question)


def create_human_input_tool(task_id: int) -> HumanInputTool:
    """
    HumanInputToolのインスタンスを作成
    
    Args:
        task_id: タスクID
        
    Returns:
        HumanInputTool: 設定済みのツールインスタンス
    """
    tool = HumanInputTool()
    tool.task_id = task_id
    return tool
