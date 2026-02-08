import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AFL Fuzz Platform"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 5000

    # 存储路径
    base_dir: str = os.path.abspath(os.path.dirname(__file__))
    upload_dir: str = os.path.join(base_dir, "uploads")
    tasks_dir: str = os.path.join(base_dir, "tasks")
    outputs_dir: str = os.path.join(base_dir, "outputs")
    crashes_dir: str = os.path.join(base_dir, "crashes")
    seeds_dir: str = os.path.join(base_dir, "seeds")

    # AFL 配置
    afl_path: str = "/usr/local/bin/afl-fuzz"
    afl_gcc_path: str = "/usr/local/bin/afl-gcc"
    afl_gxx_path: str = "/usr/local/bin/afl-g++"
    qemu_mode: bool = True
    default_timeout: int = 1000  # ms

    # 资源限制
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_tasks: int = 10

    # CORS
    cors_origins: list = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 创建必要的目录
for dir_path in [
    settings.upload_dir,
    settings.tasks_dir,
    settings.outputs_dir,
    settings.crashes_dir,
    settings.seeds_dir,
]:
    os.makedirs(dir_path, exist_ok=True)
