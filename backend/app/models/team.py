from datetime import datetime
from app import db


class Team(db.Model):
    """チームモデル - 事前定義されたエージェントチーム"""
    
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # チーム構成
    leader_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    member_ids = db.Column(db.JSON)  # チームメンバーのエージェントIDリスト [1, 2, 3]
    
    # ステータス
    is_active = db.Column(db.Boolean, default=True)
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    leader_agent = db.relationship('Agent', foreign_keys=[leader_agent_id])
    
    def __repr__(self):
        return f'<Team {self.name}>'
    
    def to_dict(self, include_members=False):
        """辞書形式に変換"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader_agent_id': self.leader_agent_id,
            'member_ids': self.member_ids or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # リーダー情報
        if self.leader_agent:
            data['leader_agent'] = {
                'id': self.leader_agent.id,
                'name': self.leader_agent.name,
                'role': self.leader_agent.role
            }
        
        # メンバー情報（詳細が必要な場合）
        if include_members and self.member_ids:
            from app.models.agent import Agent
            members = Agent.query.filter(Agent.id.in_(self.member_ids)).all()
            data['members'] = [
                {
                    'id': member.id,
                    'name': member.name,
                    'role': member.role
                }
                for member in members
            ]
        
        return data
