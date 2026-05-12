# Appform SDK

Python SDK for Appform 6.0-6.6 HPC cluster management API.

## 功能特性

- 支持 Appform API 6.0、6.3、6.5、6.6 版本
- 三种认证方式：AccessKey 签名认证（6.4+）、密码登录、AES Token（仅集群）
- 完整的作业管理：提交、查询、停止、暂停、恢复、删除
- 会话管理：启动、连接、断开、关闭、共享
- 文件管理：上传、下载（支持目录递归）、压缩、解压，Linux 风格 CLI 命令
- 组织管理：部门和用户管理
- 可扩展的端点注册系统
- 支持通过 YAML 配置文件定义应用参数并提交作业（兼容 job_submit.py）
- 命令行工具（`appform` 和 `job_submit`），支持应用自定义短参数/长参数
- 支持 `job_submit --wait` 等待作业完成后退出
- Python 3.8 - 3.14

## 安装

```bash
# 从 whl 文件安装
pip install jhinno-appform-sdk-1.0.0-py3-none-any.whl

# 从源码安装
pip install .

# 开发模式
pip install -e ".[dev]"
```

**依赖项：**
- `requests>=2.28.0`（核心）
- `pycryptodome>=3.15.0`（AES 认证）
- `PyYAML>=5.0`（可选，用于 job profile 配置）

## 快速开始

### Python SDK 基础用法

```python
from appform_sdk import AppformClient

# 创建客户端（使用密码登录）
client = AppformClient(base_url="https://your-server", verify_ssl=False)
client.auth.login(username="your_username", password="your_password")

# 或使用配置文件自动认证（推荐）
# ~/.appform/config.json 中配置 base_url、username、password
client = AppformClient(base_url="https://your-server", verify_ssl=False)
# 如果 config.json 有 password，CLI 会自动登录
```

### 作业管理

```python
# 查询作业列表
result = client.jobs.list_jobs(page=1, page_size=20)
for job in result["data"]["jobs"]:
    print(f'{job["jobId"]} | {job["status"]} | {job["name"]}')

# 按状态过滤
result = client.jobs.list_jobs(status_filter=["RUN", "PEND"])

# 查询单个作业
job = client.jobs.get_job("241028")

# 批量查询
jobs = client.jobs.list_jobs_by_ids(["241028", "241029"])

# 提交作业
result = client.jobs.submit(
    app_id="lsdyna2",
    params={
        "JH_CAS": "/home/user/simulation.k",
        "JH_NCPU": "8",
        "JH_QUEUE": "debug",
    },
)
print(f'Job ID: {result["data"][0]["jobid"]}')

# 暂停 / 恢复 / 停止 / 终止
client.jobs.suspend("241028")
client.jobs.resume("241028")
client.jobs.stop("241028")      # 挂起，可 resume 恢复
client.jobs.kill("241028")      # 终止运行中的作业，不可恢复

# 获取作业输出和文件
output = client.jobs.get_output("241028")
files = client.jobs.get_files("241028")
history = client.jobs.get_history("241028")
```

### 会话管理

```python
# 列出所有会话（当前用户）
result = client.sessions.list_all()
# 分页查询
result = client.sessions.list(page=1, page_size=20)

# 按 ID 查询会话
result = client.sessions.list(session_ids=["494039"])

# 按名称查询会话
result = client.sessions.list(session_name="my_session")

# 启动会话
result = client.sessions.start(app_id="gedit", start_new=True, cwd="${HOME}")

# 连接 / 断开 / 关闭会话
client.sessions.connect("494039")
client.sessions.disconnect("494039")
client.sessions.close("494039")

# 共享会话
client.sessions.share("494039", usernames=["user1", "user2"])
```

### 文件管理

