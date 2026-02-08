#!/bin/bash
# 前端启动脚本

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

cd "${FRONTEND_DIR}" || exit 1

# 停止现有进程
if [ -f "${FRONTEND_PID_FILE}" ]; then
    FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
    if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
        kill "${FRONTEND_PID}"
        sleep 2
    fi
fi

# 启动前端
npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "${FRONTEND_PID}" > "${FRONTEND_PID_FILE}"

sleep 3

# 检查是否启动成功
if ps -p "${FRONTEND_PID}" > /dev/null 2>&1; then
    echo "前端服务启动成功 (PID: ${FRONTEND_PID})"
    echo "地址: http://localhost:5173"
    echo "日志: /tmp/frontend.log"
else
    echo "前端服务启动失败，请查看日志"
    cat /tmp/frontend.log
    exit 1
fi
