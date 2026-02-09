#!/bin/bash
# AFL Fuzz 平台一键启动脚本 - Ubuntu 24.04 适配版

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

# Python 虚拟环境（默认优先使用虚拟环境）
VENV_DIR="${PROJECT_ROOT}/venv"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"
USE_VENV=true
FORCE_NO_VENV=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            USE_VENV=false
            FORCE_NO_VENV=true
            echo -e "${YELLOW}已选择不使用虚拟环境${NC}"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# PID 文件
BACKEND_PID_FILE="${PROJECT_ROOT}/.backend.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

# ============================================
# AFL 安装函数
# ============================================
install_afl() {
    echo ""
    echo "=================================="
    echo "  安装 AFL 工具"
    echo "=================================="
    echo ""

    # 检查是否已安装
    if command -v afl-fuzz > /dev/null 2>&1; then
        echo -e "${GREEN}AFL 已安装: $(afl-fuzz 2>&1 | head -1)${NC}"
        return 0
    fi

    echo -e "${YELLOW}AFL 未安装，开始安装...${NC}"

    # 检查构建工具
    echo "检查构建工具..."
    if ! command -v make &> /dev/null; then
        echo -e "${RED}错误: 未找到 make${NC}"
        return 1
    fi

    # 解压 AFL 源码
    if [ -f "${PROJECT_ROOT}/AFL-master.zip" ]; then
        echo "从 AFL-master.zip 解压..."
        cd /tmp
        rm -rf AFL-master 2>/dev/null || true
        unzip -q "${PROJECT_ROOT}/AFL-master.zip"
        cd AFL-master
    else
        echo "从 GitHub 克隆 AFL..."
        cd /tmp
        rm -rf AFL 2>/dev/null || true
        if command -v git > /dev/null 2>&1; then
            git clone https://github.com/google/AFL.git
            cd AFL
        elif command -v wget > /dev/null 2>&1; then
            wget -q https://github.com/google/AFL/archive/refs/heads/master.zip -O AFL.zip
            unzip -q AFL.zip
            mv AFL-master AFL
            cd AFL
        elif command -v curl > /dev/null 2>&1; then
            curl -sL https://github.com/google/AFL/archive/refs/heads/master.zip -o AFL.zip
            unzip -q AFL.zip
            mv AFL-master AFL
            cd AFL
        else
            echo -e "${RED}错误: 未找到 git、wget 或 curl${NC}"
            return 1
        fi
    fi

    # 编译 AFL
    echo "编译 AFL..."
    make clean 2>/dev/null || true
    make

    # 安装 AFL
    echo "安装 AFL 到系统..."
    make install

    echo -e "${GREEN}AFL 安装完成${NC}"
    cd "${PROJECT_ROOT}"

    return 0
}

# ============================================
# Python 虚拟环境设置函数
# ============================================
setup_venv() {
    echo ""
    echo "=================================="
    echo "  设置 Python 虚拟环境"
    echo "=================================="
    echo ""

    # 如果强制不使用虚拟环境，直接使用系统 Python
    if [ "$FORCE_NO_VENV" = true ]; then
        echo -e "${YELLOW}强制使用系统 Python（跳过虚拟环境）${NC}"
        USE_VENV=false

        # 检查系统 Python 依赖
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "安装后端依赖到系统 Python..."
            pip install --break-system-packages -r "${BACKEND_DIR}/requirements.txt"
            echo -e "${GREEN}后端依赖安装完成${NC}"
        fi

        # 创建必要的目录
        for dir in "${BACKEND_DIR}/uploads" "${BACKEND_DIR}/tasks" \
                    "${BACKEND_DIR}/outputs" "${BACKEND_DIR}/crashes" "${BACKEND_DIR}/seeds"; do
            mkdir -p "${dir}"
        done
        echo -e "${GREEN}工作目录创建完成${NC}"
        return 0
    fi

    # 检查虚拟环境是否已存在
    if [ -d "${VENV_DIR}" ] && [ -f "${VENV_ACTIVATE}" ]; then
        echo -e "${GREEN}虚拟环境已存在: ${VENV_DIR}${NC}"
        USE_VENV=true
        return 0
    fi

    # 尝试创建虚拟环境
    echo "创建虚拟环境..."
    if python3 -m venv "${VENV_DIR}" 2>/dev/null; then
        echo -e "${GREEN}虚拟环境创建成功${NC}"

        # 激活虚拟环境并安装依赖
        source "${VENV_ACTIVATE}"
        echo "安装后端依赖..."
        pip install -r "${BACKEND_DIR}/requirements.txt"
        echo -e "${GREEN}后端依赖安装完成${NC}"

        # 创建必要的目录
        for dir in "${BACKEND_DIR}/uploads" "${BACKEND_DIR}/tasks" \
                    "${BACKEND_DIR}/outputs" "${BACKEND_DIR}/crashes" "${BACKEND_DIR}/seeds"; do
            mkdir -p "${dir}"
        done
        echo -e "${GREEN}工作目录创建完成${NC}"

        USE_VENV=true
        return 0
    else
        # 创建虚拟环境失败，使用系统 Python
        echo -e "${YELLOW}无法创建虚拟环境（可能需要安装 python3-venv）${NC}"
        echo -e "${YELLOW}将使用系统 Python${NC}"

        # 检查系统 Python 依赖
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "安装后端依赖到系统 Python..."
            pip install --break-system-packages -r "${BACKEND_DIR}/requirements.txt"
            echo -e "${GREEN}后端依赖安装完成${NC}"
        fi

        # 创建必要的目录
        for dir in "${BACKEND_DIR}/uploads" "${BACKEND_DIR}/tasks" \
                    "${BACKEND_DIR}/outputs" "${BACKEND_DIR}/crashes" "${BACKEND_DIR}/seeds"; do
            mkdir -p "${dir}"
        done
        echo -e "${GREEN}工作目录创建完成${NC}"

        USE_VENV=false
        return 0
    fi
}

