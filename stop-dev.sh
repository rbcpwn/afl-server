#!/bin/bash
# 停止 AFL Fuzz 平台服务

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_PID_FILE="${PROJECT_ROOT}/.backend.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

echo "=================================="
echo "  停止 AFL Fuzz 平台"
echo "=================================="
echo ""

# 停止后端
if [ -f "${BACKEND_PID_FILE}" ]; then
    BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
    if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
        echo "停止后端服务 (PID: ${BACKEND_PID})..."
        kill "${BACKEND_PID}"
        sleep 2
        if ps -p "${BACKEND_PID}" > /dev/null 2>&1; then
            echo "强制停止后端服务..."
            kill -9 "${BACKEND_PID}"
        fi
        echo "后端服务已停止"
    else
        echo "后端服务未运行"
    fi
    rm -f "${BACKEND_PID_FILE}"
else
    echo "后端服务 PID 文件不存在"
fi

# 停止前端
if [ -f "${FRONTEND_PID_FILE}" ]; then
    FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
    if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
        echo "停止前端服务 (PID: ${FRONTEND_PID})..."
        kill "${FRONTEND_PID}"
        sleep 2
        if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
            echo "强制停止前端服务..."
            kill -9 "${FRONTEND_PID}"
        fi
        echo "前端服务已停止"
    else
        echo "前端服务未运行"
    fi
    rm -f "${FRONTEND_PID_FILE}"
else
    echo "前端服务 PID 文件不存在"
fi

echo ""
echo "所有服务已停止"
