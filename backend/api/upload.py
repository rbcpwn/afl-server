import os
import shutil
import tempfile
from datetime import datetime
from typing import List
from werkzeug.utils import secure_filename

from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource

from config import settings
from models import (
    CreateWhiteboxTaskRequest,
    CreateBlackboxTaskRequest,
    TaskCreateResponse,
    Task,
    TaskType,
    TaskStatus,
    InputType
)
from services import task_manager, compilation_service, seed_service


api = Namespace("upload", description="文件上传和任务创建")


def allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_upload_file(file, target_dir: str) -> str:
    """保存上传的文件"""
    # 确保目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 获取安全的文件名
    filename = secure_filename(file.filename)
    if not filename:
        filename = f"upload_{datetime.now().timestamp()}"

    # 构建完整路径
    filepath = os.path.join(target_dir, filename)

    # 保存文件
    file.save(filepath)

    return filepath


@api.route("/whitebox")
class WhiteboxUpload(Resource):
    """白盒测试文件上传"""

    def post(self):
        """上传 C/C++ 源代码并创建白盒测试任务"""

        try:
            # 检查是否包含文件
            if "files" not in request.files:
                return {"error": "没有上传文件"}, 400

            files = request.files.getlist("files")
            if not files or len(files) == 0:
                return {"error": "没有选择文件"}, 400

            # 获取表单数据
            task_name = request.form.get("taskName", "").strip()
            main_file = request.form.get("mainFile", "").strip()
            compile_args = request.form.get("compileArgs", "").strip()
            fuzz_args = request.form.get("fuzzArgs", "").strip()
            input_type_str = request.form.get("inputType", "stdin").strip()

            if not task_name:
                return {"error": "任务名称不能为空"}, 400

            if not main_file:
                return {"error": "请指定主程序文件"}, 400

            # 验证文件类型
            allowed_extensions = ["c", "cpp", "cc", "cxx", "h", "hpp"]
            saved_files = []

            for file in files:
                if file.filename == "":
                    continue

                if not allowed_file(file.filename, allowed_extensions):
                    return {"error": f"不支持的文件类型: {file.filename}"}, 400

                # 保存到临时目录
                temp_dir = os.path.join(settings.upload_dir, f"temp_{datetime.now().timestamp()}")
                filepath = save_upload_file(file, temp_dir)
                saved_files.append(filepath)

            # 检查主文件是否存在
            main_file_path = None
            for f in saved_files:
                if os.path.basename(f) == main_file:
                    main_file_path = f
                    break

            if not main_file_path:
                return {"error": f"未找到主程序文件: {main_file}"}, 400

            # 创建任务
            input_type = InputType(input_type_str) if input_type_str else InputType.STDIN

            task = task_manager.create_task(
                name=task_name,
                task_type=TaskType.WHITEBOX,
                input_type=input_type,
                compile_args=compile_args,
                fuzz_args=fuzz_args,
                source_files=saved_files,
                elf_file=None
            )

            # 编译源代码
            task_manager.update_task_status(task.id, task.status, message="Compiling")
            task_manager.update_task_status(task.id, TaskStatus.COMPILING)

            import asyncio
            success, error_msg = asyncio.run(compilation_service.compile_source(
                task, saved_files, main_file, compile_args
            ))

            if not success:
                task_manager.update_task_status(task.id, TaskStatus.FAILED, error_msg)
                return {"error": f"编译失败: {error_msg}"}, 400

            # 添加默认种子
            import asyncio
            asyncio.run(seed_service.add_default_seeds(task.id))

            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)

            task_manager.update_task_status(task.id, TaskStatus.READY)

            return TaskCreateResponse(
                task_id=task.id,
                task_name=task.name,
                message="白盒测试任务创建成功"
            ).model_dump(), 201

        except Exception as e:
            current_app.logger.error(f"白盒测试任务创建失败: {e}")
            return {"error": str(e)}, 500


@api.route("/blackbox")
class BlackboxUpload(Resource):
    """黑盒测试文件上传"""

    def post(self):
        """上传 ELF 二进制文件并创建黑盒测试任务"""

        try:
            # 检查是否包含文件
            if "file" not in request.files:
                return {"error": "没有上传文件"}, 400

            file = request.files["file"]

            if file.filename == "":
                return {"error": "没有选择文件"}, 400

            # 获取表单数据
            task_name = request.form.get("taskName", "").strip()
            input_type_str = request.form.get("inputType", "stdin").strip()
            fuzz_args = request.form.get("fuzzArgs", "").strip()
            dependencies = request.form.get("dependencies", "").strip()

            if not task_name:
                return {"error": "任务名称不能为空"}, 400

            # 保存 ELF 文件
            temp_dir = os.path.join(settings.upload_dir, f"temp_{datetime.now().timestamp()}")
            filepath = save_upload_file(file, temp_dir)

            # 设置可执行权限
            os.chmod(filepath, 0o755)

            # 验证 ELF 文件
            import asyncio
            success, error_msg = asyncio.run(compilation_service.validate_binary(filepath))
            if not success:
                return {"error": f"ELF 文件验证失败: {error_msg}"}, 400

            # 创建任务
            input_type = InputType(input_type_str) if input_type_str else InputType.STDIN

            task = task_manager.create_task(
                name=task_name,
                task_type=TaskType.BLACKBOX,
                input_type=input_type,
                fuzz_args=fuzz_args,
                dependencies=dependencies,
                source_files=[],
                elf_file=filepath
            )

            # 设置目标二进制文件
            task.target_binary = filepath

            # 添加默认种子
            asyncio.run(seed_service.add_default_seeds(task.id))

            # 清理临时目录（只保留目标文件）
            for f in os.listdir(temp_dir):
                if f != os.path.basename(filepath):
                    os.remove(os.path.join(temp_dir, f))

            task_manager.update_task_status(task.id, TaskStatus.READY)

            return TaskCreateResponse(
                task_id=task.id,
                task_name=task.name,
                message="黑盒测试任务创建成功"
            ).model_dump(), 201

        except Exception as e:
            current_app.logger.error(f"黑盒测试任务创建失败: {e}")
            return {"error": str(e)}, 500


@api.route("/seeds")
class SeedsUpload(Resource):
    """种子文件上传"""

    def post(self):
        """上传种子文件"""

        try:
            # 检查是否包含文件
            if "files" not in request.files:
                return {"error": "没有上传文件"}, 400

            files = request.files.getlist("files")
            if not files or len(files) == 0:
                return {"error": "没有选择文件"}, 400

            # 获取任务ID（可选）
            task_id_str = request.form.get("taskId", "").strip()
            task_id = int(task_id_str) if task_id_str else None

            # 准备文件数据
            file_data = []
            for file in files:
                if file.filename == "":
                    continue
                file_data.append((file.filename, file.read()))

            # 如果没有指定任务，创建一个新的种子集
            if task_id is None:
                task_id = task_manager.create_task_id()
                # 创建一个占位任务
                temp_dir = os.path.join(settings.seeds_dir, f"task_{task_id}")
                os.makedirs(temp_dir, exist_ok=True)

            # 保存种子文件
            import asyncio
            saved_count = asyncio.run(seed_service.save_seeds(task_id, file_data))

            return {
                "task_id": task_id,
                "saved_count": saved_count,
                "message": f"成功上传 {saved_count} 个种子文件"
            }, 200

        except Exception as e:
            current_app.logger.error(f"种子文件上传失败: {e}")
            return {"error": str(e)}, 500
