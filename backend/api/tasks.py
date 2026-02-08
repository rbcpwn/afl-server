from datetime import datetime
from typing import Optional
from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource

from models import (
    StartTaskRequest,
    TaskListResponse,
    FuzzStats,
)
from services import task_manager, monitoring_service


api = Namespace("tasks", description="任务管理")


@api.route("/")
class TaskList(Resource):
    """任务列表"""

    def get(self):
        """获取所有任务列表"""
        try:
            tasks = task_manager.get_all_tasks()

            # 过滤参数
            status_filter = request.args.get("status")
            type_filter = request.args.get("type")
            keyword = request.args.get("keyword", "").strip()

            filtered_tasks = []
            for task in tasks:
                # 状态过滤
                if status_filter and task.status.value != status_filter:
                    continue

                # 类型过滤
                if type_filter and task.type.value != type_filter:
                    continue

                # 关键词搜索
                if keyword and keyword.lower() not in task.name.lower():
                    continue

                filtered_tasks.append(task)

            return TaskListResponse(
                tasks=filtered_tasks,
                total=len(filtered_tasks)
            ).model_dump(mode='json'), 200

        except Exception as e:
            current_app.logger.error(f"获取任务列表失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>")
class TaskDetail(Resource):
    """任务详情"""

    def get(self, task_id: int):
        """获取任务详情"""
        try:
            task = task_manager.get_task(task_id)
            if not task:
                return {"error": "任务不存在"}, 404

            return task.model_dump(mode='json'), 200

        except Exception as e:
            current_app.logger.error(f"获取任务详情失败: {e}")
            return {"error": str(e)}, 500

    def delete(self, task_id: int):
        """删除任务"""
        try:
            success = task_manager.delete_task(task_id)
            if not success:
                return {"error": "任务不存在"}, 404

            return {"message": "任务已删除"}, 200

        except Exception as e:
            current_app.logger.error(f"删除任务失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/start")
class TaskStart(Resource):
    """启动任务"""

    def post(self, task_id: int):
        """启动 Fuzz 测试"""
        try:
            # 解析请求参数
            data = StartTaskRequest(**request.json)
            fuzzer_count = data.fuzzer_count

            # 启动任务
            import asyncio
            success = asyncio.run(task_manager.start_fuzz(task_id, fuzzer_count))
            if not success:
                return {"error": "任务启动失败"}, 400

            return {"message": "任务已启动", "task_id": task_id, "fuzzer_count": fuzzer_count}, 200

        except Exception as e:
            current_app.logger.error(f"启动任务失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/pause")
class TaskPause(Resource):
    """暂停任务"""

    def post(self, task_id: int):
        """暂停正在运行的任务"""
        try:
            success = task_manager.pause_task(task_id)
            if not success:
                return {"error": "任务暂停失败"}, 400

            return {"message": "任务已暂停"}, 200

        except Exception as e:
            current_app.logger.error(f"暂停任务失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/resume")
class TaskResume(Resource):
    """恢复任务"""

    def post(self, task_id: int):
        """恢复已暂停的任务"""
        try:
            success = task_manager.resume_task(task_id)
            if not success:
                return {"error": "任务恢复失败"}, 400

            return {"message": "任务已恢复"}, 200

        except Exception as e:
            current_app.logger.error(f"恢复任务失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/stop")
class TaskStop(Resource):
    """停止任务"""

    def post(self, task_id: int):
        """停止正在运行的任务"""
        try:
            success = task_manager.stop_task(task_id)
            if not success:
                return {"error": "任务停止失败"}, 400

            return {"message": "任务已停止"}, 200

        except Exception as e:
            current_app.logger.error(f"停止任务失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/stats")
class TaskStats(Resource):
    """任务统计"""

    def get(self, task_id: int):
        """获取任务统计信息"""
        try:
            task = task_manager.get_task(task_id)
            if not task:
                return {"error": "任务不存在"}, 404

            stats = asyncio.run(monitoring_service.get_task_stats(task_id))

            return FuzzStats(
                task_id=task_id,
                status=task.status,
                exec_count=stats.get("exec_count", task.exec_count),
                unique_crashes=stats.get("unique_crashes", task.unique_crashes),
                unique_hangs=stats.get("unique_hangs", task.unique_hangs),
                total_execs=stats.get("execs_done", task.total_execs),
                execs_per_sec=stats.get("execs_per_sec", task.execs_per_sec),
                corpus_count=stats.get("corpus_count", task.corpus_count),
                edges_found=stats.get("edges_found", task.edges_found),
                edges_total=stats.get("edges_total", 0),
                coverage=stats.get("coverage", task.coverage),
                run_time=stats.get("run_time", "00:00:00"),
                last_update=datetime.now()
            ).model_dump(mode='json'), 200

        except Exception as e:
            current_app.logger.error(f"获取任务统计失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/crashes")
class TaskCrashes(Resource):
    """任务崩溃样本"""

    def get(self, task_id: int):
        """获取任务的崩溃样本列表"""
        try:
            crash_files = monitoring_service.get_crash_files(task_id)

            crashes = []
            for i, cf in enumerate(crash_files, 1):
                crashes.append({
                    "crash_id": f"C{task_id:03d}{i:04d}",
                    "task_id": task_id,
                    "filename": cf["filename"],
                    "size": cf["size"],
                    "found_at": cf["mtime"],
                    "reproducible": True,  # 假设都是可重现的
                    "signal": "SIGSEGV"
                })

            return {"crashes": crashes, "total": len(crashes)}, 200

        except Exception as e:
            current_app.logger.error(f"获取崩溃样本失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/crashes/<filename>")
class CrashDownload(Resource):
    """下载崩溃样本"""

    def get(self, task_id: int, filename: str):
        """下载崩溃样本文件"""
        try:
            import os
            from flask import send_file

            task = task_manager.get_task(task_id)
            if not task:
                return {"error": "任务不存在"}, 404

            crash_dir = os.path.join(task.output_dir, "fuzzer0", "crashes")
            filepath = os.path.join(crash_dir, filename)

            if not os.path.exists(filepath):
                return {"error": "文件不存在"}, 404

            return send_file(filepath, as_attachment=True, download_name=filename)

        except Exception as e:
            current_app.logger.error(f"下载崩溃样本失败: {e}")
            return {"error": str(e)}, 500


@api.route("/<int:task_id>/corpus")
class TaskCorpus(Resource):
    """任务语料库"""

    def get(self, task_id: int):
        """获取任务的语料库文件列表"""
        try:
            corpus_files = monitoring_service.get_corpus_files(task_id)

            corpus = []
            for cf in corpus_files:
                corpus.append({
                    "filename": cf["filename"],
                    "size": cf["size"],
                    "mtime": cf["mtime"]
                })

            return {"corpus": corpus, "total": len(corpus)}, 200

        except Exception as e:
            current_app.logger.error(f"获取语料库失败: {e}")
            return {"error": str(e)}, 500
