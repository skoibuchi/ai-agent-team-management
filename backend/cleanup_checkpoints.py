#!/usr/bin/env python3
"""
チェックポイントデータベースのクリーンアップスクリプト

古いスキーマのチェックポイントデータを削除して、
新しいスキーマで再作成できるようにします。
"""
import os
import sys

def cleanup_checkpoints():
    """チェックポイントデータベースファイルを削除"""
    # データディレクトリのパス
    data_dir = os.path.join(os.path.dirname(__file__), "app", "data")
    
    # チェックポイントデータベースファイル
    checkpoint_files = [
        "agent_memory.db",
        "agent_memory.db-shm",
        "agent_memory.db-wal"
    ]
    
    deleted_count = 0
    for filename in checkpoint_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"✓ Deleted: {filepath}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {filepath}: {e}", file=sys.stderr)
        else:
            print(f"- Not found: {filepath}")
    
    if deleted_count > 0:
        print(f"\n✓ Cleanup complete! Deleted {deleted_count} file(s).")
        print("チェックポイントデータベースが削除されました。")
        print("バックエンドを再起動すると、新しいスキーマで再作成されます。")
    else:
        print("\nNo checkpoint files found. Nothing to clean up.")
    
    return deleted_count

if __name__ == "__main__":
    print("=" * 60)
    print("Checkpoint Database Cleanup")
    print("=" * 60)
    print()
    
    cleanup_checkpoints()

# Made with Bob
