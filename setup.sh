#!/bin/bash
# AFL Fuzz 平台本地环境搭建和启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

# Python 虚拟环境目录
VENV_DIR="${PROJECT_ROOT}/venv"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"

echo "=================================="
echo "  AFL Fuzz 平台环境搭建"
echo "=================================="

# 1. 检查 Python 版本
echo -e "${GREEN}[1/7]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}找到: ${PYTHON_VERSION}${NC}"

# 2. 检查并安装 AFL
echo -e "${GREEN}[2/7]${NC} 检查 AFL 工具..."
if ! command -v afl-fuzz &> /dev/null; then
    echo -e "${YELLOW}AFL 未安装，开始安装...${NC}"

    # 检查 git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}错误: 需要安装 git${NC}"
        sudo apt-get update && sudo apt-get install -y git
    fi

    # 安装编译工具
    echo "安装编译工具..."
    sudo apt-get update
    sudo apt-get install -y build-essential

    # 克隆并安装 AFL
    cd /tmp
    rm -rf AFL 2>/dev/null || true
    git clone https://github.com/google/AFL.git

    cd AFL
    make
    sudo make install

    # 检查 QEMU mode
    echo "检查 QEMU mode..."
    if [ -f "afl-qemu-trace" ]; then
        ./afl-qemu-trace/build_qemu_support.sh || echo "QEMU mode 构建失败，跳过"
    fi

    cd "${PROJECT_ROOT}"
    echo -e "${GREEN}AFL 安装完成${NC}"
else
    echo -e "${GREEN}AFL 已安装: $(which afl-fuzz)${NC}"
fi

# 3. 创建 Python 虚拟环境
echo -e "${GREEN}[3/7]${NC} 设置 Python 虚拟环境..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo -e "${GREEN}虚拟环境创建成功: ${VENV_DIR}${NC}"
else
    echo -e "${YELLOW}虚拟环境已存在: ${VENV_DIR}${NC}"
fi

# 激活虚拟环境
# shellcheck disable=SC1090
# shellcheck disable=SC1091
source "${VENV_ACTIVATE}"
echo -e "${GREEN}虚拟环境已激活${NC}"

# 4. 安装后端依赖
echo -e "${GREEN}[4/7]${NC} 安装后端 Python 依赖..."
cd "${BACKEND_DIR}"
pip install --break-system-packages -r requirements.txt
echo -e "${GREEN}后端依赖安装完成${NC}"

# 5. 创建必要的目录
echo -e "${GREEN}[5/7]${NC} 创建工作目录..."
for dir in "${BACKEND_DIR}/uploads" "${BACKEND_DIR}/tasks" \
            "${BACKEND_DIR}/outputs" "${BACKEND_DIR}/crashes" "${BACKEND_DIR}/seeds"; do
    if [ ! -d "${dir}" ]; then
        mkdir -p "${dir}"
        echo "创建目录: ${dir}"
    fi
done
echo -e "${GREEN}工作目录创建完成${NC}"

# 6. 检查 Node.js 和安装前端依赖
echo -e "${GREEN}[6/7]${NC} 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js${NC}"
    echo "请安装 Node.js:"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}找到: ${NODE_VERSION}${NC}"

cd "${FRONTEND_DIR}"
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
    echo -e "${GREEN}前端依赖安装完成${NC}"
else
    echo -e "${YELLOW}前端依赖已存在${NC}"
fi

# 7. 显示启动说明
echo -e "${GREEN}[7/7]${NC} 环境搭建完成！"
echo ""
echo "=================================="
echo "  启动服务"
echo "=================================="
echo ""
echo "使用以下命令启动服务："
echo ""
echo -e "${YELLOW}启动后端和前端:${NC}"
echo "  bash ${PROJECT_ROOT}/start-dev.sh"
echo ""
echo -e "${YELLOW}仅启动后端:${NC}"
echo "  cd ${BACKEND_DIR}"
echo "  source ${VENV_ACTIVATE}"
echo "  python3 run.py"
echo ""
echo -e "${YELLOW}仅启动前端:${NC}"
echo "  cd ${FRONTEND_DIR}"
echo "  npm run dev"
echo ""
echo "服务地址:"
echo "  后端 API: http://localhost:5000"
echo "  前端界面: http://localhost:5173"
echo "  API 文档: http://localhost:5000/"
echo ""
echo -e "${GREEN}环境搭建完成！${NC}"