```python
# 列出文件
result = client.files.list(path="/home/user")
for f in result["data"]:
    print(f'{f["fileName"]} ({f["fileType"]})')

# 列出所有文件（自动翻页）
all_files = client.files.list_all(path="/home/user")

# 创建目录
client.files.mkdir(path="/home/user/new_folder", force=True)

# 上传文件
client.files.upload(file_path="/local/file.txt", remote_path="/home/user/")

# 上传整个目录（递归）
results = client.files.upload_directory(local_dir="/local/folder", remote_dir="/home/user/remote/")

# 下载文件
client.files.download(remote_path="/home/user/file.txt", local_path="/local/file.txt")

# 下载整个目录（递归）
results = client.files.download_directory(remote_dir="/home/user/folder", local_dir="/local/save_dir/")

# 重命名 / 复制 / 移动 / 删除
client.files.rename(old_path="/home/user/old.txt", new_name="new.txt")
client.files.copy(src_path="/home/user/file.txt", dest_dir="/home/user/backup/")
client.files.move(src_path="/home/user/file.txt", dest_dir="/home/user/backup/new_name.txt")
client.files.delete(path="/home/user/old.txt")

# 压缩 / 解压
client.files.compress(source_dir="/home/user/data", target_path="/home/user/data.tar.gz")
client.files.uncompress(archive_path="/home/user/data.tar.gz", dest_dir="/home/user/extracted/")
```

### 应用管理

```python
# 获取所有应用
apps = client.apps.list_all()
for app in apps["data"]:
    print(f'{app["id"]}: {app["name"]}')

# 获取应用 URL
url = client.apps.get_url("fluent")
```

### 组织管理

```python
# 获取部门树
deps = client.organization.get_departments()

# 获取用户列表
users = client.organization.get_users(page=1, page_size=20)

# 创建用户
client.organization.create_user(
    username="new_user",
    chusername="新用户",
    password="your_password",
)

# 修改密码
client.organization.reset_password("new_user", "new_password")
```

### 作业配置文件提交

使用 YAML 配置文件定义应用参数，自动填充默认值和参数校验：

```python
from appform_sdk import JobProfileManager, AppformClient

# 加载配置
pm = JobProfileManager("/path/to/job_submit.yaml")

# 列出所有已配置应用
for app in pm.list_apps():
    print(f'{app["app_id"]}: {app["name"]}')

# 查看应用参数
profile = pm.get_profile("starccm")
for p in profile.get_required_params():
    print(f'必填: {p.name} ({p.effective_cli_name}) - {p.description}')
for p in profile.get_optional_params():
    print(f'可选: {p.name} (默认: {p.default}) - {p.description}')

# 构建提交参数（自动填充默认值）
params = pm.build_submit_params("starccm", {
    "JH_CAS": "/home/user/simulation.sim",
    "JH_NCPU": "16",
})
# -> {'JH_CAS': '/home/user/simulation.sim', 'JH_NCPU': '16', 'JH_RELEASE': '16.02', ...}

# 提交
client = AppformClient(base_url="https://server", verify_ssl=False)
client.auth.login("your_username", "your_password")
result = pm.submit_job(client, "starccm", {
    "JH_CAS": "/home/user/simulation.sim",
    "JH_NCPU": "16",
})

# 参数校验
errors = profile.validate_params({"JH_CAS": "/path/to/file.txt"})
# -> ["Parameter JH_CAS='/path/to/file.txt' does not match pattern '^.*\\.(sim)$'"]
```

### 动态 API 调用

通过端点名称调用 API：

```python
# 注册自定义端点
client.register_endpoint(
    name="custom.myApi",
    path="/appform/ws/api/custom/endpoint",
    method="GET",
    description="My custom endpoint",
)

# 调用端点
result = client.call_endpoint("custom.myApi")

# 使用动态 API
result = client.api.call("jobs.list", params={"page": 1, "pageSize": 10})
```

### 版本管理

```python
from appform_sdk import AppformClient, VERSION_6_6

# 使用 6.6 版本（包含 V2 接口）
client = AppformClient(base_url="https://server", api_version="6.6")
# 可使用 client.jobs.submit_v2()、client.jobs.delete_job() 等 6.6+ 接口

# 查询端点
endpoints = client.registry.get_all()
for name, ep in endpoints.items():
    print(f'{name}: {ep.method} {ep.path}')
```

## 错误处理

```python
from appform_sdk import AppformClient, AuthenticationError, APIError, AppformError

try:
    client = AppformClient(base_url="https://server")
    client.auth.login(username="your_username", password="wrong_password")
except AuthenticationError as e:
    print(f"认证失败: {e}")
except APIError as e:
    print(f"API 错误: {e.message}, 状态码: {e.status_code}")
except AppformError as e:
    print(f"请求失败: {e}")
```

