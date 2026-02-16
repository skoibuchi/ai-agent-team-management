"""
Tool Approval API
ツール承認リクエストのAPIエンドポイント
"""
from flask import Blueprint, request, jsonify
from app.services.approval_service import ApprovalService
from app.models.tool_approval import ToolApprovalRequest


approvals_bp = Blueprint('approvals', __name__)
approval_service = ApprovalService()


@approvals_bp.route('/', methods=['GET'])
def get_approvals():
    """承認リクエスト一覧を取得"""
    try:
        agent_id = request.args.get('agent_id', type=int)
        status = request.args.get('status', 'pending')
        
        if status == 'all':
            query = ToolApprovalRequest.query
        else:
            query = ToolApprovalRequest.query.filter_by(status=status)
        
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        
        approvals = query.order_by(ToolApprovalRequest.requested_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [approval.to_dict() for approval in approvals]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@approvals_bp.route('/<int:approval_id>', methods=['GET'])
def get_approval(approval_id):
    """特定の承認リクエストを取得"""
    try:
        approval_data = approval_service.get_request(approval_id)
        
        if not approval_data:
            return jsonify({
                'success': False,
                'error': 'Approval request not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': approval_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@approvals_bp.route('/', methods=['POST'])
def create_approval_request():
    """承認リクエストを作成"""
    try:
        data = request.get_json()
        
        agent_id = data.get('agent_id')
        task_id = data.get('task_id')
        tools = data.get('tools', [])
        reason = data.get('reason', '')
        
        if not agent_id or not tools:
            return jsonify({
                'success': False,
                'error': 'agent_id and tools are required'
            }), 400
        
        approval_id = approval_service.request_tool_approval(
            agent_id=agent_id,
            task_id=task_id,
            tools=tools,
            reason=reason
        )
        
        return jsonify({
            'success': True,
            'data': {
                'approval_id': approval_id
            }
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@approvals_bp.route('/<int:approval_id>/approve', methods=['POST'])
def approve_request(approval_id):
    """承認リクエストを承認"""
    try:
        data = request.get_json() or {}
        note = data.get('note')
        
        success = approval_service.approve_request(approval_id, note)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to approve request'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Approval request approved'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@approvals_bp.route('/<int:approval_id>/reject', methods=['POST'])
def reject_request(approval_id):
    """承認リクエストを拒否"""
    try:
        data = request.get_json() or {}
        note = data.get('note')
        
        success = approval_service.reject_request(approval_id, note)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to reject request'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Approval request rejected'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@approvals_bp.route('/pending', methods=['GET'])
def get_pending_requests():
    """保留中の承認リクエストを取得"""
    try:
        agent_id = request.args.get('agent_id', type=int)
        requests = approval_service.get_pending_requests(agent_id)
        
        return jsonify({
            'success': True,
            'data': requests
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
