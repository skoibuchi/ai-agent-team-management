"""
タスクインタラクションAPI
タスク実行中のインタラクション（対話）を管理
"""
from flask import Blueprint, jsonify, request
from app import db
from app.models import Task, TaskInteraction
from datetime import datetime

bp = Blueprint('task_interactions', __name__, url_prefix='/api/tasks')


@bp.route('/<int:task_id>/interactions', methods=['GET'])
def get_task_interactions(task_id):
    """
    タスクのインタラクション履歴を取得
    
    Args:
        task_id: タスクID
        
    Query Parameters:
        type: インタラクションタイプでフィルタ
        limit: 取得件数の上限
        since: 指定したID以降のインタラクションのみ取得（差分取得用）
        
    Returns:
        JSON: インタラクション履歴
    """
    task = Task.query.get_or_404(task_id)
    
    # クエリパラメータ
    interaction_type = request.args.get('type')
    limit = request.args.get('limit', type=int)
    since_id = request.args.get('since', type=int)
    
    # インタラクションを取得
    query = TaskInteraction.query.filter_by(task_id=task_id)
    
    # 差分取得: 指定したID以降のみ
    if since_id:
        query = query.filter(TaskInteraction.id > since_id)
    
    if interaction_type:
        query = query.filter_by(interaction_type=interaction_type)
    
    query = query.order_by(TaskInteraction.created_at.asc())
    
    if limit:
        query = query.limit(limit)
    
    interactions = query.all()
    
    return jsonify({
        'task_id': task_id,
        'interactions': [
            {
                'id': interaction.id,
                'interaction_type': interaction.interaction_type,
                'content': interaction.content,
                'metadata': interaction.metadata if isinstance(interaction.metadata, dict) else {},
                'requires_response': interaction.requires_response,
                'response': interaction.response,
                'created_at': interaction.created_at.isoformat() if interaction.created_at else None,
                'responded_at': interaction.responded_at.isoformat() if interaction.responded_at else None
            }
            for interaction in interactions
        ]
    })


@bp.route('/<int:task_id>/interactions/<int:interaction_id>/respond', methods=['POST'])
def respond_to_interaction(task_id, interaction_id):
    """
    インタラクションに応答
    
    Args:
        task_id: タスクID
        interaction_id: インタラクションID
        
    Returns:
        JSON: 更新されたインタラクション
    """
    task = Task.query.get_or_404(task_id)
    interaction = TaskInteraction.query.filter_by(
        id=interaction_id,
        task_id=task_id
    ).first_or_404()
    
    if not interaction.requires_response:
        return jsonify({'error': 'This interaction does not require a response'}), 400
    
    if interaction.response:
        return jsonify({'error': 'This interaction has already been responded to'}), 400
    
    data = request.get_json()
    response_text = data.get('response')
    
    if not response_text:
        return jsonify({'error': 'Response text is required'}), 400
    
    # 応答を記録
    interaction.response = response_text
    interaction.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': interaction.id,
        'interaction_type': interaction.interaction_type,
        'content': interaction.content,
        'metadata': interaction.metadata if isinstance(interaction.metadata, dict) else {},
        'requires_response': interaction.requires_response,
        'response': interaction.response,
        'created_at': interaction.created_at.isoformat() if interaction.created_at else None,
        'responded_at': interaction.responded_at.isoformat() if interaction.responded_at else None
    })


@bp.route('/<int:task_id>/interactions/pending', methods=['GET'])
def get_pending_interactions(task_id):
    """
    応答待ちのインタラクションを取得
    
    Args:
        task_id: タスクID
        
    Returns:
        JSON: 応答待ちインタラクション
    """
    task = Task.query.get_or_404(task_id)
    
    interactions = TaskInteraction.query.filter_by(
        task_id=task_id,
        requires_response=True,
        response=None
    ).order_by(TaskInteraction.created_at.asc()).all()
    
    return jsonify({
        'task_id': task_id,
        'pending_interactions': [
            {
                'id': interaction.id,
                'interaction_type': interaction.interaction_type,
                'content': interaction.content,
                'metadata': interaction.metadata if isinstance(interaction.metadata, dict) else {},
                'created_at': interaction.created_at.isoformat() if interaction.created_at else None
            }
            for interaction in interactions
        ]
    })


@bp.route('/<int:task_id>/interactions/send-message', methods=['POST'])
def send_user_message(task_id):
    """
    ユーザーからのメッセージを送信（AIへの自由な発言）
    
    完了/失敗したタスクの場合、自動的にタスクを再開します。
    再開時は、ユーザーのメッセージを新しいタスクとして実行し、
    会話履歴（前回の結果）を引き継ぎます。
    
    Args:
        task_id: タスクID
        
    Request Body:
        {
            "message": "ユーザーのメッセージ"
        }
        
    Returns:
        JSON: 作成されたインタラクション
    """
    task = Task.query.get_or_404(task_id)
    
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # ユーザーメッセージをインタラクションとして記録
    interaction = TaskInteraction(
        task_id=task_id,
        interaction_type='user_message',
        content=message,
        requires_response=False,  # 自由なメッセージなので応答は必須ではない
        created_at=datetime.utcnow()
    )
    db.session.add(interaction)
    
    # タスクが完了/失敗している場合、自動的に再開
    if task.status in ['completed', 'failed']:
        print(f"Task {task_id} is {task.status}. Resuming task with user message...")
        
        # 元のタスクの説明を保存（参照用）
        original_description = task.description
        
        # タスクの説明を更新（ユーザーのメッセージを新しいタスクとして実行）
        # 前回の結果を参照するように指示を追加
        task.description = f"""前回のタスク結果を参照して、以下の追加指示に従ってください：

【追加指示】
{message}

【注意】
- 前回の会話履歴と結果を参照してください
- 元のタスク: {original_description}
- 新しいタスクを最初から実行するのではなく、前回の結果を基に追加指示に応答してください"""
        
        task.status = 'running'
        task.detailed_status = 'user_interaction'
        
        # タスクを非同期で再実行
        from app.services.execution_service import ExecutionService
        execution_service = ExecutionService()
        
        # コミット後に非同期実行
        db.session.commit()
        execution_service.execute_task_async(task_id)
    else:
        db.session.commit()
    
    return jsonify({
        'id': interaction.id,
        'interaction_type': interaction.interaction_type,
        'content': interaction.content,
        'metadata': interaction.extra_data,
        'requires_response': interaction.requires_response,
        'response': interaction.response,
        'created_at': interaction.created_at.isoformat() if interaction.created_at else None,
        'responded_at': interaction.responded_at.isoformat() if interaction.responded_at else None
    }), 201
