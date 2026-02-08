from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restx import Api
from flask_socketio import SocketIO
from config import settings
from api import upload_api, tasks_api, results_api


def create_app(config_name=None):
    """创建 Flask 应用"""

    app = Flask(__name__)

    # 加载配置
    app.config["DEBUG"] = settings.debug
    app.config["SECRET_KEY"] = "afl-fuzz-platform-secret-key"

    # CORS 配置
    CORS(app, resources={
        r"/api/*": {
            "origins": settings.cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 初始化 Socket.IO
    socketio = SocketIO(
        app,
        cors_allowed_origins=settings.cors_origins,
        async_mode="eventlet",
        logger=True,
        engineio_logger=False
    )

    # 初始化 API
    api_bp = Blueprint("api", __name__, url_prefix="/api")
    api = Api(api_bp, version="1.0", title="AFL Fuzz Platform API",
              description="基于AFL的二进制漏洞挖掘平台API")

    # 注册 API 命名空间
    api.add_namespace(upload_api)
    api.add_namespace(tasks_api)
    api.add_namespace(results_api)

    app.register_blueprint(api_bp)

    # 注册 Socket.IO 事件处理
    from websocket_events import register_socket_events
    register_socket_events(socketio)

    # 健康检查端点
    @app.route("/health")
    def health_check():
        return {"status": "ok", "service": "afl-fuzz-platform"}, 200

    @app.route("/")
    def index():
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "status": "running"
        }, 200

    return app, socketio


app, socketio = create_app()


if __name__ == "__main__":
    socketio.run(app, host=settings.host, port=settings.port, debug=settings.debug)
