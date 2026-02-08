import asyncio
import json
from datetime import datetime
from flask_socketio import emit
from config import settings
from services import task_manager, monitoring_service


def register_socket_events(socketio):
    """注册 WebSocket 事件处理器"""

    @socketio.on("connect")
    def handle_connect():
        """处理客户端连接"""
        print(f"客户端连接: {datetime.now()}")
        emit("connected", {"message": "已连接到 AFL Fuzz 平台"})

    @socketio.on("disconnect")
    def handle_disconnect():
        """处理客户端断开连接"""
        print(f"客户端断开连接: {datetime.now()}")

    @socketio.on("subscribe_task")
    def handle_subscribe_task(data):
        """订阅任务实时数据"""
        task_id = data.get("task_id")

        if task_id:
            # 启动任务监控任务
            asyncio.create_task(monitor_task_updates(task_id, socketio))

    @socketio.on("unsubscribe_task")
    def handle_unsubscribe_task(data):
        """取消订阅任务"""
        task_id = data.get("task_id")
        # 这里可以添加取消订阅的逻辑
        print(f"取消订阅任务: {task_id}")

    @socketio.on("subscribe_dashboard")
    def handle_subscribe_dashboard():
        """订阅仪表盘实时数据"""
        asyncio.create_task(monitor_dashboard_updates(socketio))

    @socketio.on("ping")
    def handle_ping():
        """处理心跳检测"""
        emit("pong", {"timestamp": datetime.now().isoformat()})


async def monitor_task_updates(task_id: int, socketio):
    """监控任务更新并发送到客户端"""
    task = task_manager.get_task(task_id)
    if not task:
        return

    last_stats = {}

    while True:
        try:
            # 获取最新统计信息
            stats = await monitoring_service.get_task_stats(task_id)

            if stats and stats != last_stats:
                # 发送任务更新
                socketio.emit("task_update", {
                    "task_id": task_id,
                    "task_name": task.name,
                    "status": task.status.value,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })

                last_stats = stats.copy()

                # 如果任务状态变化，发送状态更新
                if task.status.value in ["completed", "failed", "stopped"]:
                    break

        except Exception as e:
            print(f"监控任务更新失败: {e}")
            break

        # 2秒轮询一次
        await asyncio.sleep(2)


async def monitor_dashboard_updates(socketio):
    """监控仪表盘更新并发送到客户端"""
    last_total_crashes = -1
    last_total_executions = -1

    while True:
        try:
            stats = await monitoring_service.get_dashboard_stats()

            # 只在有变化时发送
            if (stats["total_crashes"] != last_total_crashes or
                stats["total_executions"] != last_total_executions):

                socketio.emit("dashboard_update", {
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })

                last_total_crashes = stats["total_crashes"]
                last_total_executions = stats["total_executions"]

        except Exception as e:
            print(f"监控仪表盘更新失败: {e}")
            break

        # 5秒轮询一次
        await asyncio.sleep(5)
