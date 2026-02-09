import os
import shutil
import json
import asyncio
import signal
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from config import settings
from models import Task, TaskType, TaskStatus, InputType


class TaskManager:
    """任务管理器 - 负责任务的创建、启动、停止和状态管理"""

    _instance = None
    _tasks: Dict[int, Task] = {}
    _task_id_counter = 0
    _task_processes: Dict[int, subprocess.Popen] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化任务管理器"""
        if not hasattr(self, '_initialized'):
            self._load_tasks()
            self._initialized = True

    @classmethod
    def get_instance(cls) -> 'TaskManager':
        return cls()

    def create_task_id(self) -> int:
        """创建新任务ID"""
        self._task_id_counter += 1
        return self._task_id_counter

    def create_task(
        self,
        name: str,
        task_type: TaskType,
        input_type: InputType = InputType.STDIN,
        compile_args: str = "",
        fuzz_args: str = "",
        dependencies: str = "",
        source_files: List[str] = None,
        elf_file: str = None
    ) -> Task:
        """创建新任务"""
        task_id = self.create_task_id()

        # 创建任务目录
        task_dir = os.path.join(settings.tasks_dir, f"task_{task_id}")
        os.makedirs(task_dir, exist_ok=True)

        # 创建输出目录
        output_dir = os.path.join(settings.outputs_dir, f"task_{task_id}")
        os.makedirs(output_dir, exist_ok=True)

        # 创建种子目录
        seeds_dir = os.path.join(settings.seeds_dir, f"task_{task_id}")
        os.makedirs(seeds_dir, exist_ok=True)

        # 创建崩溃目录
        crashes_dir = os.path.join(settings.crashes_dir, f"task_{task_id}")
        os.makedirs(crashes_dir, exist_ok=True)

        now = datetime.now()

        task = Task(
            id=task_id,
            name=name,
            type=task_type,
            status=TaskStatus.UPLOADING,
            input_type=input_type,
            compile_args=compile_args if task_type == TaskType.WHITEBOX else None,
            fuzz_args=fuzz_args,
            dependencies=dependencies if task_type == TaskType.BLACKBOX else None,
            source_files=source_files or [],
            elf_file=elf_file,
            seeds_dir=seeds_dir,
            output_dir=output_dir,
            created_at=now,
            last_updated=now
        )

        self._tasks[task_id] = task
        self._save_task(task)
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self._tasks.values())

    def update_task_status(self, task_id: int, status: TaskStatus, error_message: str = None):
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            task.last_updated = datetime.now()
            if error_message:
                task.error_message = error_message

            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.STOPPED]:
                task.completed_at = datetime.now()

        self._save_task(task)

    def _save_task(self, task: Task):
        """保存任务到文件"""
        task_file = os.path.join(settings.tasks_dir, f"task_{task.id}", "task.json")
        try:
            with open(task_file, 'w') as f:
                json.dump(task.model_dump(mode='json'), f, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")

    def _load_tasks(self):
        """从文件加载所有任务"""
        self._tasks = {}
        self._task_id_counter = 0
        try:
            for task_dir in os.listdir(settings.tasks_dir):
                if not task_dir.startswith("task_"):
                    continue
                task_file = os.path.join(settings.tasks_dir, task_dir, "task.json")
                if not os.path.exists(task_file):
                    continue
                with open(task_file, 'r') as f:
                    task_data = json.load(f)
                    task = Task(**task_data)
                    self._tasks[task.id] = task
                    if task.id > self._task_id_counter:
                        self._task_id_counter = task.id
        except Exception as e:
            print(f"加载任务失败: {e}")

    def update_task_stats(
        self,
        task_id: int,
        exec_count: int = None,
        unique_crashes: int = None,
        unique_hangs: int = None,
        total_execs: int = None,
        execs_per_sec: float = None,
        corpus_count: int = None,
        coverage: float = None,
        edges_found: int = None
    ):
        """更新任务统计信息"""
        task = self._tasks.get(task_id)
        if task:
            if exec_count is not None:
                task.exec_count = exec_count
            if unique_crashes is not None:
                task.unique_crashes = unique_crashes
            if unique_hangs is not None:
                task.unique_hangs = unique_hangs
            if total_execs is not None:
                task.total_execs = total_execs
            if execs_per_sec is not None:
                task.execs_per_sec = execs_per_sec
            if corpus_count is not None:
                task.corpus_count = corpus_count
            if coverage is not None:
                task.coverage = coverage
            if edges_found is not None:
                task.edges_found = edges_found

            task.last_updated = datetime.now()

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        # 停止正在运行的任务
        if task.status == TaskStatus.RUNNING:
            self.stop_task(task_id)

        # 删除进程记录
        if task_id in self._task_processes:
            del self._task_processes[task_id]

        # 删除任务数据
        if task_id in self._tasks:
            del self._tasks[task_id]

        # 删除目录
        for base_dir in [settings.tasks_dir, settings.outputs_dir, settings.seeds_dir, settings.crashes_dir]:
            task_dir = os.path.join(base_dir, f"task_{task_id}")
            if os.path.exists(task_dir):
                shutil.rmtree(task_dir)

        return True

    async def start_fuzz(self, task_id: int, fuzzer_count: int = 1) -> bool:
        """启动 Fuzz 测试"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status != TaskStatus.READY:
            return False

        try:
            self.update_task_status(task_id, TaskStatus.RUNNING)

            # 构建 AFL 命令
            command = self._build_afl_command(task, fuzzer_count)

            # 创建输出目录结构
            for i in range(fuzzer_count):
                fuzzer_output_dir = os.path.join(task.output_dir, f"fuzzer{i}")
                os.makedirs(os.path.join(fuzzer_output_dir, "queue"), exist_ok=True)
                os.makedirs(os.path.join(fuzzer_output_dir, "crashes"), exist_ok=True)
                os.makedirs(os.path.join(fuzzer_output_dir, "hangs"), exist_ok=True)

            # 启动主 fuzzer
            env = os.environ.copy()
            env["AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES"] = "1"
            env["AFL_SKIP_CPUFREQ"] = "1"

            # 使用异步方式启动进程
            process = subprocess.Popen(
                command,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            self._task_processes[task_id] = process
            task.pid = process.pid
            task.fuzzer_count = fuzzer_count

            # 启动监控线程
            asyncio.create_task(self._monitor_task(task_id))

            return True

        except Exception as e:
            self.update_task_status(task_id, TaskStatus.FAILED, str(e))
            return False

    def _build_afl_command(self, task: Task, fuzzer_count: int) -> List[str]:
        """构建 AFL 命令"""
        command = [settings.afl_path]

        # 基础参数
        command.extend(["-i", task.seeds_dir])  # 输入目录
        command.extend(["-o", task.output_dir])  # 输出目录

        # 超时时间 - 使用 AFL 默认值，除非用户自定义
        if task.fuzz_args:
            # 检查用户是否自定义了超时参数
            timeout_customized = any("-t" in arg or "--timeout" in arg for arg in task.fuzz_args.split())
            if not timeout_customized:
                command.extend(["-t", str(settings.default_timeout)])

        # 添加用户自定义参数
        if task.fuzz_args:
            command.extend(task.fuzz_args.split())

        # 如果用户没有自定义参数，添加 AFL 默认参数以提高性能
        if not task.fuzz_args:
            # 使用 AFL 默认参数（基于 AFL 最佳实践）
            command.extend([
                "-m", "none",                    # 不进行 CPU 节流检测（在虚拟化环境中使用）
                "-d",                             # 去除确定性模式
                "-Q",                             # 使用 QEMU 模式的日志格式
                "-b",                             # 保存崩溃的输入
            ])
        else:
            # 即使用户提供了参数，也确保 -m none（在虚拟化环境中推荐）
            if not any("-m" in arg for arg in task.fuzz_args.split()):
                command.extend(["-m", "none"])

        # 内存限制
        command.extend(["-m", "none"])  # 确保在虚拟化环境中不进行 CPU 节流检测

        # 多实例模式
        if fuzzer_count > 1:
            command.extend(["-M", "fuzzer0"])  # 主 fuzzer
        else:
            command.extend(["-M", "fuzzer0"])

        # 目标程序
        command.extend(["--", task.target_binary])

        return command

    async def _monitor_task(self, task_id: int):
        """监控任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return

        from services import MonitoringService

        monitoring_service = MonitoringService()

        while task.status == TaskStatus.RUNNING:
            # 更新统计信息
            stats = await monitoring_service.get_task_stats(task_id)
            if stats:
                self.update_task_stats(
                    task_id,
                    exec_count=stats.get("exec_count", 0),
                    unique_crashes=stats.get("unique_crashes", 0),
                    total_execs=stats.get("total_execs", 0),
                    execs_per_sec=stats.get("execs_per_sec", 0.0),
                    corpus_count=stats.get("corpus_count", 0),
                    coverage=stats.get("coverage", 0.0),
                    edges_found=stats.get("edges_found", 0)
                )

            # 检查进程是否还在运行
            if task_id in self._task_processes:
                process = self._task_processes[task_id]
                if process.poll() is not None:
                    # 进程已退出
                    return_code = process.returncode
                    if return_code != 0:
                        self.update_task_status(task_id, TaskStatus.FAILED, f"进程异常退出，返回码: {return_code}")
                    else:
                        self.update_task_status(task_id, TaskStatus.COMPLETED)
                    break

            await asyncio.sleep(2)

    def stop_task(self, task_id: int) -> bool:
        """停止任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status != TaskStatus.RUNNING:
            return False

        try:
            # 停止 AFL 进程
            if task_id in self._task_processes:
                process = self._task_processes[task_id]
                # 发送 SIGTERM
                process.terminate()

                # 等待进程退出
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    process.kill()

                del self._task_processes[task_id]

            self.update_task_status(task_id, TaskStatus.STOPPED)
            return True

        except Exception as e:
            return False

    def pause_task(self, task_id: int) -> bool:
        """暂停任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status != TaskStatus.RUNNING:
            return False

        try:
            if task_id in self._task_processes:
                process = self._task_processes[task_id]
                process.send_signal(signal.SIGSTOP)
                self.update_task_status(task_id, TaskStatus.PAUSED)
                return True
        except Exception as e:
            return False

        return False

    def resume_task(self, task_id: int) -> bool:
        """恢复任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status != TaskStatus.PAUSED:
            return False

        try:
            if task_id in self._task_processes:
                process = self._task_processes[task_id]
                process.send_signal(signal.SIGCONT)
                self.update_task_status(task_id, TaskStatus.RUNNING)
                return True
        except Exception as e:
            return False

        return False


# 全局实例
task_manager = TaskManager()
