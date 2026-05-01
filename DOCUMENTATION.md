# Appform SDK 使用文档

## 目录

- [概述](#概述)
- [安装](#安装)
- [快速开始](#快速开始)
- [配置管理](#配置管理)
- [认证方式](#认证方式)
- [API 版本管理](#api-版本管理)
- [作业管理](#作业管理)
- [会话管理](#会话管理)
- [文件管理](#文件管理)
- [应用管理](#应用管理)
- [组织管理](#组织管理)
- [系统接口](#系统接口)
- [扩展系统](#扩展系统)
- [命令行工具](#命令行工具)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [API 参考](#api-参考)

---

## 概述

Appform SDK 是 Appform 6.0-6.6 API 的 Python 客户端库，提供：

- 支持 Appform 6.0、6.2、6.3、6.4、6.5、6.6 版本
- 多种认证方式（密码、Token、AccessKey）
- 完整的 API 覆盖（作业、会话、文件、组织等）
- 命令行工具支持
- 可扩展的端点注册系统
- 版本感知的接口管理

### 支持的版本

| 版本 | 说明 | 新增功能 |
|------|------|---------|
| 6.0 | 基础版本 | 核心作业、会话、文件、组织 API |
| 6.2 | - | 与 6.0 相同 |
| 6.3 | - | 与 6.0 相同 |
| 6.4 | - | 与 6.0 相同 |
| 6.5 | 功能增强 | 文件密级管理 |
| 6.6 | 重大更新 | V2 API、存储配额、CPU 统计 |

---

## 安装

### 使用 pip 安装

```bash
pip install appform-sdk
```

### 从源码安装

```bash
git clone https://github.com/YUTIAN0/jhinno-appform-sdk.git
cd appform-sdk
pip install -e .
```

### 依赖项

```
requests>=2.28.0
pycryptodome>=3.15.0
```

### Python 版本支持

- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

---

## 快速开始

### 基本使用

```python
from appform_sdk import AppformClient

# 创建客户端
client = AppformClient(
    base_url="https://your-appform-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# 测试连接
result = client.auth.ping()
print(f"连接状态: {result['message']}")

# 列出作业
jobs = client.jobs.list_jobs(page=1, page_size=10)
for job in jobs['data']['content']:
    print(f"作业: {job['name']}, 状态: {job['status']}")

# 关闭客户端
client.close()
```

### 使用上下文管理器

```python
from appform_sdk import AppformClient

with AppformClient(base_url="https://your-server.com") as client:
    client.auth.login(username="user", password="pass")
    jobs = client.jobs.list_jobs()
    # 自动关闭连接
```

### 从配置文件加载

```python
from appform_sdk import AppformClient, Config

# 自动加载 ~/.appform/config.json
config = Config()

client = AppformClient(
    base_url=config.base_url,
    access_key=config.access_key,
    access_key_secret=config.access_key_secret,
    username=config.username,
    api_version=config.api_version,
)
```

---

## 配置管理

### 配置优先级

配置按以下优先级加载（高优先级覆盖低优先级）：

1. 直接参数
2. 环境变量
3. 配置文件

### 环境变量

```bash
# 必需
export APPFORM_BASE_URL="https://your-appform-server.com"

# AccessKey 认证
export APPFORM_ACCESS_KEY="your_access_key"
export APPFORM_ACCESS_KEY_SECRET="your_access_key_secret"
export APPFORM_USERNAME="your_username"

# Token 认证
export APPFORM_TOKEN="your_token"

# 可选
export APPFORM_API_VERSION="6.6"
export APPFORM_TIMEOUT="30"
export APPFORM_VERIFY_SSL="false"
export APPFORM_EXTENSIONS_DIR="/path/to/extensions"
```

### 配置文件

配置文件路径：`~/.appform/config.json`

```json
{
  "base_url": "https://your-appform-server.com",
  "access_key": "your_access_key",
  "access_key_secret": "your_access_key_secret",
  "username": "your_username",
  "api_version": "6.6",
  "timeout": 30,
  "verify_ssl": false,
  "extensions_dir": "~/.appform/extensions"
}
```

### Config 类使用

```python
from appform_sdk import Config

# 从默认位置加载
config = Config()

# 从指定文件加载
config = Config(config_file="/path/to/config.json")

# 仅从环境变量加载
config = Config.from_env()

# 从文件加载
config = Config.from_file("/path/to/config.json")

# 保存配置
Config.save_config_file(
    base_url="https://your-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username",
    api_version="6.6",
    verify_ssl=False,
)

# 查看配置
print(config.to_dict())
```

---

## 认证方式

### 方式一：密码登录

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# 登录
result = client.auth.login(username="jhadmin", password="Letmein123")

if result["result"] == "success":
    print("登录成功")
    print(f"Token: {client.token}")
else:
    print(f"登录失败: {result['message']}")

# 登出
client.auth.logout()
```

### 方式二：Token 登录

使用加密的 Token 进行登录：

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# Token 登录（SDK 自动加密）
result = client.auth.login_with_token(username="jhadmin", timeout=60)
```

### 方式三：AccessKey 认证（推荐）

AccessKey 认证使用 HMAC-SHA256 签名，每次请求自动生成签名。

```python
from appform_sdk import AppformClient

# 初始化时配置
client = AppformClient(
    base_url="https://your-server.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# 或后续配置
client = AppformClient(base_url="https://your-server.com")
client.auth.login_with_access_key(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)
```

**请求头说明：**

每次请求自动发送以下头信息：
- `accessKey`: Access Key
- `username`: 用户名
- `signature`: HMAC-SHA256 签名
- `currentTimeMillis`: 当前时间戳（毫秒）

**注意：** `accessKeySecret` 仅用于签名生成，不会发送到服务器。

### 检查认证状态

```python
# 检查是否已认证
if client.auth.is_authenticated():
    print("已认证")

# 检查认证类型
if client.auth.is_access_key_authenticated():
    print("使用 AccessKey 认证")
elif client.auth.is_token_authenticated():
    print("使用 Token 认证")

# 测试连接
result = client.auth.ping()
print(f"连接状态: {result['message']}")
```

### 检查权限

```python
# 检查上传权限
if client.auth.has_upload_permission():
    print("有上传权限")

# 检查下载权限
if client.auth.has_download_permission():
    print("有下载权限")
```

### 手动生成签名

```python
from appform_sdk import SignatureGenerator

# 生成签名
signature, timestamp = SignatureGenerator.generate_signature(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)

# 生成完整认证头
headers = SignatureGenerator.generate_auth_headers(
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username"
)
# 返回: {"accessKey": ..., "signature": ..., "currentTimeMillis": ..., "username": ...}
```

---

## API 版本管理

### 设置版本

```python
from appform_sdk import AppformClient, VERSION_6_0, VERSION_6_5, VERSION_6_6

# 使用版本 6.0
client = AppformClient(base_url="...", api_version="6.0")

# 使用版本 6.5
client = AppformClient(base_url="...", api_version="6.5")

# 使用版本 6.6
client = AppformClient(base_url="...", api_version="6.6")

# 使用版本常量
client = AppformClient(base_url="...", api_version=VERSION_6_6)
```

### 版本差异

| 功能 | 6.0-6.4 | 6.5 | 6.6 |
|------|---------|-----|-----|
| 基础作业 API | ✓ | ✓ | ✓ |
| 基础会话 API | ✓ | ✓ | ✓ |
| 基础文件 API | ✓ | ✓ | ✓ |
| 组织管理 API | ✓ | ✓ | ✓ |
| 文件密级管理 | - | ✓ | ✓ |
| V2 作业 API | - | - | ✓ |
| V2 会话 API | - | - | ✓ |
| V2 应用 API | - | - | ✓ |
| 存储配额 | - | - | ✓ |
| CPU 统计 | - | - | ✓ |

### 版本特定接口

```python
# 6.5+ 文件密级
levels = client.call_endpoint("files.getConfidentiality")

# 6.6+ V2 接口
form = client.call_endpoint("jobs.getForm", path_params={"appId": "fluent"})
result = client.call_endpoint("jobs.submitV2", json_data={...})
jobs = client.call_endpoint("jobs.listV2", params={"page": 1})
client.call_endpoint("jobs.deleteV2", path_params={"jobId": "123"})
session = client.call_endpoint("sessions.startV2", json_data={...})
apps = client.call_endpoint("apps.listV2")
quota = client.call_endpoint("quota.storage")
cpu = client.call_endpoint("count.appsCpu", params={"appId": "fluent"})
```

---

## 作业管理

### 提交作业

#### 基础提交（6.0+）

```python
result = client.jobs.submit(
    app_name="fluent",
    job_name="my_simulation",
    queue="normal",
    cores=4,
    memory=8000,
    walltime="2:00:00",
    input_files=["/data/input.cas"],
    output_files=["/data/output.dat"],
    command="fluent 3d -t4",
)
print(f"作业 ID: {result['data']['jobId']}")
```

#### V2 提交（6.6+）

```python
# 1. 获取作业表单
form = client.call_endpoint("jobs.getForm", path_params={"appId": "fluent"})
print(f"表单字段: {form['data']}")

# 2. 根据表单提交作业
result = client.call_endpoint("jobs.submitV2", json_data={
    "appId": "fluent",
    "params": {
        "JH_CAS": "/home/user/jh.cas",
        "JH_NCPU": "4",
        "JH_ITERATION": "100",
        "JH_PROJECT": "default",
        "JH_RELEASE": "18.2",
        "JH_GUI_ENABLED": "off"
    }
})
```

### 查询作业

#### 分页查询

```python
# 基础查询
result = client.jobs.list_jobs(page=1, page_size=20)

# 带过滤条件
result = client.jobs.list_jobs(
    page=1,
    page_size=20,
    name_filter="fluent_",
    status_filter=["RUN", "PEND"],
    app_name_filter="fluent",
    queue_filter="normal",
)

# 遍历结果
for job in result["data"]["content"]:
    print(f"ID: {job['jobId']}")
    print(f"名称: {job['name']}")
    print(f"状态: {job['status']}")
    print(f"应用: {job['appName']}")
    print(f"队列: {job['queue']}")
    print(f"提交时间: {job['submitTime']}")
    print("---")

print(f"总数: {result['data']['totalElements']}")
```

#### 查询单个作业

```python
job = client.jobs.get_job(job_id="12345")
print(f"作业详情: {job['data']}")
```

#### 批量查询

```python
jobs = client.jobs.list_jobs_by_ids(job_ids=["123", "456", "789"])
for job in jobs["data"]:
    print(f"作业: {job['name']}")
```

#### 查询历史作业

```python
# 分页查询历史作业
history = client.jobs.list_history(page=1, page_size=20)

# 获取历史作业总数（6.6+）
total = client.call_endpoint("jobs.totalHistory")
print(f"历史作业总数: {total['data']}")
```

### 作业操作

```python
# 停止作业
client.jobs.stop(job_id="12345")

# 暂停作业
client.jobs.suspend(job_id="12345")

# 恢复作业
client.jobs.resume(job_id="12345")

# 重新排队
client.jobs.requeue(job_id="12345")

# 删除作业（6.6+）
client.call_endpoint("jobs.deleteV2", path_params={"jobId": "12345"})
```

### 批量操作

```python
# 批量停止
client.jobs.batch_stop(["job1", "job2", "job3"])

# 批量暂停
client.jobs.batch_suspend(["job1", "job2"])

# 批量恢复
client.jobs.batch_resume(["job1", "job2"])

# 批量重新排队
client.jobs.batch_requeue(["job1", "job2"])
```

### 获取作业输出

```python
# 获取作业动态输出
output = client.jobs.get_output(job_id="12345")
print(output["data"])

# 获取作业文件列表
files = client.jobs.get_files(job_id="12345")
for f in files["data"]:
    print(f"文件: {f['name']}, 大小: {f['size']}")

# 获取作业历史
history = client.jobs.get_history(job_id="12345")
```

### 连接作业图形

```python
result = client.jobs.connect(job_id="12345")
print(f"连接信息: {result['data']}")
```

### 作业监控（6.6+）

```python
info = client.call_endpoint("jobs.tooltip")
print(f"监控信息: {info['data']}")
```

---

## 会话管理

### 启动会话

#### 基础启动（6.0+）

```python
result = client.sessions.start(
    app_id="ansys",
    session_name="my_session",
    cores=2,
    memory=4000,
    queue="normal",
    walltime="1:00:00",
)
print(f"会话 ID: {result['data']['sessionId']}")
```

#### V2 启动（6.6+）

```python
result = client.call_endpoint("sessions.startV2", json_data={
    "appId": "ansys",
    "startNew": True,
    "cwd": "${HOME}",
    "workFile": "${HOME}/work/file.dat",
    "param": ""
})
# 返回客户端连接和 Web 连接
print(f"客户端连接: {result['data']['clientConnection']}")
print(f"Web 连接: {result['data']['webConnection']}")
```

### 查询会话

```python
# 查询所有会话
sessions = client.sessions.list_all()

# 分页查询
sessions = client.sessions.list(page=1, page_size=20)

for session in sessions["data"]:
    print(f"ID: {session['sessionId']}")
    print(f"应用: {session['appName']}")
    print(f"状态: {session['status']}")
```

### 会话操作

```python
# 连接会话
client.sessions.connect(session_id="session_123")

# 断开会话
client.sessions.disconnect(session_id="session_123")

# 批量断开
client.sessions.batch_disconnect(["session_1", "session_2"])

# 关闭会话
client.sessions.close(session_id="session_123")

# 批量关闭
client.sessions.batch_close(["session_1", "session_2"])

# Web 客户端连接
client.sessions.webclient_connect(session_id="session_123")
```

### 会话共享

```python
# 共享会话
client.sessions.share(
    session_id="session_123",
    usernames=["user1", "user2"]
)

# 取消共享
client.sessions.cancel_share(session_id="session_123")

# 转移操作权
client.sessions.transfer_operation(
    session_id="session_123",
    username="other_user"
)
```

---

## 文件管理

### 文件列表

```python
# 列出文件
result = client.files.list(path="/home/user/data")

for item in result["data"]:
    print(f"名称: {item['name']}")
    print(f"类型: {'目录' if item['isDirectory'] else '文件'}")
    print(f"大小: {item.get('size', 'N/A')}")
    print(f"修改时间: {item.get('modifyTime', 'N/A')}")
```

### 目录操作

```python
# 创建目录
client.files.mkdir(path="/home/user", name="new_folder")

# 获取根目录信息
root = client.files.get_root_dir()
print(f"根目录: {root['data']}")
```

### 文件操作

```python
# 重命名
client.files.rename(
    old_path="/home/user/old_name.txt",
    new_name="new_name.txt"
)

# 复制
client.files.copy(
    src_paths=["/home/user/file1.txt", "/home/user/file2.txt"],
    dest_path="/home/user/backup/"
)

# 删除
client.files.delete(paths=["/home/user/old_file.txt"])
```

### 上传下载

```python
# 上传文件
client.files.upload(
    file_path="/local/path/file.txt",
    remote_path="/home/user/data/"
)

# 下载文件（返回内容）
content = client.files.download(remote_path="/home/user/data/file.txt")

# 下载到本地文件
client.files.download(
    remote_path="/home/user/data/file.txt",
    local_path="/local/path/downloaded.txt"
)
```

### 压缩解压

```python
# 压缩
client.files.compress(
    paths=["/home/user/data/"],
    output_name="backup.zip",
    output_path="/home/user/"
)

# 解压
client.files.uncompress(
    archive_path="/home/user/backup.zip",
    dest_path="/home/user/extracted/"
)
```

### 文件密级（6.5+）

```python
# 获取可用密级
levels = client.call_endpoint("files.getConfidentiality")
print(f"可用密级: {levels['data']}")

# 设置文件密级
client.call_endpoint("files.setConfidentiality", json_data={
    "path": "/home/user/secret_file.txt",
    "level": "secret"
})
```

---

## 应用管理

### 获取应用列表

#### 基础列表（6.0+）

```python
apps = client.apps.list_all()
for app in apps["data"]:
    print(f"应用: {app['name']}")
```

#### V2 列表（6.6+）

```python
apps = client.call_endpoint("apps.listV2")
for app in apps["data"]:
    print(f"ID: {app['id']}")
    print(f"名称: {app['name']}")
    print(f"类型: {app['mode']}")
    print(f"系统: {app['os']}")
```

### 获取应用信息

```python
# 获取应用 URL
url = client.apps.get_url(app_name="fluent")
print(f"应用 URL: {url['data']}")

# 获取计算应用表单参数
params = client.apps.get_form_params(app_id="fluent")
print(f"表单参数: {params['data']}")

# 获取图形应用关联的文件后缀
extensions = client.apps.get_file_extensions()
print(f"文件后缀: {extensions['data']}")
```

---

## 组织管理

### 部门管理

```python
# 获取部门树
deps = client.organization.get_departments()

# 创建部门
client.organization.create_department(
    dep_name="engineering",
    dep_chname="工程部",
    parent_dep="company",
    description="工程部门"
)

# 修改部门
client.organization.update_department(
    dep_name="engineering",
    dep_chname="工程部门",
    description="更新后的描述"
)

# 删除部门
client.organization.delete_department(dep_name="engineering")
```

### 用户管理

```python
# 获取用户列表
users = client.organization.get_users(page=1, page_size=20)

for user in users["data"]["content"]:
    print(f"用户名: {user['username']}")
    print(f"中文名: {user['chusername']}")
    print(f"部门: {user['dep']}")

# 创建用户
client.organization.create_user(
    username="newuser",
    chusername="新用户",
    password="SecurePass123",
    dep="engineering",
    phone="1234567890",
    mail="user@example.com"
)

# 修改用户
client.organization.update_user(
    username="newuser",
    phone="0987654321",
    mail="newemail@example.com"
)

# 重置密码
client.organization.reset_password(
    username="newuser",
    new_password="NewSecurePass456"
)

# 删除用户
client.organization.delete_user(username="newuser")
```

---

## 系统接口

### 服务器信息

```python
# 获取服务器时间
time = client.call_endpoint("system.serverTime")
print(f"服务器时间: {time['data']}")

# 获取门户主题
theme = client.call_endpoint("system.theme")
print(f"主题信息: {theme['data']}")

# 获取根目录信息
root = client.call_endpoint("system.rootDir")
print(f"根目录: {root['data']}")

# 获取作业统计
stats = client.call_endpoint("system.jobStats")
print(f"作业统计: {stats['data']}")
```

### 通知管理

```python
# 获取通知数量
count = client.call_endpoint("system.notificationCount")
print(f"未读通知: {count['data']}")

# 标记所有通知已读
client.call_endpoint("system.notificationRead")
```

### 存储配额（6.6+）

```python
quota = client.call_endpoint("quota.storage")
print(f"存储配额: {quota['data']}")
```

### CPU 统计（6.6+）

```python
# 单个应用 CPU 信息
cpu = client.call_endpoint("count.appsCpu", params={
    "appId": "fluent",
    "queue": "normal",
    "noCache": False
})
print(f"可用核数: {cpu['data']['availableCores']}")
print(f"等待作业数: {cpu['data']['pendingJobs']}")

# 所有应用 CPU 信息
all_cpu = client.call_endpoint("count.allAppsCpu", params={"noCache": False})
for app in all_cpu['data']:
    print(f"应用: {app['appId']}")
    print(f"可用核数: {app['availableCores']}")
    print(f"使用核数: {app['usedCores']}")
    print(f"排队作业: {app['pendingJobs']}")
```

---

## 扩展系统

### 注册自定义端点

```python
from appform_sdk import AppformClient

client = AppformClient(base_url="https://your-server.com")

# 注册新端点
client.register_endpoint(
    name="custom.report",
    path="/appform/ws/api/custom/report",
    method="GET",
    description="自定义报表接口"
)

# 覆盖已有端点
client.register_endpoint(
    name="jobs.list",
    path="/appform/ws/api/v2/jobs",
    method="GET",
    override=True
)
```

### 加载扩展文件

```python
# 从文件加载
client.load_extension_file("/path/to/extension.json")

# 从字典加载
client.load_extension({
    "name": "my-extension",
    "version": "1.0.0",
    "endpoints": {
        "custom.endpoint": {
            "path": "/custom/endpoint",
            "method": "POST"
        }
    }
})
```

### 扩展文件格式

```json
{
  "name": "custom-endpoints",
  "version": "1.0.0",
  "description": "自定义端点",
  "endpoints": {
    "custom.report": {
      "path": "/appform/ws/api/custom/report",
      "method": "GET",
      "description": "自定义报表"
    }
  },
  "overrides": {
    "jobs.list": {
      "path": "/appform/ws/api/v2/jobs",
      "method": "GET",
      "description": "覆盖作业列表"
    }
  }
}
```

### 动态 API 调用

```python
# 通过名称调用端点
result = client.call_endpoint("jobs.list", params={"page": 1})

# 使用动态 API
result = client.api.call("jobs.get", path_params={"jobId": "12345"})

# 调用自定义端点
result = client.api.call("custom.report", params={"type": "monthly"})
```

---

## 命令行工具

### 配置管理

```bash
# 设置配置
appform config set \
    --base-url "https://your-server.com" \
    --access-key "your_access_key" \
    --access-key-secret "your_access_key_secret" \
    --username "your_username" \
    --api-version "6.6" \
    --verify-ssl false

# 查看配置
appform config show
```

### 认证操作

```bash
# 登录
appform auth login --username "user" --password "pass"

# 测试连接
appform auth ping

# 登出
appform auth logout
```

### 作业操作

```bash
# 提交作业
appform jobs submit --app-name fluent --job-name my_job --cores 4 --memory 8000

# 列出作业
appform jobs list
appform jobs list --status RUN --page 1 --page-size 20

# 按状态查看作业
appform jobs status RUN
appform jobs status PEND
appform jobs status all

# 获取作业详情
appform jobs get <job_id>

# 停止作业
appform jobs stop <job_id>

# 暂停作业
appform jobs suspend <job_id>

# 恢复作业
appform jobs resume <job_id>

# 获取作业输出
appform jobs output <job_id>

# 获取作业文件
appform jobs files <job_id>

# 获取作业历史
appform jobs history <job_id>
```

### 会话操作

```bash
# 启动会话
appform sessions start --app-id ansys --cores 2 --memory 4000

# 列出当前用户会话（默认）
appform sessions list

# 列出所有会话
appform sessions list-all

# 连接会话
appform sessions connect <session_id>

# 断开会话
appform sessions disconnect <session_id>

# 关闭会话
appform sessions close <session_id>

# 共享会话
appform sessions share <session_id> --usernames "user1,user2"
```

### 文件操作

```bash
# 列出文件
appform files list --path "/home/user"

# 创建目录
appform files mkdir --path "/home/user" --name "new_folder"

# 删除文件
appform files delete /path/file1 /path/file2
```

### 应用操作

```bash
# 列出应用
appform apps list
```

### 扩展管理

```bash
# 列出已加载扩展
appform extension list

# 加载扩展
appform extension load /path/to/extension.json
```

### 端点管理

```bash
# 列出所有端点
appform endpoint list

# 列出特定版本的端点
appform endpoint list --version 6.6

# 调用端点
appform endpoint call jobs.list --params '{"page": 1}'
appform endpoint call jobs.get --path-params '{"jobId": "123"}'
```

### 输出格式

```bash
# JSON 格式（默认）
appform -o json jobs list

# 文本格式
appform -o text jobs list
```

---

## 错误处理

### 异常类型

```python
from appform_sdk import AppformClient
from appform_sdk.exceptions import (
    AppformError,       # 基础异常
    AuthenticationError, # 认证错误
    APIError,           # API 错误
    ValidationError,    # 验证错误
    FileError,          # 文件操作错误
    JobError,           # 作业操作错误
    SessionError,       # 会话操作错误
)
```

### 错误处理示例

```python
from appform_sdk import AppformClient
from appform_sdk.exceptions import AuthenticationError, APIError, AppformError

client = AppformClient(base_url="https://your-server.com")

try:
    result = client.auth.login(username="user", password="wrong_password")
except AuthenticationError as e:
    print(f"认证失败: {e.message}")
except APIError as e:
    print(f"API 错误 (状态码 {e.status_code}): {e.message}")
    print(f"响应数据: {e.response}")
except AppformError as e:
    print(f"一般错误: {e.message}")
```

### 常见错误

| 错误类型 | 说明 | 处理建议 |
|---------|------|---------|
| AuthenticationError | 认证失败 | 检查用户名密码或 AccessKey |
| APIError | API 返回错误 | 检查请求参数 |
| AppformError | 网络或连接错误 | 检查网络连接和服务器状态 |

---

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐
with AppformClient(base_url="...") as client:
    # 使用 client
    pass
# 自动关闭

# 不推荐
client = AppformClient(base_url="...")
# 使用 client
client.close()  # 容易忘记
```

### 2. 使用配置文件

```python
# 推荐：使用配置文件
config = Config()
client = AppformClient(
    base_url=config.base_url,
    access_key=config.access_key,
    access_key_secret=config.access_key_secret,
    username=config.username,
)

# 不推荐：硬编码
client = AppformClient(
    base_url="https://hardcoded-server.com",
    access_key="hardcoded_key",
    ...
)
```

### 3. 错误处理

```python
# 推荐：处理特定错误
try:
    result = client.jobs.get_job(job_id)
except APIError as e:
    if e.status_code == 404:
        print("作业不存在")
    else:
        raise

# 不推荐：忽略错误
result = client.jobs.get_job(job_id)  # 可能抛出未处理的异常
```

### 4. 批量操作

```python
# 推荐：批量操作
client.jobs.batch_stop(["job1", "job2", "job3"])

# 不推荐：循环单个操作
for job_id in ["job1", "job2", "job3"]:
    client.jobs.stop(job_id)
```

### 5. 版本适配

```python
# 推荐：检查版本
if _compare_versions(client.api_version, "6.6") >= 0:
    result = client.call_endpoint("jobs.submitV2", json_data={...})
else:
    result = client.jobs.submit(...)

# 或使用 try-except
try:
    result = client.call_endpoint("jobs.submitV2", json_data={...})
except ValueError:
    result = client.jobs.submit(...)
```

---

## API 参考

### AppformClient

| 属性/方法 | 说明 |
|----------|------|
| `auth` | 认证 API |
| `jobs` | 作业 API |
| `sessions` | 会话 API |
| `apps` | 应用 API |
| `files` | 文件 API |
| `organization` | 组织 API |
| `api` | 动态 API |
| `registry` | 端点注册表 |
| `extension_manager` | 扩展管理器 |
| `token` | 当前 Token |
| `api_version` | API 版本 |
| `call_endpoint(name, ...)` | 调用注册的端点 |
| `register_endpoint(...)` | 注册端点 |
| `load_extension(...)` | 加载扩展 |
| `close()` | 关闭客户端 |

### AuthAPI

| 方法 | 说明 |
|------|------|
| `login(username, password)` | 密码登录 |
| `login_with_token(username, timeout)` | Token 登录 |
| `login_with_access_key(...)` | AccessKey 认证 |
| `logout()` | 登出 |
| `ping()` | 测试连接 |
| `register(...)` | 注册用户 |
| `has_upload_permission()` | 检查上传权限 |
| `has_download_permission()` | 检查下载权限 |
| `is_authenticated()` | 是否已认证 |

### JobsAPI

| 方法 | 说明 |
|------|------|
| `submit(...)` | 提交作业 |
| `get_job(job_id)` | 获取作业详情 |
| `list_jobs(...)` | 分页查询作业 |
| `list_jobs_by_ids(job_ids)` | 批量查询作业 |
| `list_history(...)` | 分页查询历史作业 |
| `stop(job_id)` | 停止作业 |
| `suspend(job_id)` | 暂停作业 |
| `resume(job_id)` | 恢复作业 |
| `requeue(job_id)` | 重新排队 |
| `get_output(job_id)` | 获取作业输出 |
| `get_files(job_id)` | 获取作业文件 |
| `get_history(job_id)` | 获取作业历史 |
| `connect(job_id)` | 连接作业图形 |
| `batch_stop(job_ids)` | 批量停止 |
| `batch_suspend(job_ids)` | 批量暂停 |
| `batch_resume(job_ids)` | 批量恢复 |

### SessionsAPI

| 方法 | 说明 |
|------|------|
| `start(app_id, ...)` | 启动会话 |
| `list_all()` | 查询所有会话 |
| `list(...)` | 分页查询会话 |
| `connect(session_id)` | 连接会话 |
| `disconnect(session_id)` | 断开会话 |
| `close(session_id)` | 关闭会话 |
| `share(session_id, usernames)` | 共享会话 |
| `cancel_share(session_id)` | 取消共享 |
| `transfer_operation(...)` | 转移操作权 |
| `webclient_connect(session_id)` | Web 连接 |

### FilesAPI

| 方法 | 说明 |
|------|------|
| `list(path)` | 列出文件 |
| `mkdir(path, name)` | 创建目录 |
| `rename(old_path, new_name)` | 重命名 |
| `copy(src_paths, dest_path)` | 复制 |
| `delete(paths)` | 删除 |
| `upload(file_path, remote_path)` | 上传 |
| `download(remote_path, local_path)` | 下载 |
| `compress(paths, output_name)` | 压缩 |
| `uncompress(archive_path, dest_path)` | 解压 |
| `get_root_dir()` | 获取根目录 |

### OrganizationAPI

| 方法 | 说明 |
|------|------|
| `get_departments()` | 获取部门树 |
| `create_department(...)` | 创建部门 |
| `update_department(...)` | 修改部门 |
| `delete_department(dep_name)` | 删除部门 |
| `get_users(...)` | 获取用户列表 |
| `create_user(...)` | 创建用户 |
| `update_user(...)` | 修改用户 |
| `delete_user(username)` | 删除用户 |
| `reset_password(...)` | 重置密码 |

### 动态端点（6.6+）

| 端点名称 | 方法 | 说明 |
|----------|------|------|
| `jobs.getForm` | GET | 获取作业表单 |
| `jobs.submitV2` | POST | 提交作业 V2 |
| `jobs.listV2` | GET | 查询作业 V2 |
| `jobs.deleteV2` | DELETE | 删除作业 |
| `jobs.tooltip` | GET | 作业监控信息 |
| `jobs.totalHistory` | GET | 历史作业总数 |
| `sessions.startV2` | POST | 启动会话 V2 |
| `apps.listV2` | GET | 获取应用 V2 |
| `quota.storage` | GET | 存储配额 |
| `count.appsCpu` | GET | 应用 CPU 统计 |
| `count.allAppsCpu` | GET | 所有应用 CPU 统计 |
| `files.getConfidentiality` | GET | 获取文件密级（6.5+） |
| `files.setConfidentiality` | POST | 设置文件密级（6.5+） |

---

## 联系与支持

- **问题反馈**: https://github.com/YUTIAN0/jhinno-appform-sdk/issues
- **文档**: https://github.com/YUTIAN0/jhinno-appform-sdk#readme

## 许可证

MIT License