# ============================================
# 前端依赖安装函数
# ============================================
setup_frontend() {
    echo ""
    echo "=================================="
    echo "  安装前端依赖"
    echo "=================================="
    echo ""

    if [ -d "${FRONTEND_DIR}/node_modules" ]; then
        echo -e "${YELLOW}前端依赖已存在${NC}"
        return 0
    fi

    echo "安装前端依赖..."
    cd "${FRONTEND_DIR}"
    npm install
    echo -e "${GREEN}前端依赖安装完成${NC}"

    return 0
}

# ============================================
# 环境检查函数
# ============================================
check_environment() {
    echo ""
    echo "=================================="
    echo "  环境检查"
    echo "=================================="
    echo ""

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3${NC}"
        exit 1
    fi
    echo -e "${GREEN}Python: $(python3 --version)${NC}"

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: 未找到 Node.js${NC}"
        exit 1
    fi
    echo -e "${GREEN}Node.js: $(node --version)${NC}"

    # 检查虚拟环境
    if [ "$FORCE_NO_VENV" = false ] && [ -d "${VENV_DIR}" ] && [ -f "${VENV_ACTIVATE}" ]; then
        echo -e "${GREEN}虚拟环境: 存在${NC}"
        USE_VENV=true
    elif [ "$FORCE_NO_VENV" = true ]; then
        echo -e "${YELLOW}虚拟环境: 已禁用（使用系统 Python）${NC}"
        USE_VENV=false
    else
        echo -e "${YELLOW}虚拟环境: 不存在或未完成${NC}"
        echo -e "${YELLOW}  将自动尝试创建虚拟环境${NC}"
    fi

    # 检查 AFL
    if ! command -v afl-fuzz > /dev/null 2>&1; then
        echo -e "${YELLOW}警告: AFL 未安装${NC}"
        echo "将会自动安装 AFL..."
    else
        echo -e "${GREEN}AFL: $(afl-fuzz 2>&1 | head -1)${NC}"
    fi

    return 0
}

# ============================================
# 停止服务函数
# ============================================
stop_services() {
    echo -e "${YELLOW}停止现有服务...${NC}"

    # 停止后端
    if [ -f "${BACKEND_PID_FILE}" ]; then
        BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
        if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
            echo "停止后端服务 (PID: ${BACKEND_PID})"
            kill "${BACKEND_PID}"
        fi
        rm -f "${BACKEND_PID_FILE}"
    fi

    # 停止前端
    if [ -f "${FRONTEND_PID_FILE}" ]; then
        FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
        if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
            echo "停止前端服务 (PID: ${FRONTEND_PID})"
            kill "${FRONTEND_PID}"
        fi
        rm -f "${FRONTEND_PID_FILE}"
    fi

    sleep 2
}

