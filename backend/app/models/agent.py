from datetime import datetime
import json
from app import db


class Agent(db.Model):
    """AIエージェントモデル"""
    
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # LLM設定
    llm_provider = db.Column(db.String(50), nullable=False)  # openai, anthropic, watsonx, ollama
    llm_model = db.Column(db.String(100), nullable=False)
    llm_config = db.Column(db.JSON)  # temperature, max_tokens, etc.
    
    # パーソナリティ設定
    personality = db.Column(db.JSON)
    
    # ツール設定
    tool_names = db.Column(db.Text)  # エージェントが使用できるツール名のリスト（JSON文字列）
    
    # ステータス
    status = db.Column(db.String(20), default='idle')  # idle, running, error
    
    # Supervisor Pattern用フィールド
    agent_type = db.Column(db.String(20), nullable=False, default='worker')  # supervisor, worker
    supervisor_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)  # 所属するSupervisor
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    tasks = db.relationship('Task', foreign_keys='Task.assigned_to', back_populates='agent', lazy='dynamic')
    execution_logs = db.relationship('ExecutionLog', back_populates='agent', lazy='dynamic')
    tools = db.relationship('Tool', secondary='agent_tools', back_populates='agents')
    
    # Supervisor Pattern用リレーションシップ
    supervisor = db.relationship('Agent', remote_side=[id], backref='workers', foreign_keys=[supervisor_id])
    
    @property
    def tool_names_list(self):
        """tool_namesをリストとして取得"""
        if not self.tool_names:
            return []
        if isinstance(self.tool_names, list):
            return self.tool_names
        try:
            return json.loads(self.tool_names) if self.tool_names else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def __repr__(self):
        return f'<Agent {self.name}>'
    
    def to_dict(self):
        """辞書形式に変換"""
        data = {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'description': self.description,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'llm_config': self.llm_config,
            'personality': self.personality,
            'tool_names': self.tool_names_list,
            'agent_type': self.agent_type,
            'supervisor_id': self.supervisor_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tasks_count': self.tasks.count(),
            'tools_count': len(self.tool_names_list)
        }
        
        # Supervisorの場合、ワーカー数を追加
        if self.agent_type == 'supervisor':
            data['workers_count'] = len(self.workers)
        
        # Workerの場合、Supervisor情報を追加
        if self.supervisor:
            data['supervisor'] = {
                'id': self.supervisor.id,
                'name': self.supervisor.name
            }
        
        return data
    
    def get_statistics(self):
        """統計情報を取得"""
        total_tasks = self.tasks.count()
        completed_tasks = self.tasks.filter_by(status='completed').count()
        failed_tasks = self.tasks.filter_by(status='failed').count()
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': round(success_rate, 2)
        }


# エージェントとツールの多対多関係テーブル
agent_tools = db.Table('agent_tools',
    db.Column('agent_id', db.Integer, db.ForeignKey('agents.id'), primary_key=True),
    db.Column('tool_id', db.Integer, db.ForeignKey('tools.id'), primary_key=True),
    db.Column('usage_count', db.Integer, default=0),
    db.Column('last_used', db.DateTime)
)
