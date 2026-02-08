#!/usr/bin/env python3
import os
import sys
import argparse


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="AFL Fuzz 平台后端服务")
    parser.add_argument("--host", default="0.0.0.0", help="主机地址")
    parser.add_argument("--port", type=int, default=5000, help="端口号")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    from app import app, socketio

    print("=" * 60)
    print(f"AFL Fuzz 平台后端服务")
    print(f"主机: {args.host}")
    print(f"端口: {args.port}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    print("=" * 60)

    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == "__main__":
    main()
