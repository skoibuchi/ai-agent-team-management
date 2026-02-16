"""
セットアップスクリプト
データベースの初期化と組み込みツールの登録を行います
"""
from app import create_app, db
from app.services.tool_service import ToolService


def setup_database():
    """データベースをセットアップ"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created")
        
        print("\nInitializing built-in tools...")
        tool_service = ToolService()
        tool_service.initialize_builtin_tools()
        print("✓ Built-in tools initialized")
        
        print("\n✓ Setup completed successfully!")
        print("\nYou can now:")
        print("1. Copy .env.example to .env and configure your API keys")
        print("2. Run 'python run.py' to start the server")


if __name__ == '__main__':
    setup_database()
