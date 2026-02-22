from flask import Blueprint, request, jsonify
from app import db
from app.models import Agent
from app.services.agent_service import AgentService

agents_bp = Blueprint('agents', __name__)
agent_service = AgentService()


@agents_bp.route('', methods=['GET'])
def get_agents():
    """エージェント一覧を取得"""
    try:
        agents = Agent.query.all()
        return jsonify({
            'success': True,
            'data': [agent.to_dict() for agent in agents]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """特定のエージェントを取得"""
    try:
        agent = Agent.query.get_or_404(agent_id)
        return jsonify({
            'success': True,
            'data': agent.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@agents_bp.route('', methods=['POST'])
def create_agent():
    """新しいエージェントを作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        required_fields = ['name', 'llm_provider', 'llm_model']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # エージェントの作成
        agent = agent_service.create_agent(
            name=data['name'],
            role=data.get('role'),
            description=data.get('description'),
            llm_provider=data['llm_provider'],
            llm_model=data['llm_model'],
            llm_config=data.get('llm_config', {}),
            personality=data.get('personality'),
            tool_names=data.get('tool_names'),
            agent_type=data.get('agent_type', 'worker'),
            supervisor_id=data.get('supervisor_id')
        )
        
        return jsonify({
            'success': True,
            'data': agent.to_dict(),
            'message': 'Agent created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """エージェントを更新"""
    try:
        import json
        agent = Agent.query.get_or_404(agent_id)
        data = request.get_json()
        
        # tool_namesを配列からJSON文字列に変換
        if 'tool_names' in data:
            tool_names = data['tool_names']
            if tool_names is None:
                data['tool_names'] = json.dumps([])
            elif isinstance(tool_names, list):
                data['tool_names'] = json.dumps(tool_names)
            # 既にJSON文字列の場合はそのまま
        
        # 更新可能なフィールド
        updatable_fields = ['name', 'role', 'description', 'llm_provider',
                            'llm_model', 'llm_config', 'personality', 'status',
                            'tool_names', 'agent_type', 'supervisor_id']
        
        for field in updatable_fields:
            if field in data:
                setattr(agent, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': agent.to_dict(),
            'message': 'Agent updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """エージェントを削除"""
    try:
        agent = Agent.query.get_or_404(agent_id)
        
        # 実行中のタスクがある場合は削除できない
        running_tasks = agent.tasks.filter_by(status='running').count()
        if running_tasks > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete agent with running tasks'
            }), 400
        
        db.session.delete(agent)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Agent deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:agent_id>/statistics', methods=['GET'])
def get_agent_statistics(agent_id):
    """エージェントの統計情報を取得"""
    try:
        agent = Agent.query.get_or_404(agent_id)
        statistics = agent.get_statistics()
        
        return jsonify({
            'success': True,
            'data': statistics
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:agent_id>/tools', methods=['GET'])
def get_agent_tools(agent_id):
    """エージェントが使用できるツール一覧を取得"""
    try:
        agent = Agent.query.get_or_404(agent_id)
        tools = [tool.to_dict() for tool in agent.tools]
        
        return jsonify({
            'success': True,
            'data': tools
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:supervisor_id>/workers', methods=['GET'])
def get_supervisor_workers(supervisor_id):
    """Supervisorのワーカーエージェント一覧を取得"""
    try:
        workers = agent_service.get_workers(supervisor_id)
        
        return jsonify({
            'success': True,
            'data': [worker.to_dict() for worker in workers]
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:worker_id>/assign-supervisor', methods=['POST'])
def assign_supervisor(worker_id):
    """ワーカーエージェントにSupervisorを割り当て"""
    try:
        data = request.get_json()
        supervisor_id = data.get('supervisor_id')
        
        if not supervisor_id:
            return jsonify({
                'success': False,
                'error': 'supervisor_id is required'
            }), 400
        
        worker = agent_service.assign_supervisor(worker_id, supervisor_id)
        
        return jsonify({
            'success': True,
            'data': worker.to_dict(),
            'message': 'Supervisor assigned successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/<int:worker_id>/remove-supervisor', methods=['POST'])
def remove_supervisor(worker_id):
    """ワーカーエージェントからSupervisorを解除"""
    try:
        worker = agent_service.remove_supervisor(worker_id)
        
        return jsonify({
            'success': True,
            'data': worker.to_dict(),
            'message': 'Supervisor removed successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/supervisors', methods=['GET'])
def get_supervisors():
    """Supervisorエージェント一覧を取得"""
    try:
        supervisors = agent_service.list_agents(agent_type='supervisor')
        
        return jsonify({
            'success': True,
            'data': [supervisor.to_dict() for supervisor in supervisors]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_bp.route('/workers', methods=['GET'])
def get_workers():
    """Workerエージェント一覧を取得"""
    try:
        workers = agent_service.list_agents(agent_type='worker')
        
        return jsonify({
            'success': True,
            'data': [worker.to_dict() for worker in workers]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
