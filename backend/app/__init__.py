from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

from app.config import get_config

# 拡張機能の初期化
db = SQLAlchemy()
socketio = SocketIO()
celery = Celery()


def create_app(config_name=None):
    """Flaskアプリケーションファクトリ"""
    app = Flask(__name__)
    
    # 設定の読み込み
    if config_name is None:
        config_class = get_config()
    else:
        from app.config import config
        config_class = config[config_name]
    
    app.config.from_object(config_class)
    
    # 拡張機能の初期化
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    socketio.init_app(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    # Celeryの設定
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )
    
    # ログ設定
    setup_logging(app)
    
    # Blueprintの登録
    register_blueprints(app)
    
    # WebSocketイベントハンドラの登録
    register_socketio_events()
    
    # データベースの初期化
    with app.app_context():
        # モデルをインポート（db.create_all()の直前）
        from app.models import agent, task, team, tool, execution_log, llm_setting, tool_approval, task_interaction  # noqa: F401
        db.create_all()
    
    # エラーハンドラーの登録
    register_error_handlers(app)
    
    return app


def register_error_handlers(app):
    """エラーハンドラーの登録"""
    import traceback
    from flask import jsonify
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """全ての例外をキャッチして詳細を出力"""
        app.logger.error(f"Unhandled exception: {str(e)}")
        app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def register_blueprints(app):
    """Blueprintの登録"""
    from app.api.agents import agents_bp
    from app.api.tasks import tasks_bp
    from app.api.teams import teams_bp
    from app.api.tools import tools_bp
    from app.api.settings import settings_bp
    from app.api.task_analysis import task_analysis_bp
    from app.api.approvals import approvals_bp
    from app.api.task_interactions import bp as task_interactions_bp
    
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(teams_bp, url_prefix='/api/teams')
    app.register_blueprint(tools_bp, url_prefix='/api/tools')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(task_analysis_bp, url_prefix='/api/task-analysis')
    app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
    app.register_blueprint(task_interactions_bp)


def register_socketio_events():
    """WebSocketイベントハンドラの登録"""
    from app.websocket import events


def setup_logging(app):
    """ログ設定"""
    import logging
    import os
    from logging.handlers import RotatingFileHandler
    
    # ログディレクトリの作成
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # ログレベルの設定
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    
    # ファイルハンドラの設定
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    
    # ロガーの設定
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    app.logger.info('AI Agent Team Manager started')
