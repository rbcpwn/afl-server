# API 模块初始化
from api.upload import api as upload_api
from api.tasks import api as tasks_api
from api.results import api as results_api

__all__ = [
    "upload_api",
    "tasks_api",
    "results_api",
]
