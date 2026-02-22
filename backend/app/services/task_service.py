from datetime import datetime
from app import db
from app.models import Task, Agent


class TaskService:
    """タスク管理サービス"""
    
    def create_task(self, title, description, priority='medium',
                     assigned_to=None, mode='single', deadline=None,
                     additional_tool_names=None, team_member_ids=None,
                     leader_agent_id=None):
        """タスクを作成"""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            mode=mode,
            deadline=deadline,
            additional_tool_names=additional_tool_names or [],
            team_member_ids=team_member_ids or [],
            leader_agent_id=leader_agent_id,
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        return task
    
    def get_task(self, task_id):
        """タスクを取得"""
        return Task.query.get(task_id)
    
    def update_task(self, task_id, **kwargs):
        """タスクを更新"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        db.session.commit()
        return task
    
    def delete_task(self, task_id):
        """タスクを削除"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        # 実行中のタスクは削除できない
        if task.status == 'running':
            raise ValueError('Cannot delete running task')
        
        db.session.delete(task)
        db.session.commit()
    
    def list_tasks(self, status=None, agent_id=None):
        """タスク一覧を取得"""
        query = Task.query
        
        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(assigned_to=agent_id)
        
        # 親タスクのみ
        query = query.filter_by(parent_task_id=None)
        
        return query.order_by(Task.created_at.desc()).all()
    
    def assign_task(self, task_id, agent_id):
        """タスクをエージェントに割り当て"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        
        task.assigned_to = agent_id
        db.session.commit()
        
        return task
    
    def update_task_status(self, task_id, status, error_message=None):
        """タスクのステータスを更新"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        task.status = status
        
        if status == 'running' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ['completed', 'failed']:
            task.completed_at = datetime.utcnow()
            if error_message:
                task.error_message = error_message
        
        db.session.commit()
        return task
    
    def decompose_task(self, task_id):
        """タスクを分解（サブタスクを作成）"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        # TODO: LLMを使ってタスクを分析し、サブタスクを生成
        # 現在は簡易実装
        subtasks = []
        
        # 例: タスクを3つのサブタスクに分解
        subtask_descriptions = [
            f"Step 1: Analyze requirements for '{task.title}'",
            f"Step 2: Execute main task for '{task.title}'",
            f"Step 3: Verify results for '{task.title}'"
        ]
        
        for i, desc in enumerate(subtask_descriptions, 1):
            subtask = Task(
                title=f"{task.title} - Step {i}",
                description=desc,
                priority=task.priority,
                parent_task_id=task.id,
                mode=task.mode,
                status='pending'
            )
            db.session.add(subtask)
            subtasks.append(subtask)
        
        db.session.commit()
        return subtasks
    
    def get_task_logs(self, task_id):
        """タスクの実行ログを取得"""
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f'Task {task_id} not found')
        
        return task.execution_logs.order_by('created_at').all()
