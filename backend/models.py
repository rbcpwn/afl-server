from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    WHITEBOX = "whitebox"
    BLACKBOX = "blackbox"


class TaskStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPILING = "compiling"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class InputType(str, Enum):
    STDIN = "stdin"
    FILE = "file"
    ARGS = "args"


class CreateWhiteboxTaskRequest(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    compile_args: str = Field(default="", description="编译参数")
    fuzz_args: str = Field(default="", description="Fuzz参数")
    input_type: InputType = Field(default=InputType.STDIN, description="输入类型")


class CreateBlackboxTaskRequest(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    input_type: InputType = Field(default=InputType.STDIN, description="输入类型")
    fuzz_args: str = Field(default="", description="Fuzz参数")
    dependencies: str = Field(default="", description="依赖库")


class Task(BaseModel):
    id: int
    name: str
    type: TaskType
    status: TaskStatus
    input_type: InputType
    compile_args: Optional[str] = None
    fuzz_args: str = ""
    dependencies: Optional[str] = None
    target_binary: Optional[str] = None
    source_files: List[str] = []
    elf_file: Optional[str] = None
    seeds_dir: Optional[str] = None
    output_dir: Optional[str] = None

    # 统计数据
    exec_count: int = 0
    unique_crashes: int = 0
    unique_hangs: int = 0
    total_execs: int = 0
    execs_per_sec: float = 0.0
    corpus_count: int = 0
    coverage: float = 0.0
    edges_found: int = 0

    # 时间信息
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime

    # 进程信息
    pid: Optional[int] = None
    fuzzer_count: int = 1

    # 错误信息
    error_message: Optional[str] = None


class TaskCreateResponse(BaseModel):
    task_id: int
    task_name: str
    message: str


class TaskListResponse(BaseModel):
    tasks: List[Task]
    total: int


class FuzzStats(BaseModel):
    task_id: int
    status: TaskStatus

    # AFL 统计
    exec_count: int
    unique_crashes: int
    unique_hangs: int
    total_execs: int
    execs_per_sec: float
    corpus_count: int
    edges_found: int
    edges_total: int

    # 覆盖率
    coverage: float

    # 时间
    run_time: str
    last_update: datetime


class CrashInfo(BaseModel):
    crash_id: str
    task_id: int
    task_name: str
    crash_type: str
    signal: str
    reproducible: bool
    severity: int
    sample_file: str
    stack_trace: Optional[str] = None
    found_at: datetime


class DashboardStats(BaseModel):
    total_tasks: int
    running_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_crashes: int
    total_executions: int
    avg_coverage: float


class StartTaskRequest(BaseModel):
    fuzzer_count: int = Field(default=1, ge=1, le=10, description="Fuzzer实例数量")


class SeedUploadRequest(BaseModel):
    task_id: Optional[int] = Field(default=None, description="关联任务ID")


class SeedFile(BaseModel):
    id: int
    filename: str
    size: int
    task_id: Optional[int] = None
    uploaded_at: datetime
