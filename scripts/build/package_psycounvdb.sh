#!/bin/bash
# 打包 psycounvdb 多版本包
# 从 psycounvdb wheel 提取模块，从 psycopg2-binary wheel 提取依赖库

set -euo pipefail

VERSION="${1:-2.9.11}"
OUTPUT_DIR="${2:-dist}"
WORK_DIR=$(mktemp -d)

trap "rm -rf ${WORK_DIR}" EXIT

echo "=== 打包 psycounvdb ${VERSION} ==="
echo "工作目录: ${WORK_DIR}"

# 创建输出目录
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${WORK_DIR}/package"

# 查找所有 psycounvdb wheel 包
PSYCOUNVDB_WHEELS=$(find . -name "psycounvdb-${VERSION}*.whl" -type f 2>/dev/null | grep -v psycopg2 || true)

if [ -z "$PSYCOUNVDB_WHEELS" ]; then
    echo "错误: 找不到 psycounvdb wheel 包"
    exit 1
fi

echo "找到的 psycounvdb wheels:"
echo "$PSYCOUNVDB_WHEELS"

# 解压所有 psycounvdb wheel
for wheel in $PSYCOUNVDB_WHEELS; do
    echo "解压: $wheel"
    unzip -q -o "$wheel" -d "${WORK_DIR}/package"
done

# 查找 psycopg2-binary wheel 获取依赖库
BINARY_WHEEL=$(find . -name "psycopg2_binary*.whl" -type f 2>/dev/null | head -1 || true)

if [ -n "$BINARY_WHEEL" ]; then
    echo "从 psycopg2-binary 提取依赖库: $BINARY_WHEEL"
    BINARY_DIR="${WORK_DIR}/binary"
    mkdir -p "$BINARY_DIR"
    unzip -q "$BINARY_WHEEL" -d "$BINARY_DIR"
    
    # 复制依赖库目录，重命名为 psycounvdb.libs
    if [ -d "$BINARY_DIR/psycopg2_binary.libs" ]; then
        cp -r "$BINARY_DIR/psycopg2_binary.libs" "${WORK_DIR}/package/psycounvdb.libs"
        echo "已复制依赖库到 psycounvdb.libs"
    fi
fi

# 删除不需要的目录
rm -rf "${WORK_DIR}/package/psycopg2" 2>/dev/null || true
rm -rf "${WORK_DIR}/package/psycopg2_binary.libs" 2>/dev/null || true
rm -rf "${WORK_DIR}/package/"*.dist-info 2>/dev/null || true

# 创建简单的 __init__.py 如果不存在
if [ ! -f "${WORK_DIR}/package/psycounvdb/__init__.py" ]; then
    echo "from psycounvdb._psycounvdb import *" > "${WORK_DIR}/package/psycounvdb/__init__.py"
fi

# 列出包内容
echo ""
echo "包内容:"
find "${WORK_DIR}/package" -type f | head -30

# 确定 Python 版本范围
PY_VERSIONS=$(find "${WORK_DIR}/package/psycounvdb" -name "_psycounvdb.cpython-*.so" | \
    sed 's/.*cpython-\([0-9]*\).*/\1/' | sort -n | uniq)
PY_MIN=$(echo "$PY_VERSIONS" | head -1)
PY_MAX=$(echo "$PY_VERSIONS" | tail -1)

# 格式化版本号 38 -> 3.8
PY_MIN_FMT="${PY_MIN:0:1}.${PY_MIN:1}"
PY_MAX_FMT="${PY_MAX:0:1}.${PY_MAX:1}"

# 确定平台
PLATFORM="linux_x86_64"
if find "${WORK_DIR}/package" -name "*.so" | head -1 | grep -q aarch64; then
    PLATFORM="linux_aarch64"
fi

# 打包
ZIP_NAME="psycounvdb-${VERSION}-${PLATFORM}-python${PY_MIN_FMT}~${PY_MAX_FMT}.zip"
cd "${WORK_DIR}/package"
zip -r "${OUTPUT_DIR}/${ZIP_NAME}" .

echo ""
echo "=== 打包完成 ==="
echo "输出: ${OUTPUT_DIR}/${ZIP_NAME}"
echo ""
echo "包内容验证:"
unzip -l "${OUTPUT_DIR}/${ZIP_NAME}" | head -20
