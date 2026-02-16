import os
from app import create_app, socketio

# アプリケーションの作成
app = create_app()

if __name__ == '__main__':
    # 開発サーバーの起動
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"Starting AI Agent Team Manager on port {port}...")
    print(f"Debug mode: {debug}")
    
    # Werkzeug 2.0.3との互換性のため、allow_unsafe_werkzeugは使用しない
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug
    )
