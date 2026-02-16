from flask_socketio import emit, join_room, leave_room
from app import socketio


@socketio.on('connect')
def handle_connect():
    """クライアント接続時"""
    print('Client connected')
    emit('connected', {'message': 'Connected to AI Agent Team Manager'})


@socketio.on('disconnect')
def handle_disconnect():
    """クライアント切断時"""
    print('Client disconnected')


@socketio.on('join_task')
def handle_join_task(data):
    """タスクルームに参加"""
    task_id = data.get('task_id')
    if task_id:
        room = f'task_{task_id}'
        join_room(room)
        emit('joined_task', {'task_id': task_id, 'room': room})


@socketio.on('leave_task')
def handle_leave_task(data):
    """タスクルームから退出"""
    task_id = data.get('task_id')
    if task_id:
        room = f'task_{task_id}'
        leave_room(room)
        emit('left_task', {'task_id': task_id, 'room': room})


@socketio.on('join_agent')
def handle_join_agent(data):
    """エージェントルームに参加"""
    agent_id = data.get('agent_id')
    if agent_id:
        room = f'agent_{agent_id}'
        join_room(room)
        emit('joined_agent', {'agent_id': agent_id, 'room': room})


@socketio.on('leave_agent')
def handle_leave_agent(data):
    """エージェントルームから退出"""
    agent_id = data.get('agent_id')
    if agent_id:
        room = f'agent_{agent_id}'
        leave_room(room)
        emit('left_agent', {'agent_id': agent_id, 'room': room})


# サーバーサイドからのイベント送信用ヘルパー関数

def emit_task_started(task_id, agent_id):
    """タスク開始イベントを送信"""
    socketio.emit('task_started', {
        'task_id': task_id,
        'agent_id': agent_id
    }, room=f'task_{task_id}')


def emit_task_progress(task_id, progress, message):
    """タスク進捗イベントを送信"""
    socketio.emit('task_progress', {
        'task_id': task_id,
        'progress': progress,
        'message': message
    }, room=f'task_{task_id}')


def emit_task_completed(task_id, result):
    """タスク完了イベントを送信"""
    socketio.emit('task_completed', {
        'task_id': task_id,
        'result': result
    }, room=f'task_{task_id}')


def emit_task_failed(task_id, error):
    """タスク失敗イベントを送信"""
    socketio.emit('task_failed', {
        'task_id': task_id,
        'error': error
    }, room=f'task_{task_id}')


def emit_agent_status_changed(agent_id, status):
    """エージェントステータス変更イベントを送信"""
    socketio.emit('agent_status_changed', {
        'agent_id': agent_id,
        'status': status
    }, room=f'agent_{agent_id}')


def emit_log_message(task_id, log):
    """ログメッセージイベントを送信"""
    socketio.emit('log_message', {
        'task_id': task_id,
        'log': log
    }, room=f'task_{task_id}')


def emit_tool_approval_request(approval_data):
    """ツール承認リクエストイベントを送信"""
    socketio.emit('tool_approval_request', approval_data, broadcast=True)


def emit_tool_approval_response(approval_id, status):
    """ツール承認レスポンスイベントを送信"""
    socketio.emit('tool_approval_response', {
        'approval_id': approval_id,
        'status': status
    }, broadcast=True)


def emit_task_interaction(task_id, interaction_data):
    """タスクインタラクションイベントを送信"""
    socketio.emit('task_interaction', {
        'task_id': task_id,
        'interaction': interaction_data
    }, room=f'task_{task_id}')


def emit_task_interaction_new(task_id, interaction):
    """新しいタスクインタラクションイベントを送信"""
    socketio.emit('task_interaction_new', {
        'task_id': task_id,
        'interaction': {
            'id': interaction.id,
            'interaction_type': interaction.interaction_type,
            'content': interaction.content,
            'metadata': interaction.metadata,
            'requires_response': interaction.requires_response,
            'created_at': interaction.created_at.isoformat() if interaction.created_at else None
        }
    }, room=f'task_{task_id}')
