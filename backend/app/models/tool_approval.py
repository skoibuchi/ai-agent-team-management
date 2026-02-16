"""
Tool Approval Request Model
ツール追加承認リクエストのデータモデル
"""
from datetime import datetime
from app import db


class ToolApprovalRequest(db.Model):
    """ツール追加承認リクエスト"""
    __tablename__ = 'tool_approval_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    requested_tools = db.Column(db.JSON, nullable=False)  # List[str]
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, timeout
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    response_note = db.Column(db.Text, nullable=True)
    
    # Relationships
    agent = db.relationship('Agent', backref='tool_approval_requests')
    task = db.relationship('Task', backref='tool_approval_requests')
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_name': self.agent.name if self.agent else None,
            'task_id': self.task_id,
            'task_title': self.task.title if self.task else None,
            'requested_tools': self.requested_tools,
            'reason': self.reason,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'response_note': self.response_note,
        }


class ToolUsage(db.Model):
    """ツール使用統計"""
    __tablename__ = 'tool_usages'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    tool_name = db.Column(db.String(100), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    execution_time = db.Column(db.Float, nullable=True)  # seconds
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Relationships
    agent = db.relationship('Agent', backref='tool_usages')
    task = db.relationship('Task', backref='tool_usages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'task_id': self.task_id,
            'tool_name': self.tool_name,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
        }
