#!/usr/bin/env python3
"""
构建 psycounvdb 多 Python 版本包

从 psycopg2-binary 下载各版本的 wheel 包，提取 .so 文件和依赖库，
然后用本地的 psycounvdb Python 文件替换，生成最终的多版本包。
"""

import os
import sys
import shutil
import tempfile
import zipfile
import subprocess
import re
from pathlib import Path

# 配置
VERSION = "2.9.11"
PSYCOPG2_BINARY_VERSION = "2.9.10"  # PyPI 上的 psycopg2-binary 版本
PYTHON_VERSIONS = ["cp38", "cp39", "cp310", "cp311", "cp312", "cp313", "cp314"]
PLATFORM = "manylinux_2_17_x86_64.manylinux2014_x86_64"

def download_wheel(python_version, work_dir):
    """下载 psycopg2-binary wheel 包"""
    # 转换版本格式: cp38 -> 38, cp310 -> 310
    py_ver = python_version.replace("cp", "")
    
    # 检查是否已存在
    for f in work_dir.glob(f"psycopg2_binary-{PSYCOPG2_BINARY_VERSION}-{python_version}*.whl"):
        print(f"  已存在: {f.name}")
        return f
    
    print(f"  下载: psycopg2-binary {PSYCOPG2_BINARY_VERSION} for Python {py_ver}")
    
    # 使用 pip download
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "download",
            f"psycopg2-binary=={PSYCOPG2_BINARY_VERSION}",
            "--python-version", py_ver,
            "--platform", "manylinux_2_17_x86_64",
            "--only-binary=:all:",
            "-d", str(work_dir),
            "--no-deps"
        ], check=True, capture_output=True)
        
        # 查找下载的文件
        for f in work_dir.glob(f"psycopg2_binary-{PSYCOPG2_BINARY_VERSION}-{python_version}*.whl"):
            return f
    except subprocess.CalledProcessError as e:
        print(f"  下载失败: {e.stderr.decode()}")
        return None
    
    return None

def extract_so_files(wheel_path, output_dir, python_version):
    """从 wheel 包中提取 .so 文件 - 已废弃，改用本地编译的"""
    pass  # 不再使用，改用 copy_local_so_files

def copy_local_so_files(build_dir, output_dir):
    """复制本地编译的 .so 文件"""
    psycounvdb_dir = output_dir / 'psycounvdb'
    psycounvdb_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找所有本地编译的 .so 文件
    for build_subdir in build_dir.glob('lib.linux-*'):
        for so_file in build_subdir.glob('psycounvdb/_psycounvdb.cpython-*.so'):
            dest = psycounvdb_dir / so_file.name
            shutil.copy(so_file, dest)
            print(f"  复制本地 .so: {so_file.name}")

def extract_libs(wheel_path, output_dir):
    """从 wheel 包中提取依赖库"""
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        for name in zf.namelist():
            # 提取 psycopg2_binary.libs/ 目录
            if 'psycopg2_binary.libs/' in name or 'psycopg2.libs/' in name:
                content = zf.read(name)
                # 重命名为 psycounvdb_binary.libs/
                new_name = name.replace('psycopg2_binary.libs/', 'psycounvdb_binary.libs/')
                new_name = new_name.replace('psycopg2.libs/', 'psycounvdb_binary.libs/')
                output_path = output_dir / new_name
                if name.endswith('/'):
                    output_path.mkdir(parents=True, exist_ok=True)
                else:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(content)

def copy_python_files(lib_dir, output_dir):
    """复制本地的 Python 文件"""
    psycounvdb_dir = output_dir / 'psycounvdb'
    psycounvdb_dir.mkdir(parents=True, exist_ok=True)
    
    for py_file in lib_dir.glob('*.py'):
        shutil.copy(py_file, psycounvdb_dir / py_file.name)
        print(f"  复制: psycounvdb/{py_file.name}")

def fix_so_rpath(output_dir):
    """修复 .so 文件的 rpath，指向 psycounvdb_binary.libs"""
    psycounvdb_dir = output_dir / 'psycounvdb'
    libs_dir = output_dir / 'psycounvdb_binary.libs'
    
    if not libs_dir.exists():
        print("  警告: 没有找到依赖库目录")
        return
    
    for so_file in psycounvdb_dir.glob('_psycounvdb.cpython-*.so'):
        try:
            # 使用 patchelf 修改 rpath
            subprocess.run([
                'patchelf', '--set-rpath', '$ORIGIN/../psycounvdb_binary.libs',
                str(so_file)
            ], check=True, capture_output=True)
            print(f"  修复 rpath: {so_file.name}")
        except FileNotFoundError:
            print("  警告: patchelf 未安装，跳过 rpath 修复")
            break
        except subprocess.CalledProcessError as e:
            print(f"  警告: 修复 rpath 失败: {e}")

