# 开发环境说明

## 快速开始

### 1. 首次环境搭建

```bash
# 一键搭建开发环境
bash setup.sh
```

该脚本会自动完成以下操作：
- 检查并安装 AFL
- 创建 Python 虚拟环境
- 安装后端依赖
- 创建必要的工作目录
- 检查 Node.js 版本
- 安装前端依赖

### 2. 启动服务

```bash
# 方式一：使用启动脚本（推荐）
bash start-dev.sh

# 方式二：直接指定启动模式
bash start-dev.sh all       # 启动后端和前端
bash start-dev.sh backend   # 仅启动后端
bash start-dev.sh frontend  # 仅启动前端
bash start-dev.sh status    # 查看服务状态
```

### 3. 停止服务

```bash
# 方式一：使用启动脚本菜单选择停止
bash start-dev.sh
# 选择 4) 停止所有服务

# 方式二：直接使用停止脚本
bash stop-dev.sh
```

## 手动启动方式

### 启动后端

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动后端
cd backend
python3 run.py --host 0.0.0.0 --port 5000
```

### 启动前端

```bash
cd frontend
npm run dev
```

## 目录说明

```
/workspace/
├── backend/              # 后端代码
│   ├── uploads/          # 上传文件临时目录
│   ├── tasks/           # 任务文件目录
│   ├── outputs/         # AFL 输出目录
│   ├── crashes/         # 崩溃样本目录
│   ├── seeds/           # 种子文件目录
│   └── backend.log      # 后端日志文件
├── frontend/             # 前端代码
│   └── frontend.log     # 前端日志文件
├── venv/                # Python 虚拟环境
├── setup.sh             # 环境搭建脚本
├── start-dev.sh         # 服务启动脚本
└── stop-dev.sh          # 服务停止脚本
```

## 服务地址

启动成功后，可通过以下地址访问：

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:5000 |
| API 文档 | http://localhost:5000/ |
| WebSocket | ws://localhost:5000/socket.io/ |

## 查看日志

```bash
# 查看后端日志
tail -f backend/backend.log

# 查看前端日志
tail -f frontend/frontend.log

# 同时查看两个日志
tail -f backend/backend.log frontend/frontend.log
```

## 常见问题

### 1. AFL 安装失败

如果 AFL 安装失败，可以手动安装：

```bash
sudo apt-get install -y build-essential
git clone https://github.com/google/AFL.git /tmp/AFL
cd /tmp/AFL
make
sudo make install
```

### 2. 端口被占用

如果端口 5000 或 5173 被占用，可以修改配置：

```bash
# 后端端口
cd backend
python3 run.py --host 0.0.0.0 --port 5001

# 前端端口
cd frontend
npm run dev -- --port 5174
```

### 3. 虚拟环境激活失败

确保使用 bash 或 zsh：

```bash
bash setup.sh
source venv/bin/activate
```

### 4. 前端依赖安装失败

使用国内镜像加速：

```bash
cd frontend
npm config set registry https://registry.npmmirror.com
npm install
```

## 重置环境

如果需要完全重置环境：

```bash
# 停止服务
bash stop-dev.sh

# 删除虚拟环境
rm -rf venv

# 删除 node_modules
rm -rf frontend/node_modules

# 重新搭建
bash setup.sh
```
