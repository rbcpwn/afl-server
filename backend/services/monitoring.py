import os
import json
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

from config import settings
from services.task_manager import task_manager


class MonitoringService:
    """监控服务 - 负责 AFL 统计数据的采集和解析"""

    def __init__(self):
        self._stats_cache = {}

    async def get_task_stats(self, task_id: int) -> Optional[Dict]:
        """获取任务统计数据"""
        task = task_manager.get_task(task_id)
        if not task:
            return None

        # 尝试读取 AFL 的统计文件
        stats_file = os.path.join(task.output_dir, "fuzzer0", "fuzzer_stats")

        if not os.path.exists(stats_file):
            # 返回默认值
            return {
                "exec_count": task.exec_count,
                "unique_crashes": task.unique_crashes,
                "unique_hangs": task.unique_hangs,
                "total_execs": task.total_execs,
                "execs_per_sec": task.execs_per_sec,
                "corpus_count": task.corpus_count,
                "coverage": task.coverage,
                "edges_found": task.edges_found,
                "run_time": self._format_runtime(task)
            }

        try:
            stats = self._parse_fuzzer_stats(stats_file)

            # 统计队列中的样本数量
            queue_dir = os.path.join(task.output_dir, "fuzzer0", "queue")
            corpus_count = 0
            if os.path.exists(queue_dir):
                corpus_count = len([f for f in os.listdir(queue_dir) if f.startswith("id:")])

            # 统计崩溃数量
            crashes_dir = os.path.join(task.output_dir, "fuzzer0", "crashes")
            unique_crashes = 0
            if os.path.exists(crashes_dir):
                unique_crashes = len([f for f in os.listdir(crashes_dir) if f.startswith("id:")])


            stats.update({
                "corpus_count": corpus_count,
                "unique_crashes": unique_crashes,
                "run_time": self._format_runtime(task),
                "coverage": self._calculate_coverage(stats),
                "edges_found": stats.get("edges_found", 0)
            })

            # 更新缓存
            self._stats_cache[task_id] = {
                "data": stats,
                "timestamp": datetime.now()
            }

            return stats

        except Exception as e:
            # 返回缓存数据或默认值
            if task_id in self._stats_cache:
                cached = self._stats_cache[task_id]
                if (datetime.now() - cached["timestamp"]).seconds < 30:
                    return cached["data"]

            return {
                "exec_count": task.exec_count,
                "unique_crashes": task.unique_crashes,
                "run_time": self._format_runtime(task)
            }

    def _parse_fuzzer_stats(self, stats_file: str) -> Dict:
        """解析 AFL fuzzer_stats 文件"""
        stats = {}

        with open(stats_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # AFL stats 格式示例:
        # run_time                : 0 days, 00 hrs, 32 min, 15 sec
        # execs_done              : 1523456
        # execs_per_sec           : 789.12
        # unique_crashes           : 3
        # unique_hangs             : 0

        patterns = {
            "run_time": r"run_time\s*:\s*(.+)",
            "execs_done": r"execs_done\s*:\s*(\d+)",
            "execs_per_sec": r"execs_per_sec\s*:\s*([\d.]+)",
            "unique_crashes": r"unique_crashes\s*:\s*(\d+)",
            "unique_hangs": r"unique_hangs\s*:\s*(\d+)",
            "saved_crashes": r"saved_crashes\s*:\s*(\d+)",
            "saved_hangs": r"saved_hangs\s*:\s*(\d+)",
            "last_path": r"last_path\s*:\s*(.+)",
            "last_crash": r"last_crash\s*:\s*(.+)",
            "last_hang": r"last_hang\s*:\s*(.+)",
            "paths_favored": r"paths_favored\s*:\s*(\d+)",
            "paths_found": r"paths_found\s*:\s*(\d+)",
            "paths_imported": r"paths_imported\s*:\s*(\d+)",
            "max_depth": r"max_depth\s*:\s*(\d+)",
            "cur_path": r"cur_path\s*:\s*(\d+)",
            "map_size": r"map_size\s*:\s*(\d+)",
            "map_density": r"map_density\s*:\s*([\d.]+)",
            "cycles_done": r"cycles_done\s*:\s*(\d+)",
            "cycles_wo_finds": r"cycles_wo_finds\s*:\s*(\d+)",
            "timeout_time": r"timeout_time\s*:\s*(\d+)",
            "unique_hangs": r"unique_hangs\s*:\s*(\d+)",
            "edges_found": r"edges_found\s*:\s*(\d+)",
            "edges_total": r"edges_total\s*:\s*(\d+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                # 尝试转换为数字
                try:
                    if "." in value:
                        stats[key] = float(value)
                    else:
                        stats[key] = int(value)
                except ValueError:
                    stats[key] = value

        return stats

    def _calculate_coverage(self, stats: Dict) -> float:
        """计算覆盖率百分比"""
        edges_found = stats.get("edges_found", 0)
        edges_total = stats.get("edges_total", 0)

        if edges_total == 0:
            return 0.0

        coverage = (edges_found / edges_total) * 100
        return round(coverage, 2)

    def _format_runtime(self, task) -> str:
        """格式化运行时间"""
        now = datetime.now()

        if task.started_at:
            delta = now - task.started_at
        else:
            return "00:00:00"

        total_seconds = int(delta.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    async def get_dashboard_stats(self) -> Dict:
        """获取仪表盘统计数据"""
        tasks = task_manager.get_all_tasks()

        stats = {
            "total_tasks": len(tasks),
            "running_tasks": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_crashes": 0,
            "total_executions": 0,
            "avg_coverage": 0.0
        }

        total_coverage = 0.0
        coverage_count = 0

        for task in tasks:
            if task.task_status.name == "RUNNING":
                stats["running_tasks"] += 1
            elif task.task_status.name == "PENDING":
                stats["pending_tasks"] += 1
            elif task.task_status.name == "COMPLETED":
                stats["completed_tasks"] += 1
            elif task.task_status.name == "FAILED":
                stats["failed_tasks"] += 1

            stats["total_crashes"] += task.unique_crashes
            stats["total_executions"] += task.exec_count

            if task.coverage > 0:
                total_coverage += task.coverage
                coverage_count += 1

        if coverage_count > 0:
            stats["avg_coverage"] = round(total_coverage / coverage_count, 2)

        return stats

    def get_crash_files(self, task_id: int) -> list:
        """获取崩溃文件列表"""
        task = task_manager.get_task(task_id)
        if not task:
            return []

        crashes_dir = os.path.join(task.output_dir, "fuzzer0", "crashes")
        if not os.path.exists(crashes_dir):
            return []

        crash_files = []
        for filename in os.listdir(crashes_dir):
            if filename.startswith("id:"):
                filepath = os.path.join(crashes_dir, filename)
                crash_files.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": os.path.getsize(filepath),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(filepath))
                })

        return sorted(crash_files, key=lambda x: x["mtime"], reverse=True)

    def get_corpus_files(self, task_id: int) -> list:
        """获取语料库文件列表"""
        task = task_manager.get_task(task_id)
        if not task:
            return []

        queue_dir = os.path.join(task.output_dir, "fuzzer0", "queue")
        if not os.path.exists(queue_dir):
            return []

        corpus_files = []
        for filename in os.listdir(queue_dir):
            if filename.startswith("id:"):
                filepath = os.path.join(queue_dir, filename)
                corpus_files.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": os.path.getsize(filepath),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(filepath))
                })

        return sorted(corpus_files, key=lambda x: x["mtime"], reverse=True)


# 全局实例
monitoring_service = MonitoringService()