def create_init_py(output_dir):
    """创建 __init__.py，支持从 psycounvdb_binary.libs 加载依赖"""
    init_content = '''"""psycounvdb - PostgreSQL database adapter for Python

This package provides a PostgreSQL database adapter compatible with psycopg2.
"""

import os
import sys

# 添加依赖库路径
_libs_dir = os.path.join(os.path.dirname(__file__), '..', 'psycounvdb_binary.libs')
if os.path.exists(_libs_dir):
    if sys.platform == 'linux':
        # Linux: 设置 LD_LIBRARY_PATH
        _ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        if _libs_dir not in _ld_path:
            os.environ['LD_LIBRARY_PATH'] = _libs_dir + ':' + _ld_path
    elif sys.platform == 'darwin':
        # macOS: 设置 DYLD_LIBRARY_PATH
        _dyld_path = os.environ.get('DYLD_LIBRARY_PATH', '')
        if _libs_dir not in _dyld_path:
            os.environ['DYLD_LIBRARY_PATH'] = _libs_dir + ':' + _dyld_path

# 导入核心模块
from psycounvdb._psycounvdb import (
    BINARY, NUMBER, STRING, DATETIME, ROWID,
    Binary, Date, Time, Timestamp,
    DateFromTicks, TimeFromTicks, TimestampFromTicks,
    Error, Warning, DataError, DatabaseError, ProgrammingError, IntegrityError,
    InterfaceError, InternalError, NotSupportedError, OperationalError,
    _connect, apilevel, threadsafety, paramstyle,
    __version__, __libpq_version__,
)

# 注册默认适配器
from psycounvdb import extensions as _ext
_ext.register_adapter(tuple, _ext.SQL_IN)
_ext.register_adapter(type(None), _ext.NoneAdapter)

# 注册 Decimal 适配器
from decimal import Decimal
from psycounvdb._psycounvdb import Decimal as Adapter
_ext.register_adapter(Decimal, Adapter)
del Decimal, Adapter


def connect(dsn=None, connection_factory=None, cursor_factory=None, **kwargs):
    """Create a new database connection."""
    kwasync = {}
    if 'async' in kwargs:
        kwasync['async'] = kwargs.pop('async')
    if 'async_' in kwargs:
        kwasync['async_'] = kwargs.pop('async_')

    dsn = _ext.make_dsn(dsn, **kwargs)
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
    if cursor_factory is not None:
        conn.cursor_factory = cursor_factory

    return conn
'''
    
    init_path = output_dir / 'psycounvdb' / '__init__.py'
    init_path.write_text(init_content)
    print("  创建: psycounvdb/__init__.py")

def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent
    lib_dir = project_dir / 'lib'
    dist_dir = project_dir / 'dist'
    
    print(f"=== 构建 psycounvdb {VERSION} 多版本包 ===")
    print(f"项目目录: {project_dir}")
    print(f"lib 目录: {lib_dir}")
    
    # 创建临时工作目录
    work_dir = Path(tempfile.mkdtemp(prefix='psycounvdb_build_'))
    output_dir = work_dir / 'package'
    output_dir.mkdir()
    
    print(f"工作目录: {work_dir}")
    
    try:
        # 1. 复制 Python 文件
        print("\n[1/5] 复制 Python 文件...")
        copy_python_files(lib_dir, output_dir)
        
        # 2. 复制本地编译的 .so 文件
        print("\n[2/5] 复制本地编译的 .so 文件...")
        build_dir = project_dir / 'build'
        if not build_dir.exists():
            print("错误: build 目录不存在，请先编译各 Python 版本")
            print("运行: python3.X setup.py build_ext --inplace 对每个版本")
            sys.exit(1)
        copy_local_so_files(build_dir, output_dir)
        
        # 检查是否有 .so 文件
        so_files = list((output_dir / 'psycounvdb').glob('_psycounvdb.cpython-*.so'))
        if not so_files:
            print("错误: 没有找到本地编译的 .so 文件")
            print("请先为各 Python 版本编译:")
            for pyver in PYTHON_VERSIONS:
                py_ver = pyver.replace('cp', '')
                print(f"  python{py_ver[0]}.{py_ver[1:]} setup.py build_ext --inplace")
            sys.exit(1)
        
        # 3. 下载 psycopg2-binary 获取依赖库
        print("\n[3/5] 下载 psycopg2-binary 获取依赖库...")
        wheels_dir = work_dir / 'wheels'
        wheels_dir.mkdir()
        
        # 只需要下载一个版本来获取依赖库
        wheel_path = download_wheel("cp38", wheels_dir)
        if not wheel_path:
            print("警告: 无法下载 psycopg2-binary，将不包含依赖库")
        
        # 4. 提取依赖库
        print("\n[4/5] 提取依赖库...")
        if wheel_path:
            extract_libs(wheel_path, output_dir)
        
        # 5. 修复 rpath
        print("\n[5/5] 修复 .so 文件 rpath...")
        fix_so_rpath(output_dir)
        
        # 创建 zip 包
        print("\n创建 zip 包...")
        py_min = PYTHON_VERSIONS[0].replace('cp', '')
        py_max = PYTHON_VERSIONS[-1].replace('cp', '')
        py_min_fmt = f"{py_min[0]}.{py_min[1:]}"
        py_max_fmt = f"{py_max[0]}.{py_max[1:]}"
        
        zip_name = f"psycounvdb-{VERSION}-linux-x86_64-python{py_min_fmt}~{py_max_fmt}.zip"
        zip_path = dist_dir / zip_name
        
        dist_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname)
        
        print(f"\n=== 构建完成 ===")
        print(f"输出: {zip_path}")
        print(f"\n包内容:")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in sorted(zf.namelist())[:20]:
                print(f"  {name}")
            if len(zf.namelist()) > 20:
                print(f"  ... 共 {len(zf.namelist())} 个文件")
        
    finally:
        # 清理
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == '__main__':
    main()