# ============================================
# 清理函数
# ============================================
cleanup() {
    echo ""
    echo -e "${YELLOW}正在关闭服务...${NC}"
    stop_services
    echo -e "${GREEN}服务已关闭${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# ============================================
# 启动后端函数
# ============================================
start_backend() {
    echo ""
    echo -e "${BLUE}==================================${NC}"
    echo -e "${BLUE}  启动后端服务${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo ""

    # 检查是否已运行
    if [ -f "${BACKEND_PID_FILE}" ]; then
        BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
        if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
            echo -e "${YELLOW}后端服务已在运行 (PID: ${BACKEND_PID})${NC}"
            return
        fi
    fi

    cd "${BACKEND_DIR}"

    # 激活虚拟环境（如果存在）
    if [ "$USE_VENV" = true ] && [ -f "${VENV_ACTIVATE}" ]; then
        source "${VENV_ACTIVATE}"
        echo -e "${GREEN}使用虚拟环境${NC}"
    else
        echo -e "${YELLOW}使用系统 Python${NC}"
    fi

    # 后台启动
    nohup python3 run.py --host 0.0.0.0 --port 5000 > "${BACKEND_DIR}/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "${BACKEND_PID}" > "${BACKEND_PID_FILE}"

    sleep 2

    # 检查是否启动成功
    if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
        echo -e "${GREEN}后端服务启动成功${NC}"
        echo "  PID: ${BACKEND_PID}"
        echo "  日志: ${BACKEND_DIR}/backend.log"
        echo "  地址: http://localhost:5000"
        echo ""
        echo "查看日志: tail -f ${BACKEND_DIR}/backend.log"
    else
        echo -e "${RED}后端服务启动失败，请查看日志${NC}"
        cat "${BACKEND_DIR}/backend.log"
        rm -f "${BACKEND_PID_FILE}"
        exit 1
    fi
}

# ============================================
# 启动前端函数
# ============================================
start_frontend() {
    echo ""
    echo -e "${BLUE}==================================${NC}"
    echo -e "${BLUE}  启动前端服务${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo ""

    # 检查是否已运行
    if [ -f "${FRONTEND_PID_FILE}" ]; then
        FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
        if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
            echo -e "${YELLOW}前端服务已在运行 (PID: ${FRONTEND_PID})${NC}"
            return
        fi
    fi

    cd "${FRONTEND_DIR}"

    # 后台启动
    nohup npm run dev > "${FRONTEND_DIR}/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "${FRONTEND_PID}" > "${FRONTEND_PID_FILE}"

    sleep 3

    # 检查是否启动成功
    if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
        echo -e "${GREEN}前端服务启动成功${NC}"
        echo "  PID: ${FRONTEND_PID}"
        echo "  日志: ${FRONTEND_DIR}/frontend.log"
        echo "  地址: http://localhost:5173"
        echo ""
        echo "查看日志: tail -f ${FRONTEND_DIR}/frontend.log"
    else
        echo -e "${RED}前端服务启动失败，请查看日志${NC}"
        cat "${FRONTEND_DIR}/frontend.log"
        rm -f "${FRONTEND_PID_FILE}"
        exit 1
    fi
}

# ============================================
# 显示服务状态函数
# ============================================
show_status() {
    echo ""
    echo "=================================="
    echo "  服务状态"
    echo "=================================="
    echo ""

    # 后端状态
    if [ -f "${BACKEND_PID_FILE}" ]; then
        BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
        if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
            echo -e "${GREEN}后端服务: 运行中 (PID: ${BACKEND_PID})${NC}"
        else
            echo -e "${RED}后端服务: 已停止 (残留 PID 文件)${NC}"
            rm -f "${BACKEND_PID_FILE}"
        fi
    else
        echo -e "${YELLOW}后端服务: 未运行${NC}"
    fi

    # 前端状态
    if [ -f "${FRONTEND_PID_FILE}" ]; then
        FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
        if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
            echo -e "${GREEN}前端服务: 运行中 (PID: ${FRONTEND_PID})${NC}"
        else
            echo -e "${RED}前端服务: 已停止 (残留 PID 文件)${NC}"
            rm -f "${FRONTEND_PID_FILE}"
        fi
    else
        echo -e "${YELLOW}前端服务: 未运行${NC}"
    fi

    echo ""
}

# ============================================
# 显示菜单函数
# ============================================
show_menu() {
    echo ""
    echo "=================================="
    echo "  AFL Fuzz 平台启动选项"
    echo "=================================="
    echo ""
    echo "  1) 一键启动 (推荐)"
    echo "  2) 一键启动（不使用虚拟环境）"
    echo "  3) 仅启动后端"
    echo "  4) 仅启动前端"
    echo "  5) 停止所有服务"
    echo "  6) 查看服务状态"
    echo "  7) 退出"
    echo ""
    read -p "请选择操作 [1-7]: " choice

    case $choice in
        1)
            start_all
            ;;
        2)
            FORCE_NO_VENV=true
            start_all
            ;;
        3)
            start_backend
            ;;
        4)
            start_frontend
            ;;
        5)
            stop_services
            show_menu
            ;;
        6)
            show_status
            show_menu
            ;;
        7)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重新输入${NC}"
            show_menu
            ;;
    esac
}

