#!/bin/bash
# 为所有 Python 版本编译 psycounvdb

set -e

PYENV_ROOT="${HOME}/.pyenv"
SYSTEM_PYTHON="/usr/local/python3.8/bin/python3"

echo "=== 编译 psycounvdb 各 Python 版本 ==="

# 清理旧的构建
rm -rf build/lib.linux-*

# System Python 3.8
if [ -x "$SYSTEM_PYTHON" ]; then
    echo ""
    echo "编译 System Python 3.8..."
    $SYSTEM_PYTHON setup.py build_ext
fi

# pyenv 版本
if [ -d "$PYENV_ROOT/versions" ]; then
    for version_dir in "$PYENV_ROOT/versions"/*; do
        if [ -d "$version_dir" ]; then
            python_bin="$version_dir/bin/python"
            if [ -x "$python_bin" ]; then
                version=$(basename "$version_dir")
                echo ""
                echo "编译 Python $version..."
                $python_bin setup.py build_ext || echo "  跳过 $version (编译失败)"
            fi
        fi
    done
fi

echo ""
echo "=== 编译完成 ==="
echo "生成的 .so 文件:"
find build -name "_psycounvdb.cpython-*.so" -type f 2>/dev/null
