# AFL Fuzz 平台后端

基于 Flask + SocketIO 开发的 AFL Fuzz 平台后端服务。

## 功能特性

- 白盒测试：上传 C/C++ 源代码，使用 AFL 编译插桩进行测试
- 黑盒测试：上传 ELF 二进制文件，使用 QEMU 模式进行测试
- 实时监控：通过 WebSocket 实时推送任务状态和统计信息
- 任务管理：创建、启动、暂停、恢复、停止、删除 Fuzz 任务
- 结果分析：崩溃样本收集、覆盖率统计、报告导出

## 技术栈

- Flask 3.0
- Flask-RESTX (API 文档)
- Flask-CORS
- Flask-SocketIO (实时通信)
- Pydantic (数据验证)
- Eventlet (异步处理)

## 安装依赖

```bash
cd /workspace/backend
pip install --break-system-packages -r requirements.txt
```

## 安装 AFL

```bash
# 克隆 AFL 源码
git clone https://github.com/google/AFL.git /tmp/AFL
cd /tmp/AFL
make
sudo make install
```

## 运行服务

### 开发模式

```bash
python run.py --host 0.0.0.0 --port 5000 --debug
```

### 生产模式

```bash
python run.py --host 0.0.0.0 --port 5000
```

## API 接口说明

### 文件上传

#### 白盒测试上传
```
POST /api/upload/whitebox
Content-Type: multipart/form-data

参数:
- taskName: 任务名称
- mainFile: 主程序文件名
- compileArgs: 编译参数 (可选)
- fuzzArgs: Fuzz参数 (可选)
- inputType: 输入类型 (stdin/file/args)
- files[]: 源代码文件列表
```

#### 黑盒测试上传
```
POST /api/upload/blackbox
Content-Type: multipart/form-data

参数:
- taskName: 任务名称
- file: ELF 二进制文件
- inputType: 输入类型 (stdin/file/args)
- fuzzArgs: Fuzz参数 (可选)
- dependencies: 依赖库 (可选)
```

#### 种子文件上传
```
POST /api/upload/seeds
Content-Type: multipart/form-data

参数:
- taskId: 关联任务ID (可选)
- files[]: 种子文件列表
```

### 任务管理

```
GET    /api/tasks                    # 获取任务列表
GET    /api/tasks/:id               # 获取任务详情
POST   /api/tasks/:id/start         # 启动任务
POST   /api/tasks/:id/pause         # 暂停任务
POST   /api/tasks/:id/resume        # 恢复任务
POST   /api/tasks/:id/stop          # 停止任务
DELETE /api/tasks/:id               # 删除任务
GET    /api/tasks/:id/stats         # 获取任务统计
GET    /api/tasks/:id/crashes       # 获取崩溃样本
GET    /api/tasks/:id/corpus        # 获取语料库
```

### 结果分析

```
GET    /api/results/dashboard        # 获取仪表盘统计
GET    /api/results/crashes         # 获取崩溃列表
GET    /api/results/coverage        # 获取覆盖率报告
GET    /api/results/export          # 导出报告
```

## WebSocket 事件

### 客户端 -> 服务器

```
connect                        # 连接
disconnect                     # 断开连接
subscribe_task(task_id)        # 订阅任务
unsubscribe_task(task_id)     # 取消订阅
subscribe_dashboard            # 订阅仪表盘
ping                          # 心跳
```

### 服务器 -> 客户端

```
connected                     # 连接确认
task_update                   # 任务更新
dashboard_update              # 仪表盘更新
pong                         # 心跳响应
```

## 目录结构

```
backend/
├── api/
│   ├── __init__.py
│   ├── upload.py             # 上传相关API
│   ├── tasks.py              # 任务管理API
│   └── results.py            # 结果分析API
├── services/
│   ├── __init__.py
│   ├── task_manager.py       # 任务管理器
│   ├── monitoring.py         # 监控服务
│   └── compilation.py       # 编译和种子服务
├── config.py                # 配置文件
├── models.py                # 数据模型
├── app.py                   # 应用入口
├── websocket_events.py      # WebSocket 事件处理
├── run.py                   # 启动脚本
└── requirements.txt         # 依赖包
```

## 配置说明

在 `config.py` 中修改以下配置：

```python
# AFL 路径配置
afl_path: str = "/usr/local/bin/afl-fuzz"
afl_gcc_path: str = "/usr/local/bin/afl-gcc"
afl_gxx_path: str = "/usr/local/bin/afl-g++"

# 存储路径
upload_dir: str = "./uploads"
tasks_dir: str = "./tasks"
outputs_dir: str = "./outputs"
crashes_dir: str = "./crashes"
seeds_dir: str = "./seeds"

# 资源限制
max_file_size: int = 100 * 1024 * 1024  # 100MB
max_tasks: int = 10

# AFL 默认参数
default_timeout: int = 1000  # ms
```
