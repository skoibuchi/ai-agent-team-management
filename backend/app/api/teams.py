from flask import Blueprint, request, jsonify
from app import db
from app.models import Team, Agent

teams_bp = Blueprint('teams', __name__)


@teams_bp.route('', methods=['GET'])
def get_teams():
    """チーム一覧を取得"""
    try:
        # クエリパラメータでフィルタリング
        is_active = request.args.get('is_active')
        
        query = Team.query
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        teams = query.order_by(Team.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [team.to_dict(include_members=True) for team in teams]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teams_bp.route('/<int:team_id>', methods=['GET'])
def get_team(team_id):
    """特定のチームを取得"""
    try:
        team = Team.query.get_or_404(team_id)
        return jsonify({
            'success': True,
            'data': team.to_dict(include_members=True)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@teams_bp.route('', methods=['POST'])
def create_team():
    """新しいチームを作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        if 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: name'
            }), 400
        
        if 'leader_agent_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: leader_agent_id'
            }), 400
        
        # リーダーエージェントの存在確認
        leader = Agent.query.get(data['leader_agent_id'])
        if not leader:
            return jsonify({
                'success': False,
                'error': f'Leader agent {data["leader_agent_id"]} not found'
            }), 404
        
        # メンバーエージェントの存在確認
        member_ids = data.get('member_ids', [])
        if member_ids:
            members = Agent.query.filter(Agent.id.in_(member_ids)).all()
            if len(members) != len(member_ids):
                return jsonify({
                    'success': False,
                    'error': 'One or more member agents not found'
                }), 404
        
        # チームの作成
        team = Team(
            name=data['name'],
            description=data.get('description'),
            leader_agent_id=data['leader_agent_id'],
            member_ids=member_ids,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(team)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': team.to_dict(include_members=True),
            'message': 'Team created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teams_bp.route('/<int:team_id>', methods=['PUT'])
def update_team(team_id):
    """チームを更新"""
    try:
        team = Team.query.get_or_404(team_id)
        data = request.get_json()
        
        # 更新可能なフィールド
        if 'name' in data:
            team.name = data['name']
        
        if 'description' in data:
            team.description = data['description']
        
        if 'leader_agent_id' in data:
            # リーダーエージェントの存在確認
            leader = Agent.query.get(data['leader_agent_id'])
            if not leader:
                return jsonify({
                    'success': False,
                    'error': f'Leader agent {data["leader_agent_id"]} not found'
                }), 404
            team.leader_agent_id = data['leader_agent_id']
        
        if 'member_ids' in data:
            # メンバーエージェントの存在確認
            member_ids = data['member_ids']
            if member_ids:
                members = Agent.query.filter(Agent.id.in_(member_ids)).all()
                if len(members) != len(member_ids):
                    return jsonify({
                        'success': False,
                        'error': 'One or more member agents not found'
                    }), 404
            team.member_ids = member_ids
        
        if 'is_active' in data:
            team.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': team.to_dict(include_members=True),
            'message': 'Team updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@teams_bp.route('/<int:team_id>', methods=['DELETE'])
def delete_team(team_id):
    """チームを削除"""
    try:
        team = Team.query.get_or_404(team_id)
        
        db.session.delete(team)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Team deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
