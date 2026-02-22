#!/usr/bin/env python3
"""
タスククリーンアップスクリプト
問題のあるタスクを削除するためのユーティリティ
"""
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Task

def list_tasks():
    """全タスクを一覧表示"""
    app = create_app()
    with app.app_context():
        tasks = Task.query.order_by(Task.created_at.desc()).all()
        
        if not tasks:
            print("タスクがありません。")
            return
        
        print("\n=== タスク一覧 ===")
        for task in tasks:
            print(f"ID: {task.id}")
            print(f"  タイトル: {task.title}")
            print(f"  ステータス: {task.status}")
            print(f"  作成日時: {task.created_at}")
            print(f"  更新日時: {task.updated_at}")
            print()

def delete_task(task_id):
    """指定したタスクを削除"""
    app = create_app()
    with app.app_context():
        task = Task.query.get(task_id)
        
        if not task:
            print(f"タスクID {task_id} が見つかりません。")
            return False
        
        print(f"タスクを削除します:")
        print(f"  ID: {task.id}")
        print(f"  タイトル: {task.title}")
        print(f"  ステータス: {task.status}")
        
        confirm = input("\n本当に削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("キャンセルしました。")
            return False
        
        db.session.delete(task)
        db.session.commit()
        print(f"タスクID {task_id} を削除しました。")
        return True

def delete_all_tasks():
    """全タスクを削除"""
    app = create_app()
    with app.app_context():
        tasks = Task.query.all()
        
        if not tasks:
            print("タスクがありません。")
            return
        
        print(f"\n{len(tasks)}個のタスクを削除します。")
        confirm = input("本当に全て削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("キャンセルしました。")
            return
        
        for task in tasks:
            db.session.delete(task)
        
        db.session.commit()
        print(f"{len(tasks)}個のタスクを削除しました。")

def delete_running_tasks():
    """実行中のタスクを全て削除"""
    app = create_app()
    with app.app_context():
        tasks = Task.query.filter_by(status='running').all()
        
        if not tasks:
            print("実行中のタスクがありません。")
            return
        
        print(f"\n{len(tasks)}個の実行中タスクを削除します:")
        for task in tasks:
            print(f"  - ID: {task.id}, タイトル: {task.title}")
        
        confirm = input("\n本当に削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("キャンセルしました。")
            return
        
        for task in tasks:
            db.session.delete(task)
        
        db.session.commit()
        print(f"{len(tasks)}個のタスクを削除しました。")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python cleanup_tasks.py list              - タスク一覧を表示")
        print("  python cleanup_tasks.py delete <task_id>  - 指定したタスクを削除")
        print("  python cleanup_tasks.py delete-all        - 全タスクを削除")
        print("  python cleanup_tasks.py delete-running    - 実行中のタスクを削除")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        list_tasks()
    elif command == 'delete' and len(sys.argv) == 3:
        task_id = int(sys.argv[2])
        delete_task(task_id)
    elif command == 'delete-all':
        delete_all_tasks()
    elif command == 'delete-running':
        delete_running_tasks()
    else:
        print("無効なコマンドです。")
        sys.exit(1)

if __name__ == '__main__':
    main()

