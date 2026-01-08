# psycounvdb 使用说明

psycounvdb 是 psycopg2 的预编译二进制包，支持连接 PostgreSQL 兼容数据库（如 UNVDB）。

## 下载

从 GitHub Actions 的 Artifacts 下载对应平台的 zip 包：

### Linux (CentOS 8+ / glibc 2.28+)
- `psycounvdb-2.9.11-linux-x86_64-glibc228-python3.8~3.13.zip` - Linux x86_64
- `psycounvdb-2.9.11-linux-aarch64-glibc228-python3.8~3.13.zip` - Linux ARM64

### Linux (CentOS 7 / glibc 2.17+)
- `psycounvdb-2.9.11-linux-x86_64-glibc217-python3.8~3.12.zip` - Linux x86_64 (兼容 CentOS 7)
- `psycounvdb-2.9.11-linux-aarch64-glibc217-python3.8~3.12.zip` - Linux ARM64 (兼容 CentOS 7)

> 注意：Python 3.13 需要 glibc 2.28+，因此 CentOS 7 包不支持 Python 3.13

### Windows
- `psycounvdb-2.9.11-windows-amd64-python3.8~3.13.zip` - Windows x64

## 安装

### Linux

```bash
# 解压到 site-packages
unzip psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip
cp -r psycounvdb psycounvdb_binary.libs /path/to/your/python/site-packages/

# 或者解压到项目目录，确保在 Python 路径中
unzip psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip -d /your/project/
```

### Windows

```powershell
# 解压 zip 文件
Expand-Archive psycounvdb-2.9.11-windows-amd64-python3.8~3.13.zip -DestinationPath .

# 复制到 site-packages
Copy-Item -Recurse psycounvdb, psycounvdb.libs C:\Python3x\Lib\site-packages\

# 或者添加 DLL 目录到 PATH
$env:PATH = "$PWD\psycounvdb.libs;$env:PATH"
```

## 使用示例

```python
import psycounvdb

# 连接数据库
conn = psycounvdb.connect(
    host="localhost",
    port=5432,
    database="mydb",
    user="myuser",
    password="mypassword"
)

# 执行查询
cur = conn.cursor()
cur.execute("SELECT version()")
print(cur.fetchone())

# 关闭连接
cur.close()
conn.close()
```

## 与 psycopg2 的兼容性

psycounvdb 的 API 与 psycopg2 完全兼容。如果你的代码使用 psycopg2，只需修改 import：

```python
# 原来
import psycopg2
conn = psycopg2.connect(...)

# 改为
import psycounvdb
conn = psycounvdb.connect(...)
```

## 目录结构

解压后的文件结构：

```
psycounvdb/                    # Python 模块
├── __init__.py
├── _psycopg.cpython-3x-*.so   # Linux 原生扩展 (多个 Python 版本)
├── _psycopg.cp3x-*.pyd        # Windows 原生扩展 (多个 Python 版本)
├── extensions.py
├── extras.py
├── sql.py
└── ...

psycounvdb_binary.libs/        # Linux 依赖库
├── libpq-*.so
├── libssl-*.so
└── libcrypto-*.so

psycounvdb.libs/               # Windows 依赖库
├── libpq.dll
├── libssl-3-x64.dll
├── libcrypto-3-x64.dll
└── ...
```

## 支持的 Python 版本

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## 支持的平台

- Linux x86_64 (glibc 2.28+, CentOS 8+)
- Linux x86_64 (glibc 2.17+, CentOS 7+)
- Linux aarch64 (glibc 2.28+, CentOS 8+)
- Linux aarch64 (glibc 2.17+, CentOS 7+)
- Windows x64

## 常见问题

### Linux: 找不到共享库

确保 `psycounvdb_binary.libs` 目录与 `psycounvdb` 在同一位置，或设置 `LD_LIBRARY_PATH`：

```bash
export LD_LIBRARY_PATH=/path/to/psycounvdb_binary.libs:$LD_LIBRARY_PATH
```

### Windows: DLL 加载失败

确保 `psycounvdb.libs` 目录中的 DLL 可被找到：

```python
import os
os.add_dll_directory(r"C:\path\to\psycounvdb.libs")
import psycounvdb
```

或将 DLL 目录添加到系统 PATH。
