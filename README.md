# AFL Fuzz 平台

基于 AFL 的二进制漏洞挖掘 Fuzz 平台，支持白盒测试（源代码插桩）和黑盒测试（QEMU 模式）。

## 功能特性

- 白盒测试：上传 C/C++ 源代码，使用 AFL 编译插桩进行测试
- 黑盒测试：上传 ELF 二进制文件，使用 QEMU 模式进行测试
- 自定义指令：支持自定义编译参数和 Fuzz 参数
- 实时监控：通过 WebSocket 实时推送任务状态和统计信息
- 任务管理：创建、启动、暂停、恢复、停止、删除 Fuzz 任务
- 结果分析：崩溃样本收集、覆盖率统计、报告导出
- 仪表盘：直观展示平台整体状态和任务进度

## 技术栈

### 前端
- Vue 3 (Composition API)
- Vue Router
- Pinia
- Element Plus
- Axios
- Socket.IO Client
- Vite

### 后端
- Flask 3.0
- Flask-RESTX (API 文档)
- Flask-CORS
- Flask-SocketIO (实时通信)
- Pydantic (数据验证)
- Eventlet (异步处理)

## 快速开始

### 使用 Docker 部署（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 本地开发

#### 后端开发

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --break-system-packages -r backend/requirements.txt

# 启动后端服务
cd backend
python3 run.py --host 0.0.0.0 --port 5000
```

#### 前端开发

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

## 安装 AFL

### Ubuntu 24.04

```bash
# 克隆 AFL 源码
git clone https://github.com/google/AFL.git /tmp/AFL
cd /tmp/AFL
make
sudo make install
```

## 目录结构

```
afl-fuzz-platform/
├── backend/                 # 后端服务
│   ├── api/                 # API 接口
│   ├── services/            # 业务逻辑
│   ├── config.py           # 配置文件
│   ├── models.py           # 数据模型
│   ├── app.py              # 应用入口
│   ├── websocket_events.py # WebSocket 事件处理
│   └── run.py             # 启动脚本
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── api/           # API 接口封装
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── utils/         # 工具函数
│   │   └── views/        # 页面组件
│   └── package.json
├── docker-compose.yml      # Docker 编排配置
├── Dockerfile.backend     # 后端镜像
├── Dockerfile.frontend    # 前端镜像
└── nginx.conf            # Nginx 配置
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

## 配置说明

### 后端配置 (backend/config.py)

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

### 前端配置 (frontend/vite.config.js)

```javascript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

## 开发说明

### 添加新的 API 接口

1. 在 `backend/api/` 目录下创建或修改 API 文件
2. 在 `backend/api/__init__.py` 中注册命名空间
3. 在前端 `frontend/src/api/` 中添加对应的接口封装

### 添加新的页面

1. 在 `frontend/src/views/` 目录下创建 Vue 组件
2. 在 `frontend/src/router/index.js` 中添加路由
3. 在 `frontend/src/App.vue` 中的导航菜单添加入口

## 许可证

MIT License
