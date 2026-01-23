# psycounvdb 使用说明

psycounvdb 是 psycopg2 的预编译二进制包，支持连接 PostgreSQL 兼容数据库（如 UNVDB）。

## 下载

从 GitHub Actions 的 Artifacts 下载对应平台的 zip 包：

### Linux (CentOS 8+ / glibc 2.28+)
- `psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip` - Linux x86_64
- `psycounvdb-2.9.11-linux-aarch64-python3.8~3.13.zip` - Linux ARM64

### Linux (CentOS 7 / glibc 2.17+)
- `psycounvdb-2.9.11-linux-x86_64-centos7-python3.8~3.12.zip` - Linux x86_64 (兼容 CentOS 7)
- `psycounvdb-2.9.11-linux-aarch64-centos7-python3.8~3.12.zip` - Linux ARM64 (兼容 CentOS 7)

> 注意：Python 3.13 需要 glibc 2.28+，因此 CentOS 7 包不支持 Python 3.13

### Windows
- `psycounvdb-2.9.11-windows-amd64-python3.8~3.13.zip` - Windows x64

## 安装

### 方式一：使用虚拟环境（推荐）

#### Linux / macOS

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 解压 psycounvdb 包
unzip psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip

# 复制到虚拟环境的 site-packages
cp -r psycounvdb psycounvdb.libs venv/lib/python3.*/site-packages/

# 验证安装
python -c "import psycounvdb; print(psycounvdb.__version__)"
```

#### Windows (PowerShell)

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 解压 psycounvdb 包
Expand-Archive psycounvdb-2.9.11-windows-amd64-python3.8~3.13.zip -DestinationPath .

# 复制到虚拟环境的 site-packages
Copy-Item -Recurse psycounvdb, psycounvdb.libs venv\Lib\site-packages\

# 验证安装
python -c "import psycounvdb; print(psycounvdb.__version__)"
```

#### Windows (CMD)

```cmd
:: 创建虚拟环境
python -m venv venv

:: 激活虚拟环境
venv\Scripts\activate.bat

:: 解压后复制到 site-packages
xcopy /E /I psycounvdb venv\Lib\site-packages\psycounvdb
xcopy /E /I psycounvdb.libs venv\Lib\site-packages\psycounvdb.libs

:: 验证安装
python -c "import psycounvdb; print(psycounvdb.__version__)"
```

### 方式二：直接安装到系统 Python

#### Linux

```bash
# 解压 psycounvdb 包
unzip psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip

# 复制到 site-packages
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
cp -r psycounvdb psycounvdb.libs $SITE_PACKAGES/

# 验证安装
python3 -c "import psycounvdb; print(psycounvdb.__version__)"
```

#### Windows

```powershell
# 解压 zip 文件
Expand-Archive psycounvdb-2.9.11-windows-amd64-python3.8~3.13.zip -DestinationPath .

# 复制到 site-packages
Copy-Item -Recurse psycounvdb, psycounvdb.libs C:\Python3x\Lib\site-packages\

# 或者添加 DLL 目录到 PATH
$env:PATH = "$PWD\psycounvdb.libs;$env:PATH"
```

### 方式三：使用 conda 环境

```bash
# 创建 conda 环境
conda create -n myenv python=3.11
conda activate myenv

# 获取 site-packages 路径
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")

# 解压并复制
unzip psycounvdb-2.9.11-linux-x86_64-python3.8~3.13.zip
cp -r psycounvdb psycounvdb.libs $SITE_PACKAGES/

# 验证安装
python -c "import psycounvdb; print(psycounvdb.__version__)"
```

## 使用示例

### 基本连接

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

### 使用连接字符串

```python
import psycounvdb

# 使用 DSN 连接字符串
conn = psycounvdb.connect("host=localhost port=5432 dbname=mydb user=myuser password=mypassword")

cur = conn.cursor()
cur.execute("SELECT current_database(), current_user")
db, user = cur.fetchone()
print(f"数据库: {db}, 用户: {user}")

cur.close()
conn.close()
```

