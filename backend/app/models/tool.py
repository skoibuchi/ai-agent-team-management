from datetime import datetime
from app import db


class Tool(db.Model):
    """ツールモデル"""
    
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)  # file_system, web, api, code, custom
    description = db.Column(db.Text)
    
    # ツールタイプ
    type = db.Column(db.String(20), nullable=False)  # builtin, api, script, cli
    
    # 設定
    config = db.Column(db.JSON)  # API endpoint, parameters, etc.
    
    # ステータス
    is_builtin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    agents = db.relationship('Agent', secondary='agent_tools', back_populates='tools')
    execution_logs = db.relationship('ExecutionLog', back_populates='tool', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tool {self.name}>'
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'type': self.type,
            'config': self.config,
            'is_builtin': self.is_builtin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_count': self.get_usage_count()
        }
    
    def get_usage_count(self):
        """使用回数を取得"""
        return self.execution_logs.count()
    
    def get_schema(self):
        """ツールのスキーマを取得（LLMに渡す用）"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.config.get('parameters', {}) if self.config else {}
        }
