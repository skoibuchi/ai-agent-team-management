"""
タスク実行中のインタラクション（対話）を記録するモデル
"""
from datetime import datetime
from app import db


class TaskInteraction(db.Model):
    """
    タスク実行中のインタラクション
    
    エージェントの思考過程、ツール実行、ユーザーへの質問などを記録
    """
    __tablename__ = 'task_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    # インタラクションの種類
    # 'agent_thinking' - エージェントの思考
    # 'tool_call' - ツール実行
    # 'tool_result' - ツール実行結果
    # 'question' - ユーザーへの質問
    # 'user_response' - ユーザーの回答
    # 'info' - 情報メッセージ
    # 'error' - エラーメッセージ
    # 'result' - 最終結果
    interaction_type = db.Column(db.String(50), nullable=False)
    
    # メッセージ内容
    content = db.Column(db.Text, nullable=False)
    
    # 追加のメタデータ（JSON形式）
    # 例: {"tool_name": "web_search", "parameters": {...}}
    # 注: metadataはSQLAlchemyの予約語のためextra_dataを使用
    extra_data = db.Column(db.JSON, nullable=True)
    
    # ユーザーの回答が必要か
    requires_response = db.Column(db.Boolean, default=False)
    
    # ユーザーの回答
    response = db.Column(db.Text, nullable=True)
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # リレーション
    task = db.relationship('Task', backref=db.backref('interactions', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'interaction_type': self.interaction_type,
            'content': self.content,
            'metadata': self.extra_data,  # APIではmetadataとして返す
            'requires_response': self.requires_response,
            'response': self.response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }
    
    def __repr__(self):
        return f'<TaskInteraction {self.id}: {self.interaction_type}>'