### 使用 with 语句（自动关闭）

```python
import psycounvdb

with psycounvdb.connect(host="localhost", database="mydb", user="myuser", password="mypassword") as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users LIMIT 10")
        for row in cur:
            print(row)
```

### 参数化查询（防止 SQL 注入）

```python
import psycounvdb

conn = psycounvdb.connect(host="localhost", database="mydb", user="myuser", password="mypassword")
cur = conn.cursor()

# 使用 %s 占位符
cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
user = cur.fetchone()

# 使用命名参数
cur.execute("SELECT * FROM users WHERE name = %(name)s AND age > %(age)s", 
            {'name': 'Alice', 'age': 18})
users = cur.fetchall()

cur.close()
conn.close()
```

### 批量插入

```python
import psycounvdb

conn = psycounvdb.connect(host="localhost", database="mydb", user="myuser", password="mypassword")
cur = conn.cursor()

# 批量插入数据
data = [
    ('Alice', 25),
    ('Bob', 30),
    ('Charlie', 35)
]
cur.executemany("INSERT INTO users (name, age) VALUES (%s, %s)", data)
conn.commit()

cur.close()
conn.close()
```

### 查看版本信息

```python
import psycounvdb

print(f"psycounvdb 版本: {psycounvdb.__version__}")
print(f"libpq 版本: {psycounvdb.__libpq_version__}")
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

如果需要同时兼容两者：

```python
try:
    import psycounvdb as psycopg2
except ImportError:
    import psycopg2

conn = psycopg2.connect(...)
```

## 目录结构

解压后的文件结构：

```
psycounvdb/                    # Python 模块
├── __init__.py
├── _psycounvdb.cpython-3x-*.so   # Linux 原生扩展 (多个 Python 版本)
├── _psycounvdb.cp3x-*.pyd        # Windows 原生扩展 (多个 Python 版本)
├── extensions.py
├── extras.py
├── sql.py
├── pool.py
├── tz.py
├── errors.py
├── errorcodes.py
└── ...

psycounvdb.libs/        # Linux 依赖库
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

| 平台 | 架构 | glibc 要求 | 说明 |
|------|------|-----------|------|
| Linux | x86_64 | 2.28+ | CentOS 8+, Ubuntu 18.04+ |
| Linux | x86_64 | 2.17+ | CentOS 7+ (不支持 Python 3.13) |
| Linux | aarch64 | 2.28+ | CentOS 8+, Ubuntu 18.04+ |
| Linux | aarch64 | 2.17+ | CentOS 7+ (不支持 Python 3.13) |
| Windows | x64 | - | Windows 10+ |

## 常见问题

### Linux/Windows: 找不到共享库或 DLL

正常情况下，只要 `psycounvdb` 和 `psycounvdb.libs` 目录位于同一父目录（如 site-packages），库会**自动加载**，无需手动配置。

**如果遇到问题，请检查：**

1. 确保 `psycounvdb.libs` 目录与 `psycounvdb` 在同一位置（都在 site-packages 下）
2. 确保文件完整，没有丢失

**极少数特殊情况下的备用方案：**

Linux:
```bash
export LD_LIBRARY_PATH=/path/to/site-packages/psycounvdb.libs:$LD_LIBRARY_PATH
```

Windows:
```python
import os
os.add_dll_directory(r"C:\path\to\site-packages\psycounvdb.libs")
import psycounvdb
```

### 如何检查 glibc 版本

```bash
# 方法一
ldd --version

# 方法二
getconf GNU_LIBC_VERSION
```

### 虚拟环境中找不到模块

确保已正确激活虚拟环境，并将文件复制到正确的 site-packages 目录：

```bash
# 查看 site-packages 路径
python -c "import site; print(site.getsitepackages())"
```

### 连接超时

检查网络连接和防火墙设置，可以设置连接超时：

```python
conn = psycounvdb.connect(
    host="localhost",
    database="mydb",
    user="myuser",
    password="mypassword",
    connect_timeout=10  # 10秒超时
)
```
