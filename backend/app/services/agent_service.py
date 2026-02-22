from app import db
from app.models import Agent


class AgentService:
    """エージェント管理サービス"""
    
    def create_agent(self, name, llm_provider, llm_model, role=None,
                     description=None, llm_config=None, personality=None,
                     tool_names=None, agent_type='worker', supervisor_id=None):
        """エージェントを作成"""
        import json
        
        # tool_namesをJSON文字列に変換
        if tool_names is None:
            tool_names_str = json.dumps([])
        elif isinstance(tool_names, list):
            tool_names_str = json.dumps(tool_names)
        else:
            tool_names_str = tool_names
        
        agent = Agent(
            name=name,
            role=role,
            description=description,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_config=llm_config or {},
            personality=personality,
            tool_names=tool_names_str,
            status='idle',
            agent_type=agent_type,
            supervisor_id=supervisor_id
        )
        
        db.session.add(agent)
        db.session.commit()
        
        return agent
    
    def get_agent(self, agent_id):
        """エージェントを取得"""
        return Agent.query.get(agent_id)
    
    def update_agent(self, agent_id, **kwargs):
        """エージェントを更新"""
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        
        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        db.session.commit()
        return agent
    
    def delete_agent(self, agent_id):
        """エージェントを削除"""
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        
        # 実行中のタスクがある場合は削除できない
        running_tasks = agent.tasks.filter_by(status='running').count()
        if running_tasks > 0:
            raise ValueError('Cannot delete agent with running tasks')
        
        db.session.delete(agent)
        db.session.commit()
    
    def list_agents(self, status=None, agent_type=None, supervisor_id=None):
        """エージェント一覧を取得"""
        query = Agent.query
        
        if status:
            query = query.filter_by(status=status)
        
        if agent_type:
            query = query.filter_by(agent_type=agent_type)
        
        if supervisor_id is not None:
            query = query.filter_by(supervisor_id=supervisor_id)
        
        return query.all()
    
    def get_workers(self, supervisor_id):
        """Supervisorのワーカーエージェント一覧を取得"""
        supervisor = Agent.query.get(supervisor_id)
        if not supervisor:
            raise ValueError(f'Agent {supervisor_id} not found')
        
        if supervisor.agent_type != 'supervisor':
            raise ValueError(f'Agent {supervisor_id} is not a supervisor')
        
        return supervisor.workers
    
    def assign_supervisor(self, worker_id, supervisor_id):
        """ワーカーエージェントにSupervisorを割り当て"""
        worker = Agent.query.get(worker_id)
        if not worker:
            raise ValueError(f'Worker agent {worker_id} not found')
        
        supervisor = Agent.query.get(supervisor_id)
        if not supervisor:
            raise ValueError(f'Supervisor agent {supervisor_id} not found')
        
        if supervisor.agent_type != 'supervisor':
            raise ValueError(f'Agent {supervisor_id} is not a supervisor')
        
        worker.supervisor_id = supervisor_id
        db.session.commit()
        
        return worker
    
    def remove_supervisor(self, worker_id):
        """ワーカーエージェントからSupervisorを解除"""
        worker = Agent.query.get(worker_id)
        if not worker:
            raise ValueError(f'Worker agent {worker_id} not found')
        
        worker.supervisor_id = None
        db.session.commit()
        
        return worker
    
    def get_agent_status(self, agent_id):
        """エージェントのステータスを取得"""
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        
        return {
            'id': agent.id,
            'name': agent.name,
            'status': agent.status,
            'current_task': None,  # TODO: 実装
            'statistics': agent.get_statistics()
        }
    
    def update_agent_status(self, agent_id, status):
        """エージェントのステータスを更新"""
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        
        agent.status = status
        db.session.commit()
        
        return agent