# ============================================
# 启动所有服务函数
# ============================================
start_all() {
    echo ""
    echo "=================================="
    echo "  AFL Fuzz 平台 - 一键启动"
    echo "=================================="

    # 环境检查
    check_environment

    # 安装 AFL（如果需要）
    if ! command -v afl-fuzz > /dev/null 2>&1; then
        install_afl
    fi

    # 设置虚拟环境（如果需要）
    if [ "$FORCE_NO_VENV" = false ] && ! ([ -d "${VENV_DIR}" ] && [ -f "${VENV_ACTIVATE}" ]); then
        setup_venv
    fi

    # 如果强制不使用虚拟环境，确保系统 Python 依赖已安装
    if [ "$FORCE_NO_VENV" = true ]; then
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "安装后端依赖到系统 Python..."
            pip install --break-system-packages -r "${BACKEND_DIR}/requirements.txt"
        fi
    fi

    # 安装前端依赖（如果需要）
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        setup_frontend
    fi

    echo ""

    # 先启动后端
    start_backend
    echo ""

    # 再启动前端
    start_frontend
    echo ""

    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}  所有服务已启动${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo ""
    echo "服务地址:"
    echo "  后端 API: http://localhost:5000"
    echo "  前端界面: http://localhost:5173"
    echo "  API 文档: http://localhost:5000/"
    echo ""
    echo "日志文件:"
    echo "  后端: ${BACKEND_DIR}/backend.log"
    echo "  前端: ${FRONTEND_DIR}/frontend.log"
    echo ""
    echo "查看所有日志:"
    echo "  tail -f ${BACKEND_DIR}/backend.log ${FRONTEND_DIR}/frontend.log"
    echo ""
    echo "停止服务: 按 Ctrl+C 或运行 bash ${PROJECT_ROOT}/one-click-start.sh stop"
    echo ""

    # 保持脚本运行
    wait
}

# ============================================
# 主函数
# ============================================
main() {
    if [ $# -eq 0 ]; then
        # 无参数，显示菜单
        show_menu
    else
        # 有参数，根据参数执行
        case $1 in
            start|all)
                start_all
                ;;
            --no-venv)
                FORCE_NO_VENV=true
                start_all
                ;;
            backend)
                check_environment
                if [ "$FORCE_NO_VENV" = false ] && ! ([ -d "${VENV_DIR}" ] && [ -f "${VENV_ACTIVATE}" ]); then
                    setup_venv
                fi
                start_backend
                ;;
            frontend)
                start_frontend
                ;;
            stop)
                stop_services
                ;;
            status)
                show_status
                ;;
            install-afl)
                install_afl
                ;;
            setup-venv)
                setup_venv
                ;;
            setup-frontend)
                setup_frontend
                ;;
            *)
                echo "用法: $0 [start|--no-venv|backend|frontend|stop|status|install-afl|setup-venv|setup-frontend]"
                echo ""
                echo "选项:"
                echo "  start         - 一键启动（推荐，使用虚拟环境）"
                echo "  --no-venv     - 一键启动，不使用虚拟环境"
                echo "  backend       - 仅启动后端"
                echo "  frontend      - 仅启动前端"
                echo "  stop         - 停止所有服务"
                echo "  status        - 查看服务状态"
                echo "  install-afl   - 安装 AFL 工具"
                echo "  setup-venv    - 设置 Python 虚拟环境"
                echo "  setup-frontend - 安装前端依赖"
                echo ""
                echo "不带参数则显示交互式菜单"
                ;;
        esac
    fi
}

# 执行主函数
main "$@"
