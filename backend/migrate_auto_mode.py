"""
データベースマイグレーション: auto_modeカラムを追加
"""
from app import create_app, db
from sqlalchemy import text


def migrate():
    app = create_app()
    with app.app_context():
        try:
            # auto_modeカラムが存在するかチェック
            result = db.session.execute(text("PRAGMA table_info(tasks)"))
            columns = [row[1] for row in result]
            
            if 'auto_mode' not in columns:
                print("Adding auto_mode column to tasks table...")
                db.session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN auto_mode BOOLEAN DEFAULT 0"
                ))
                db.session.commit()
                print("✓ auto_mode column added successfully")
            else:
                print("✓ auto_mode column already exists")
                
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()


if __name__ == '__main__':
    migrate()
