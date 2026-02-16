from flask import Blueprint, request, jsonify
from app import db
from app.models import Task, Agent
from app.services.task_service import TaskService

tasks_bp = Blueprint('tasks', __name__)
task_service = TaskService()


@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """タスク一覧を取得"""
    try:
        # クエリパラメータでフィルタリング
        status = request.args.get('status')
        agent_id = request.args.get('agent_id', type=int)
        updated_since = request.args.get('updated_since')  # ISO 8601形式のタイムスタンプ
        
        query = Task.query
        
        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(assigned_to=agent_id)
        
        # 指定時刻以降に更新されたタスクのみ取得（差分更新用）
        if updated_since:
            from datetime import datetime
            try:
                since_dt = datetime.fromisoformat(updated_since.replace('Z', '+00:00'))
                query = query.filter(Task.updated_at > since_dt)
            except ValueError:
                pass  # 無効な日時形式の場合は無視
        
        # 親タスクのみ取得（サブタスクは除外）
        query = query.filter_by(parent_task_id=None)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [task.to_dict(include_subtasks=True) for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """特定のタスクを取得"""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify({
            'success': True,
            'data': task.to_dict(include_subtasks=True)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@tasks_bp.route('', methods=['POST'])
def create_task():
    """新しいタスクを作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドのチェック
        if 'description' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: description'
            }), 400
        
        # タスクの作成
        task = task_service.create_task(
            title=data.get('title', data['description'][:50]),
            description=data['description'],
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to'),
            mode=data.get('mode', 'manual'),
            deadline=data.get('deadline'),
            additional_tool_names=data.get('additional_tool_names')
        )
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Task created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """タスクを更新"""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        # 更新可能なフィールド
        updatable_fields = ['title', 'description', 'priority', 'status',
                            'assigned_to', 'deadline', 'result',
                            'error_message', 'additional_tool_names']
        
        for field in updatable_fields:
            if field in data:
                setattr(task, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Task updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """タスクを削除"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # 実行中のタスクは削除できない
        # pending, completed, failed, cancelled は削除可能
        if task.status == 'running':
            return jsonify({
                'success': False,
                'error': 'Cannot delete running task. Please cancel it first.'
            }), 400
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<int:task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """タスクを実行"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # デバッグログ
        print(f"Task {task_id} details:")
        print(f"  - Status: {task.status}")
        print(f"  - Assigned to: {task.assigned_to}")
        print(f"  - Title: {task.title}")
        
        # タスクの状態チェック
        if task.status == 'running':
            error_msg = 'Task is already running'
            print(f"Error: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # エージェントが未割り当ての場合、最初のエージェントを自動割り当て
        if not task.assigned_to:
            first_agent = Agent.query.first()
            if not first_agent:
                error_msg = 'No agents available. Please create an agent first.'
                print(f"Error: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            task.assigned_to = first_agent.id
            db.session.commit()
            print(f"Auto-assigned task to agent: {first_agent.name} (ID: {first_agent.id})")
        
        # タスク実行（非同期）
        from app.services.execution_service import ExecutionService
        execution_service = ExecutionService()
        execution_service.execute_task_async(task.id)
        
        return jsonify({
            'success': True,
            'message': 'Task execution started',
            'data': task.to_dict()
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@tasks_bp.route('/<int:task_id>/toggle-auto-mode', methods=['POST'])
def toggle_auto_mode(task_id):
    """タスクの自動/対話モードを切り替え"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # auto_modeを切り替え
        task.auto_mode = not task.auto_mode
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': f'Auto mode {"enabled" if task.auto_mode else "disabled"}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tasks_bp.route('/<int:task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """タスクをキャンセル"""
    try:
        task = Task.query.get_or_404(task_id)
        
        if task.status != 'running':
            return jsonify({
                'success': False,
                'error': 'Task is not running'
            }), 400
        
        task.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Task cancelled successfully'
        }), 200
        
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"Task execution error: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500


@tasks_bp.route('/<int:task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """タスクの実行ログを取得"""
    try:
        task = Task.query.get_or_404(task_id)
        logs = task.execution_logs.order_by('created_at').all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
