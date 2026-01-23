#!/usr/bin/env python3
"""
多 Python 版本测试脚本
手动解压 zip 包并测试各版本
"""

import os
import sys
import subprocess
import shutil
import tempfile
import zipfile

# 配置
PACKAGE_ZIP = "dist/psycounvdb-2.9.11-linux-x86_64-python3.8~3.13(1).zip"
PYENV_ROOT = os.path.expanduser("~/.pyenv")

# 数据库配置
DB_CONFIG = {
    'host': '192.168.4.13',
    'port': 5434,
    'database': 'postgres',
    'user': 'root',
    'password': 'root'
}

def get_python_versions():
    """获取所有可用的 Python 版本"""
    versions = []
    
    # system python
    versions.append(("system", "/usr/local/python3.8/bin/python3"))
    
    # pyenv versions
    pyenv_versions_dir = os.path.join(PYENV_ROOT, "versions")
    if os.path.exists(pyenv_versions_dir):
        for v in os.listdir(pyenv_versions_dir):
            python_path = os.path.join(pyenv_versions_dir, v, "bin", "python")
            if os.path.exists(python_path):
                versions.append((v, python_path))
    
    return versions

def test_version(version_name, python_path):
    """测试单个 Python 版本"""
    print(f"\n{'='*50}")
    print(f"测试 Python {version_name}")
    print(f"路径: {python_path}")
    print('='*50)
    
    # 获取版本信息
    try:
        result = subprocess.run([python_path, "--version"], capture_output=True, text=True)
        py_version = result.stdout.strip() or result.stderr.strip()
        print(f"版本: {py_version}")
    except Exception as e:
        print(f"✗ 无法获取版本: {e}")
        return "获取版本失败"
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix=f"test_{version_name}_")
    venv_dir = os.path.join(temp_dir, "venv")
    
    try:
        # 创建虚拟环境
        print("创建虚拟环境...")
        result = subprocess.run([python_path, "-m", "venv", venv_dir], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ 创建虚拟环境失败: {result.stderr}")
            return "venv失败"
        
        # 虚拟环境中的 python
        if sys.platform == "win32":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")
        
        # 解压包到虚拟环境的 site-packages
        print("安装 psycounvdb...")
        site_packages = subprocess.run(
            [venv_python, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True, text=True
        ).stdout.strip()
        
        with zipfile.ZipFile(PACKAGE_ZIP, 'r') as zf:
            zf.extractall(site_packages)
        
        # 测试导入
        print("测试导入...")
        result = subprocess.run(
            [venv_python, "-c", 
             "import psycounvdb; print(f'psycounvdb 版本: {psycounvdb.__version__}'); "
             "print(f'libpq 版本: {psycounvdb.__libpq_version__}')"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"✗ 导入失败: {result.stderr}")
            return "导入失败"
        print(result.stdout.strip())
        
        # 测试数据库连接
        print("测试数据库连接...")
        test_code = f'''
import psycounvdb
try:
    conn = psycounvdb.connect(
        host="{DB_CONFIG['host']}",
        port={DB_CONFIG['port']},
        database="{DB_CONFIG['database']}",
        user="{DB_CONFIG['user']}",
        password="{DB_CONFIG['password']}"
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"数据库版本: {{version[:50]}}...")
    cur.close()
    conn.close()
    print("✓ 连接成功")
except Exception as e:
    print(f"✗ 连接失败: {{e}}")
    exit(1)
'''
        result = subprocess.run([venv_python, "-c", test_code],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(f"✗ 连接失败: {result.stderr}")
            return "连接失败"
        print(result.stdout.strip())
        
        return "✓ 通过"
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return f"异常: {e}"
    finally:
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("="*60)
    print("psycounvdb 多 Python 版本测试")
    print("="*60)
    
    if not os.path.exists(PACKAGE_ZIP):
        print(f"错误: 找不到包文件 {PACKAGE_ZIP}")
        sys.exit(1)
    
    versions = get_python_versions()
    print(f"\n发现 {len(versions)} 个 Python 版本")
    
    results = {}
    for version_name, python_path in versions:
        results[version_name] = test_version(version_name, python_path)
    
    # 输出汇总
    print("\n")
    print("="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"| {'Python 版本':<15} | {'测试结果':<20} |")
    print(f"|{'-'*17}|{'-'*22}|")
    for version_name, result in results.items():
        print(f"| {version_name:<15} | {result:<20} |")
    print("="*60)
    
    # 统计
    passed = sum(1 for r in results.values() if r == "✓ 通过")
    print(f"\n通过: {passed}/{len(results)}")

if __name__ == "__main__":
    main()
