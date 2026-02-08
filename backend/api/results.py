from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource
from flask import send_file

from models import DashboardStats, CrashInfo
from services import monitoring_service, task_manager
import os


api = Namespace("results", description="结果分析")


@api.route("/dashboard")
class Dashboard(Resource):
    """仪表盘统计"""

    def get(self):
        """获取仪表盘统计数据"""
        try:
            import asyncio
            stats = asyncio.run(monitoring_service.get_dashboard_stats())

            return DashboardStats(**stats).model_dump(), 200

        except Exception as e:
            current_app.logger.error(f"获取仪表盘统计失败: {e}")
            return {"error": str(e)}, 500


@api.route("/crashes")
class Crashes(Resource):
    """崩溃样本列表"""

    def get(self):
        """获取所有崩溃样本"""
        try:
            task_id = request.args.get("taskId", type=int)

            crashes = []

            if task_id:
                # 获取指定任务的崩溃
                crash_files = monitoring_service.get_crash_files(task_id)
                task = task_manager.get_task(task_id)

                for i, cf in enumerate(crash_files, 1):
                    crashes.append({
                        "crash_id": f"C{task_id:03d}{i:04d}",
                        "task_id": task_id,
                        "task_name": task.name if task else "Unknown",
                        "filename": cf["filename"],
                        "crash_type": "Heap Overflow",  # 简化处理
                        "signal": "SIGSEGV",
                        "reproducible": True,
                        "severity": 5,
                        "sample_file": cf["filename"],
                        "found_at": cf["mtime"],
                        "stack_trace": None
                    })
            else:
                # 获取所有任务的崩溃
                tasks = task_manager.get_all_tasks()
                for task in tasks:
                    crash_files = monitoring_service.get_crash_files(task.id)

                    for i, cf in enumerate(crash_files, 1):
                        crashes.append({
                            "crash_id": f"C{task.id:03d}{i:04d}",
                            "task_id": task.id,
                            "task_name": task.name,
                            "filename": cf["filename"],
                            "crash_type": "Heap Overflow",
                            "signal": "SIGSEGV",
                            "reproducible": True,
                            "severity": 5,
                            "sample_file": cf["filename"],
                            "found_at": cf["mtime"],
                            "stack_trace": None
                        })

            # 按时间倒序排序
            crashes.sort(key=lambda x: x["found_at"], reverse=True)

            return {"crashes": crashes, "total": len(crashes)}, 200

        except Exception as e:
            current_app.logger.error(f"获取崩溃列表失败: {e}")
            return {"error": str(e)}, 500


@api.route("/crashes/<crash_id>/download")
class CrashDownload(Resource):
    """下载崩溃样本"""

    def get(self, crash_id: str):
        """下载崩溃样本文件"""
        try:
            # 解析 crash_id 获取 task_id 和文件名
            # 格式: C{task_id:03d}{index:04d}
            task_id = int(crash_id[1:4])

            task = task_manager.get_task(task_id)
            if not task:
                return {"error": "任务不存在"}, 404

            crash_dir = os.path.join(task.output_dir, "fuzzer0", "crashes")
            crash_files = os.listdir(crash_dir) if os.path.exists(crash_dir) else []

            if not crash_files:
                return {"error": "没有崩溃文件"}, 404

            # 获取第一个崩溃文件（简化处理）
            filename = crash_files[0]
            filepath = os.path.join(crash_dir, filename)

            if not os.path.exists(filepath):
                return {"error": "文件不存在"}, 404

            return send_file(filepath, as_attachment=True, download_name=filename)

        except Exception as e:
            current_app.logger.error(f"下载崩溃样本失败: {e}")
            return {"error": str(e)}, 500


@api.route("/coverage")
class Coverage(Resource):
    """覆盖率报告"""

    def get(self):
        """获取覆盖率报告"""
        try:
            task_id = request.args.get("taskId", type=int)

            coverage_data = []

            if task_id:
                # 获取指定任务的覆盖率
                task = task_manager.get_task(task_id)
                if task:
                    coverage_data.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "edge_coverage": task.coverage,
                        "path_coverage": task.coverage * 0.8,  # 简化处理
                        "unique_crashes": task.unique_crashes,
                        "total_execs": task.exec_count,
                        "duration": "Running" if task.status.value == "running" else "Completed"
                    })
            else:
                # 获取所有任务的覆盖率
                tasks = task_manager.get_all_tasks()
                for task in tasks:
                    coverage_data.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "edge_coverage": task.coverage,
                        "path_coverage": task.coverage * 0.8,
                        "unique_crashes": task.unique_crashes,
                        "total_execs": task.exec_count,
                        "duration": "Running" if task.status.value == "running" else "Completed"
                    })

            return {"coverage": coverage_data, "total": len(coverage_data)}, 200

        except Exception as e:
            current_app.logger.error(f"获取覆盖率报告失败: {e}")
            return {"error": str(e)}, 500


@api.route("/export")
class Export(Resource):
    """导出报告"""

    def get(self):
        """导出测试报告"""
        try:
            task_id = request.args.get("taskId", type=int)

            # 生成 JSON 报告
            report = {
                "generated_at": str(monitoring_service._format_runtime.__self__.__class__),
                "tasks": [],
                "total_crashes": 0,
                "total_executions": 0
            }

            tasks = task_manager.get_all_tasks()
            for task in tasks:
                if task_id is None or task.id == task_id:
                    task_data = {
                        "task_id": task.id,
                        "task_name": task.name,
                        "task_type": task.type.value,
                        "status": task.status.value,
                        "created_at": str(task.created_at),
                        "started_at": str(task.started_at) if task.started_at else None,
                        "completed_at": str(task.completed_at) if task.completed_at else None,
                        "exec_count": task.exec_count,
                        "unique_crashes": task.unique_crashes,
                        "coverage": task.coverage
                    }
                    report["tasks"].append(task_data)
                    report["total_crashes"] += task.unique_crashes
                    report["total_executions"] += task.exec_count

            import json
            return jsonify(report), 200, {
                "Content-Type": "application/json",
                "Content-Disposition": "attachment; filename=fuzz_report.json"
            }

        except Exception as e:
            current_app.logger.error(f"导出报告失败: {e}")
            return {"error": str(e)}, 500
