#!/bin/bash
# AFL Fuzz 平台开发环境启动脚本

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

# Python 虚拟环境
VENV_DIR="${PROJECT_ROOT}/venv"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"

# PID 文件
BACKEND_PID_FILE="${PROJECT_ROOT}/.backend.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

# 停止现有服务
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

    # 等待进程完全退出
    sleep 2
}

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在关闭服务...${NC}"
    stop_services
    echo -e "${GREEN}服务已关闭${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 显示菜单
show_menu() {
    echo ""
    echo "=================================="
    echo "  AFL Fuzz 平台启动选项"
    echo "=================================="
    echo ""
    echo "  1) 启动后端 + 前端 (推荐)"
    echo "  2) 仅启动后端"
    echo "  3) 仅启动前端"
    echo "  4) 停止所有服务"
    echo "  5) 退出"
    echo ""
    read -p "请选择操作 [1-5]: " choice

    case $choice in
        1)
            start_all
            ;;
        2)
            start_backend
            ;;
        3)
            start_frontend
            ;;
        4)
            stop_services
            show_menu
            ;;
        5)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重新输入${NC}"
            show_menu
            ;;
    esac
}

# 检查环境
check_environment() {
    # 检查虚拟环境
    if [ ! -d "${VENV_DIR}" ]; then
        echo -e "${RED}错误: Python 虚拟环境不存在${NC}"
        echo "请先运行: bash ${PROJECT_ROOT}/setup.sh"
        exit 1
    fi

    # 检查 node_modules
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        echo -e "${RED}错误: 前端依赖未安装${NC}"
        echo "请先运行: bash ${PROJECT_ROOT}/setup.sh"
        exit 1
    fi
}

# 启动后端
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

    # 激活虚拟环境并启动
    # shellcheck disable=SC1090
    # shellcheck disable=SC1091
    source "${VENV_ACTIVATE}"

    cd "${BACKEND_DIR}"

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

# 启动前端
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

# 启动所有服务
start_all() {
    check_environment

    echo ""
    echo "=================================="
    echo "  AFL Fuzz 平台"
    echo "=================================="
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
    echo "停止服务:"
    echo "  bash ${PROJECT_ROOT}/start-dev.sh"
    echo "  或按 Ctrl+C"
    echo ""

    # 保持脚本运行
    wait
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        # 无参数，显示菜单
        show_menu
    else
        # 有参数，根据参数执行
        case $1 in
            all)
                start_all
                ;;
            backend)
                check_environment
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
            *)
                echo "用法: $0 [all|backend|frontend|stop|status]"
                echo ""
                echo "选项:"
                echo "  all       - 启动后端和前端"
                echo "  backend   - 仅启动后端"
                echo "  frontend  - 仅启动前端"
                echo "  stop      - 停止所有服务"
                echo "  status    - 查看服务状态"
                echo ""
                echo "不带参数则显示交互式菜单"
                ;;
        esac
    fi
}

# 显示服务状态
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

# 执行主函数
main "$@"
