---
name: appform-sdk
description: 使用 Appform Python SDK (AppformClient) 提交计算作业、查看作业状态、获取应用列表、启动交互应用。当用户在 Python 代码中操作 Appform、导入 appform_sdk、或使用 SDK 编程方式与 Appform HPC 集群交互时使用。务必在此类场景下使用此 skill，即使用户没有明确提到 "appform_sdk"。
---

# Appform Python SDK 使用指南

与 Appform 6.0-6.6 HPC 平台交互的 Python SDK。

## 安装

```bash
pip install jhinno-appform-sdk
# SFTP 可选
pip install jhinno-appform-sdk[sftp]
```

## 初始化客户端

三种认证方式，选择其一：

```python
from appform_sdk import AppformClient, Config

# 方式 1: AccessKey 认证（推荐）
client = AppformClient(
    base_url="https://appform.example.com",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="your_username",
)

# 方式 2: 用户名密码登录
client = AppformClient(base_url="https://appform.example.com")
client.auth.login(username="user", password="pass")

# 方式 3: 配置文件（~/.appform/config.json）
client = AppformClient(config=Config())
```

配置优先级：直接参数 > 环境变量(`APPFORM_*`) > 配置文件。`verify_ssl=False` 可关闭 SSL 校验。

**禁止直接读取 `~/.appform/config.json` 文件。如果需要查看配置内容，使用 `appform -o json config show` 命令获取。**

## 返回数据说明

SDK 所有方法返回的是 API 原始 JSON（Python `dict`），需自行解析。典型响应结构：

```python
# 列表类 API 返回分页结构
result = client.jobs.list_jobs()
# result["data"]["records"] — 作业列表
# result["data"]["total"]   — 总数

# 单个资源
job = client.jobs.get_job("1001")
# job["data"] — 作业详情 dict

# 提交/控制类
result = client.jobs.submit(...)
# result["data"] — 新作业 ID 或结果
```

字段名因 API 版本和服务器而异，用 `print(result)` 或 `json.dumps(result, indent=2)` 查看完整结构。

## 提交作业

```python
# 基本提交
result = client.jobs.submit(
    app_id="starccm",
    params={
        "JH_JOB_NAME": "cfd_simulation",
        "JH_CAS": "/home/user/simulations/test.sim",
        "JH_NCPU": "32",
        "JH_RELEASE": "16.02",
        "JH_NODE_GROUP": "batch",
        "STAR_POST_SWITCH": "off",
    },
)

# V2 提交（6.6+）— 先用 get_form 获取参数模板
form = client.jobs.get_form("starccm")
result = client.jobs.submit_v2(app_id="starccm", params={...})
```

常用参数键（因应用而异，以上面 starccm 为例）：`JH_JOB_NAME`(作业名), `JH_CAS`(算例文件，必填), `JH_NCPU`(节点数，默认 1), `JH_RELEASE`(软件版本，默认 16.02), `JH_NODE_GROUP`(节点组), `STAR_POST_SWITCH`(后处理开关)。完整参数列表用 `client.jobs.get_form(app_id)` (6.6+) 或 `client.apps.get_form_params(app_id)` 查看。

## 查看作业

```python
# 列表（支持过滤）
jobs = client.jobs.list_jobs(
    page=1,
    page_size=20,
    name_filter="cfd",               # 按名称模糊匹配
    status_filter=["RUN", "PEND"],   # 按状态
    app_name_filter="starccm",       # 按应用名
    queue_filter="batch",            # 按队列名
)

# 按 ID 批量查询
jobs = client.jobs.list_jobs_by_ids(["1001", "1002"])

# 单个作业详情
job = client.jobs.get_job("1001")

# 作业输出
output = client.jobs.get_output("1001")

# 历史作业
history = client.jobs.list_history(page=1, page_size=50)

# 作业控制
client.jobs.stop("1001")
client.jobs.suspend("1001")
client.jobs.resume("1001")
client.jobs.requeue("1001")

# 批量操作
client.jobs.batch_stop(["1001", "1002"])

# 删除作业（6.6+）
client.jobs.delete_job("1001")
```

状态常量：`RUN`(运行), `PEND`(等待), `DONE`(完成), `EXIT`(退出), `UNKNOWN`, `PSUSP`, `USUSP`, `SSUSP`, `ZOMBI`。

## 获取应用列表

```python
# 所有应用（返回原始 JSON dict）
result = client.apps.list_all()
apps = result.get("data", [])

# 遍历应用，通过字典字段区分类型
for app in apps:
    app_id = app.get("app_id") or app.get("APP_ID")
    app_type = app.get("type") or app.get("TYPE")  # "batch" 或 "desktop"
    if app_type == "batch":
        # 计算应用 → client.jobs.submit(app_id=...)
        pass
    elif app_type == "desktop":
        # 交互应用 → client.sessions.start(app_id=...)
        pass
    # 无 TYPE 字段 → 管理入口（应用仓库、我的数据等）

# 计算应用表单参数
form_params = client.apps.get_form_params("starccm")
```

## 启动交互应用

```python
# 启动会话
session = client.sessions.start(
    app_id="gedit",
    start_new=True,        # 强制新建
    cwd="${HOME}",         # 工作目录
    work_file="/path",     # 打开的文件
)

# V2 启动（6.6+）— 返回 clientUrl + webUrl
session = client.sessions.start_v2(
    app_id="common_sub",
    start_new=True,
    cwd="${HOME}",
)

# 查询当前用户会话
my_sessions = client.sessions.list()

# 按 ID 精确查询
sessions = client.sessions.list(session_ids=["sid1", "sid2"])

# 按名称查询
sessions = client.sessions.list(session_name="gedit")

# 获取连接信息
conn = client.sessions.connect("session_id")

# 连接并自动启动 JHApp 客户端
conn = client.sessions.connect_and_launch("session_id")

# 断开 / 关闭
client.sessions.disconnect("session_id")
client.sessions.close("session_id")

# 分享会话
client.sessions.share("session_id", usernames=["user2"])

# Web 客户端连接
web_url = client.sessions.webclient_connect("session_id")
```

`sessions.list()` 无参数时会遍历所有分页来查找当前用户的会话，数据量大时较慢。

## 文件操作

```python
# 列表 / 上传 / 下载
client.files.list(path="/home/user")
client.files.upload(file_path="local.txt", remote_path="/remote/")
client.files.download(remote_path="/remote/file", local_path="./file")

# SFTP 方式（需要 [sftp] 扩展）
client.files.list(path="/home/user", transfer_method="sftp")
client.sftp.tailf(remote_path="/path/to/log")
```

## 动态 API 调用

```python
# 通过注册名调用端点
result = client.call_endpoint("jobs.list", params={"page": 1})
```

## 关闭客户端

```python
client.close()

# 或作为上下文管理器
with AppformClient(base_url="...") as client:
    jobs = client.jobs.list_jobs()
```

## 完整 API 参考

所有模块的完整方法签名、参数类型、环境变量和异常类见 [`reference/api.md`](reference/api.md)。主要补充：

- `AuthAPI` — `login_with_token()` AES token 集群内登录、权限检查、注册
- `OrganizationAPI` — 部门 CRUD、用户 CRUD、重置密码
- `Config` — `from_env()` / `from_file()` / `save_config_file()`、所有 `APPFORM_*` 环境变量
- 异常 — `AppformError` / `APIError` / `AuthenticationError` / `SFTPError` / `ComputeError`
- `parse_size()` — 人类可读大小字符串转字节