## 命令行工具

### appform CLI

```bash
# 配置认证
appform config set --base-url https://server
appform config set --username your_username --password your_password
appform config set --job-profile-config /path/to/job_submit.yaml

# 测试连接
appform auth ping

# 作业管理
appform jobs list
appform jobs list --status DONE
appform jobs list --job-id 241028
appform jobs get 241028
appform jobs status RUN

# 使用配置文件参数提交作业
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run
appform jobs submit -a starccm -i /path/to/file.sim -n 8 -r 20.02.007
appform jobs submit -a lsdyna2 -i /path/to/input.k -n 8 -q debug
appform jobs submit -a starccm --set JH_CAS=/file.sim --set JH_NCPU=8

# 查看应用参数
appform jobs apps
appform jobs params starccm
appform jobs submit -a starccm --help

# 会话管理
appform sessions list-all
appform sessions list --ids 494039
appform sessions start --app-id gedit --start-new --cwd ${HOME}

# 文件管理
appform files ls /home/user
appform files mkdir --path /home/user --name new_dir
appform files cat /home/user/file.txt --head 10
appform files tailf /home/user/output.log  # 实时跟踪文件输出 (SFTP)
appform files put ./local_file.txt /home/user/
appform files get /home/user/remote_file.txt
```

### job_submit 工具

完全兼容原 `job_submit.py` 参数格式，支持本地文件自动上传：

```bash
# 列出应用
job_submit -l

# 查看应用参数帮助
job_submit -a starccm -h

# 提交作业（文件在远程映射路径，无需上传）
job_submit -a starccm -i /apps/project/file.sim -n 8

# 提交作业（本地文件自动上传到 $HOME/<timestamp>/）
job_submit -a starccm -i /local/file.sim -n 8

# 指定上传目录
job_submit -a starccm -i /local/file.sim -n 8 --upload-path /projects/job_data

# 上传多个文件和目录
job_submit -a fluent -i /local/case.cas /local/data.dat /local/mesh_dir/ -n 32

# 提交并等待完成（默认每 10 分钟查询一次）
job_submit -a lsdyna2 -i /path/to/input.k -n 8 --wait

# 提交并等待完成（每 5 分钟查询一次）
job_submit -a lsdyna2 -i /path/to/input.k -n 8 --wait 5

# 使用用户名密码认证
job_submit -a starccm -i file.sim -n 8 -u your_username -p your_password
```

**文件上传规则：**
- `upload` 类型参数指定的文件，通过 `windows_disk_mapping` 目标路径判断是否已在远程
- 不在映射路径下的文件自动上传，上传后替换为远程路径
- 支持多个文件和目录
- 传输方式跟随 `APPFORM_DEFAULT_METHOD` 配置（http/sftp）

### xml2table 工具

从门户导出的应用包生成 SDK 配置文件：

```bash
# 扫描目录生成 YAML
python -m appform_sdk.xml2table -a -r -d . -o yaml

# 生成多种格式
python -m appform_sdk.xml2table -a -r -d . -o yaml,excel,csv
```

## 文档目录

- [配置管理](configuration.md) - 环境变量、配置文件、Config 类
- [认证方式](authentication.md) - AccessKey、密码、AES Token 认证
- [作业管理](jobs.md) - 作业提交、查询、操作
- [作业配置文件](job-profiles.md) - YAML 配置文件、应用参数、submit 命令详解
- [job_submit 快速开始](job-submit.md) - 作业提交工具快速参考，包含文件上传功能
- [会话管理](sessions.md) - 会话启动、连接、共享
- [文件管理](files.md) - 文件上传下载、压缩解压
- [应用管理](apps.md) - 应用列表和信息
- [组织管理](organization.md) - 部门和用户管理
- [扩展系统](extensions.md) - 自定义端点、版本管理、动态 API
- [XML 表单解析](xml2table.md) - 从门户导出包生成 SDK 配置文件
- [CLI 命令参考](cli.md) - 完整命令行工具文档
- [错误处理](error-handling.md) - 异常类型和最佳实践

## 许可证

MIT License
