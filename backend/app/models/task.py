from datetime import datetime
import json
from app import db


class Task(db.Model):
    """タスクモデル"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # 優先度と期限
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    deadline = db.Column(db.DateTime)
    
    # ステータス
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed, cancelled
    
    # 割り当て
    assigned_to = db.Column(db.Integer, db.ForeignKey('agents.id'))
    
    # 親タスク（サブタスクの場合）
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    
    # 実行モード
    mode = db.Column(db.String(20), default='single')  # single, auto, team
    
    # 自動実行モード（実行中に切り替え可能）
    auto_mode = db.Column(db.Boolean, default=False)  # False=対話モード, True=自動モード
    
    # ツール設定
    additional_tool_names = db.Column(db.JSON)  # タスク固有の追加ツール名のリスト ['file_reader', 'data_analyzer']
    
    # 動的チーム編成（Dynamic Team Pattern用）
    team_member_ids = db.Column(db.JSON)  # チームメンバーのエージェントIDリスト [1, 2, 3]
    leader_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))  # チームリーダーのエージェントID
    
    # 結果
    result = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    @property
    def additional_tool_names_list(self):
        """additional_tool_namesをリストとして取得"""
        if not self.additional_tool_names:
            return []
        if isinstance(self.additional_tool_names, list):
            return self.additional_tool_names
        try:
            return json.loads(self.additional_tool_names) if isinstance(self.additional_tool_names, str) else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def team_member_ids_list(self):
        """team_member_idsをリストとして取得"""
        if not self.team_member_ids:
            return []
        if isinstance(self.team_member_ids, list):
            return self.team_member_ids
        try:
            return json.loads(self.team_member_ids) if isinstance(self.team_member_ids, str) else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    # リレーションシップ
    agent = db.relationship('Agent', foreign_keys=[assigned_to], back_populates='tasks')
    leader_agent = db.relationship('Agent', foreign_keys=[leader_agent_id])
    parent_task = db.relationship('Task', remote_side=[id], backref=db.backref('subtasks', cascade='all, delete-orphan'))
    execution_logs = db.relationship('ExecutionLog', back_populates='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self, include_subtasks=False):
        """辞書形式に変換"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'detailed_status': self.get_detailed_status(),  # 詳細ステータスを追加
            'assigned_to': self.assigned_to,
            'parent_task_id': self.parent_task_id,
            'mode': self.mode,
            'auto_mode': self.auto_mode,
            'additional_tool_names': self.additional_tool_names or [],
            'team_member_ids': self.team_member_ids or [],
            'leader_agent_id': self.leader_agent_id,
            'result': self.result,
            'error_message': self.error_message,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
        
        # エージェント情報
        if self.agent:
            data['agent'] = {
                'id': self.agent.id,
                'name': self.agent.name,
                'role': self.agent.role
            }
        
        # サブタスク情報
        if include_subtasks and self.subtasks:
            data['subtasks'] = [subtask.to_dict() for subtask in self.subtasks]
        
        return data
    
    def get_duration(self):
        """実行時間を取得（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_progress(self):
        """進捗率を取得（サブタスクがある場合）"""
        if not self.subtasks:
            return 100 if self.status == 'completed' else 0
        
        total = len(self.subtasks)
        completed = sum(1 for subtask in self.subtasks if subtask.status == 'completed')
        
        return int((completed / total) * 100) if total > 0 else 0
    
    def get_detailed_status(self):
        """
        詳細なステータスを取得
        
        Returns:
            str: 詳細ステータス
                - 'pending': 待機中
                - 'running': 実行中
                - 'waiting_input': ユーザー入力待ち
                - 'waiting_approval': ツール承認待ち
                - 'completed': 完了
                - 'failed': 失敗
        """
        # 基本ステータスがpending, completed, failed, cancelledの場合はそのまま返す
        if self.status in ['pending', 'completed', 'failed', 'cancelled']:
            return self.status
        
        # waiting_for_input状態の場合はそのまま返す
        if self.status == 'waiting_for_input':
            return 'waiting_input'
        
        # runningの場合、インタラクションの状態を確認
        if self.status == 'running':
            # 最新の未回答の質問があるか確認
            pending_question = self.interactions.filter_by(
                interaction_type='question',
                requires_response=True,
                response=None
            ).order_by(db.desc('created_at')).first()
            
            if pending_question:
                return 'waiting_input'
            
            # ツール承認待ちがあるか確認（execution_logsから）
            from app.models.execution_log import ExecutionLog
            pending_approval = ExecutionLog.query.filter_by(
                task_id=self.id,
                status='pending_approval'
            ).first()
            
            if pending_approval:
                return 'waiting_approval'
            
            # それ以外は実行中
            return 'running'
        
        return self.status
