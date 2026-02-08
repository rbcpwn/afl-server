# AFL 配置适配脚本
# 用于将下载的 AFL-master.zip 中的 AFL 可执行文件配置到正确路径

AFL_DIR="/tmp/AFL-master"
LOCAL_AFL_DIR="/usr/local/bin/afl"

# AFL 可执行文件列表
AFL_BINS=(
    "afl-fuzz"
    "afl-gcc"
    "afl-g++"
    "afl-gotcpu"
    "afl-clang"
    "afl-clang++"
)

# 检查 AFL-master 是否有可执行文件
check_afl_master() {
    if [ ! -d "$AFL_DIR" ]; then
        echo "错误: AFL-master 目录不存在: $AFL_DIR"
        return 1
    fi

    echo "检查 AFL-master 目录中的可执行文件..."

    # 尝试构建 AFL 可执行文件
    cd "$AFL_DIR"

    # 检查 Makefile 是否存在
    if [ ! -f "Makefile" ]; then
        echo "AFL 源码中缺少 Makefile，跳过"
        return 1
    fi

    # 尝试构建
    echo "尝试构建 AFL..."
    make clean 2>/dev/null || true
    make 2>&1 | head -50

    # 检查构建结果
    local found_bins=0
    for bin in "${AFL_BINS[@]}"; do
        if [ -f "$bin" ]; then
            found_bins=$((found_bins + 1))
            echo "  找到: $bin"
        fi
    done

    if [ $found_bins -eq 0 ]; then
        echo "警告: 未找到任何 AFL 可执行文件"
        return 1
    fi

    return 0
}

# 创建符号链接
create_symlinks() {
    echo "创建 AFL 可执行文件的符号链接..."

    for bin in "${AFL_BINS[@]}"; do
        local src="$AFL_DIR/$bin"
        if [ -f "$src" ]; then
            ln -sf "$src" "$LOCAL_AFL_DIR/$bin"
            echo "  $src -> $LOCAL_AFL_DIR/$bin"
        else
            echo "  跳过: $src (不存在)"
        fi
    done

    echo "AFL 配置完成"
    return 0
}

# 主函数
main() {
    echo "==================================="
    echo "  AFL 配置适配"
    echo "==================================="
    echo ""

    if [ "$1" == "--check-only" ]; then
        check_afl_master
    else
        check_afl_master
        create_symlinks
    fi

    echo ""
    echo "可执行的 AFL 命令:"
    echo "  afl-fuzz    # 启动 fuzz"
    echo "  afl-gcc     # 编译插桩（白盒测试）"
    echo "  afl-g++     # 编译插桩（C++）"
    echo ""
    echo "检查 AFL 命令:"
    echo "  which afl-fuzz"
    echo "  afl-gcc --version"
}

main "$@"
