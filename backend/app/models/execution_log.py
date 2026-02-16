from datetime import datetime
from app import db


class ExecutionLog(db.Model):
    """実行ログモデル"""
    
    __tablename__ = 'execution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 関連
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'))
    
    # アクション
    action = db.Column(db.String(100), nullable=False)
    
    # データ
    input_data = db.Column(db.JSON)
    output_data = db.Column(db.JSON)
    
    # ステータス
    status = db.Column(db.String(20), nullable=False)  # started, success, failed
    error_message = db.Column(db.Text)
    
    # パフォーマンス
    execution_time = db.Column(db.Float)  # 秒
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    task = db.relationship('Task', back_populates='execution_logs')
    agent = db.relationship('Agent', back_populates='execution_logs')
    tool = db.relationship('Tool', back_populates='execution_logs')
    
    def __repr__(self):
        return f'<ExecutionLog {self.id} - {self.action}>'
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'tool_id': self.tool_id,
            'action': self.action,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'status': self.status,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'agent_name': self.agent.name if self.agent else None,
            'tool_name': self.tool.name if self.tool else None
        }
