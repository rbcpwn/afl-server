import os
import subprocess
import shutil
from typing import List, Optional
from pathlib import Path

from config import settings
from models import Task, TaskType, InputType, TaskStatus


class CompilationService:
    """编译服务 - 负责白盒测试的代码编译"""

    def __init__(self):
        # 检查 AFL 编译器是否可用
        self._check_afl_compilers()

    def _check_afl_compilers(self):
        """检查 AFL 编译器是否可用"""
        for compiler in [settings.afl_gcc_path, settings.afl_gxx_path]:
            if not os.path.exists(compiler):
                print(f"警告: {compiler} 不存在，将尝试使用系统默认编译器")

    async def compile_source(
        self,
        task: Task,
        source_files: List[str],
        main_file: str,
        compile_args: str = ""
    ) -> tuple[bool, Optional[str]]:
        """编译源代码生成可执行文件"""

        # 确定使用的编译器
        is_cpp = any(f.endswith((".cpp", ".cc", ".cxx")) for f in source_files)
        compiler = settings.afl_gxx_path if is_cpp else settings.afl_gcc_path

        # 如果 AFL 编译器不可用，使用系统编译器
        if not os.path.exists(compiler):
            compiler = "g++" if is_cpp else "gcc"

        # 输出文件路径
        task_dir = os.path.join(settings.tasks_dir, f"task_{task.id}")
        output_file = os.path.join(task_dir, "target")

        # 构建编译命令
        compile_command = [compiler]

        # 添加编译参数
        if compile_args:
            compile_command.extend(compile_args.split())

        # 添加基础编译参数
        compile_command.extend([
            "-g",  # 生成调试信息
            "-O2",  # 优化级别
            "-o", output_file
        ])

        # 添加源文件
        compile_command.extend(source_files)

        # 添加 AFL 标志（如果使用 AFL 编译器）
        if os.path.exists(compiler):
            compile_command.append("-fno-omit-frame-pointer")

        try:
            # 执行编译
            process = subprocess.Popen(
                compile_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=60)

            if process.returncode != 0:
                error_msg = stderr or stdout or "编译失败"
                return False, error_msg

            # 检查输出文件是否生成
            if not os.path.exists(output_file):
                return False, "编译成功但未找到输出文件"

            # 设置可执行权限
            os.chmod(output_file, 0o755)

            # 更新任务信息
            task.target_binary = output_file
            task.task_status = TaskStatus.READY

            return True, None

        except subprocess.TimeoutExpired:
            process.kill()
            return False, "编译超时"
        except Exception as e:
            return False, str(e)

    async def validate_binary(self, binary_path: str) -> tuple[bool, Optional[str]]:
        """验证二进制文件是否有效"""
        if not os.path.exists(binary_path):
            return False, "文件不存在"

        if not os.access(binary_path, os.X_OK):
            return False, "文件不可执行"

        # 使用 file 命令检查文件类型
        try:
            result = subprocess.run(
                ["file", binary_path],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False  # 避免路径解析问题
            )

            if "ELF" not in result.stdout:
                return False, "不是有效的 ELF 文件"

            if "executable" not in result.stdout:
                return False, "不是可执行文件"

            return True, None

        except Exception as e:
            return False, str(e)


class SeedService:
    """种子服务 - 负责种子文件的管理"""

    def __init__(self):
        pass

    async def save_seeds(
        self,
        task_id: int,
        files: List[tuple[str, bytes]],
        replace: bool = False
    ) -> int:
        """保存种子文件"""
        task_seeds_dir = os.path.join(settings.seeds_dir, f"task_{task_id}")

        # 如果替换模式，清空目录
        if replace and os.path.exists(task_seeds_dir):
            shutil.rmtree(task_seeds_dir)
            os.makedirs(task_seeds_dir)

        # 如果目录不存在，创建
        if not os.path.exists(task_seeds_dir):
            os.makedirs(task_seeds_dir)

        saved_count = 0

        for filename, content in files:
            # 验证文件名
            safe_filename = self._sanitize_filename(filename)
            if not safe_filename:
                continue

            filepath = os.path.join(task_seeds_dir, safe_filename)

            try:
                with open(filepath, "wb") as f:
                    f.write(content)
                saved_count += 1
            except Exception as e:
                print(f"保存种子文件失败: {e}")
                continue

        return saved_count

    async def add_default_seeds(self, task_id: int):
        """添加默认种子文件"""
        task_seeds_dir = os.path.join(settings.seeds_dir, f"task_{task_id}")

        if not os.path.exists(task_seeds_dir):
            os.makedirs(task_seeds_dir)

        # 根据输入类型添加不同的默认种子
        default_seeds = {
            "stdin": [
                ("empty", b""),
                ("null", b"\x00"),
                ("newline", b"\n"),
                ("simple", b"Hello World\n"),
                ("ascii", b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789\n")
            ],
            "file": [
                ("empty.txt", b""),
                ("simple.txt", b"Hello World\n"),
                ("multiline.txt", b"Line 1\nLine 2\nLine 3\n")
            ]
        }

        # 读取任务的输入类型
        from services.task_manager import task_manager
        task = task_manager.get_task(task_id)
        input_type = (task.input_type.value if task else "stdin").lower()

        seeds = default_seeds.get(input_type, default_seeds["stdin"])

        for filename, content in seeds:
            filepath = os.path.join(task_seeds_dir, filename)
            with open(filepath, "wb") as f:
                f.write(content)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        # 移除路径
        filename = os.path.basename(filename)

        # 移除不安全字符
        unsafe_chars = "..", "/", "\\", "\x00"
        for char in unsafe_chars:
            filename = filename.replace(char, "")

        # 限制长度
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename or "seed"


# 全局实例
compilation_service = CompilationService()
seed_service = SeedService()
