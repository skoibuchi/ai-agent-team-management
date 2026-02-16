from app import db
from app.models import Agent


class AgentService:
    """エージェント管理サービス"""
    
    def create_agent(self, name, llm_provider, llm_model, role=None,
                      description=None, llm_config=None, personality=None,
                      tool_names=None):
        """エージェントを作成"""
        agent = Agent(
            name=name,
            role=role,
            description=description,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_config=llm_config or {},
            personality=personality,
            tool_names=tool_names or [],
            status='idle'
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
    
    def list_agents(self, status=None):
        """エージェント一覧を取得"""
        query = Agent.query
        
        if status:
            query = query.filter_by(status=status)
        
        return query.all()
    
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
