# 认证方式

Appform SDK 支持三种认证方式，按推荐程度排列。

## 方式一：AccessKey 签名认证（推荐，需 6.4+）

使用 AccessKey 和 AccessKeySecret 进行 HMAC-SHA256 签名认证。密钥不会直接传输，安全性最高。

> **注意**：AccessKey 认证需要 Appform 6.4 及以上版本。6.3 及以下版本请使用密码登录。

### 基本用法

```python
from appform_sdk import AppformClient

# 指定 username（以该用户身份操作）
client = AppformClient(
    base_url="https://server",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
    username="target_user",
)

# 不指定 username（自动使用当前系统用户）
client = AppformClient(
    base_url="https://server",
    access_key="your_access_key",
    access_key_secret="your_access_key_secret",
)
# username 自动检测为当前登录系统的用户
```

### username 自动检测

未指定 `username` 时，按以下优先级自动检测：

1. `USER` 环境变量
2. `USERNAME` 环境变量（Windows）
3. `getpass.getuser()` 函数
4. `pwd` 模块（Linux）

### 指定其他用户操作

同一个 AccessKey 可以通过切换 `username` 来代表不同用户执行操作：

```python
client = AppformClient(
    base_url="https://server",
    access_key="your_key",
    access_key_secret="your_secret",
    username="user_A",
)

# 以 user_A 身份提交作业
client.jobs.submit(app_id="fluent", params={...})

# 切换到 user_B
client.username = "user_B"

# 以 user_B 身份提交作业
client.jobs.submit(app_id="fluent", params={...})
```

### 签名机制

每个请求自动生成以下请求头：
- `accessKey`: AccessKey
- `signature`: HMAC-SHA256 签名
- `currentTimeMillis`: 当前时间戳（毫秒）
- `username`: 操作账号

签名计算公式：
```
签名字符串 = #accessKey#username#currentTime#
signature  = HMAC-SHA256(accessKeySecret, 签名字符串)
```

### 配置方式

```bash
# 环境变量
export APPFORM_BASE_URL=https://server
export APPFORM_ACCESS_KEY=your_key
export APPFORM_ACCESS_KEY_SECRET=your_secret
# APPFORM_USERNAME 可省略，未设置时自动使用当前系统用户

# 配置文件（永久生效）
appform config set --base-url https://server
appform config set --access-key KEY --access-key-secret SECRET

# CLI 直接指定
appform --access-key KEY --access-key-secret SECRET jobs list
appform --username other_user --access-key KEY --access-key-secret SECRET jobs list
```

## 方式二：密码登录

使用用户名和密码登录获取 Token。支持所有版本。

### Python SDK

```python
client = AppformClient(base_url="https://server")
result = client.auth.login(username="admin", password="your_password")
# Token 自动保存，后续请求自动携带
```

### 配置文件

将 `username` 和 `password` 保存到配置文件，`appform` CLI 和 `job_submit` 工具会自动登录：

```bash
# 保存到配置文件
appform config set --base-url https://server
appform config set --username admin --password your_password

# 之后直接使用，自动完成登录
appform jobs list
appform files list
job_submit -a starccm -i /path/to/file.sim -n 8
```

配置文件内容（`~/.appform/config.json`）：
```json
{
  "base_url": "https://server",
  "username": "admin",
  "password": "your_password"
}
```

### 环境变量

```bash
export APPFORM_BASE_URL=https://server
export APPFORM_USERNAME=admin
export APPFORM_PASSWORD=your_password
```

### CLI 直接指定

```bash
# appform CLI
appform --username admin --password your_password jobs list

# job_submit 工具
job_submit -a starccm -i /path/to/file.sim -n 8 -u admin -p password
```

## 方式三：AES Token 登录（仅限集群环境）

使用 AES/ECB/PKCS7 加密 username 后请求 Token，仅在 HPC 集群环境中可用。

**限制条件：**
- AES 密钥必须通过环境变量或配置文件提供（不硬编码）
- 仅在集群内可用：检测 `jversion` 命令和 `jhosts -w` 中当前节点
- 自动使用当前系统用户，不允许指定任意用户名

### 配置 AES 密钥

```bash
# 环境变量
export APPFORM_AES_KEY=your_aes_key

# 配置文件
appform config set --aes-key your_aes_key
```

配置文件内容：
```json
{
  "aes_key": "your_aes_key"
}
```

### Python SDK

```python
from appform_sdk import AppformClient, check_cluster_environment

# 检查是否在集群内
info = check_cluster_environment()
if info["in_cluster"]:
    print(f"Scheduler: {info['jversion']}")
    print(f"Host: {info['hostname']} ({info['host_status']})")

    client = AppformClient(base_url="https://server", aes_key="your_aes_key")
    client.auth.login_with_token()
    # Token 自动保存，使用当前系统用户
else:
    print(f"Not in cluster: {info['error']}")
```

### 集群环境检测

`check_cluster_environment()` 函数检测当前节点是否在 HPC 集群内：

```python
from appform_sdk import check_cluster_environment

info = check_cluster_environment()
# info = {
#     "in_cluster": True,
#     "jversion": "JH Unischeduler 6.5, Sep 05 2025\n...",
#     "hostname": "ev-hpc-manager3",
#     "host_status": "ok",
#     "error": None,
# }
```

检测逻辑：
1. 执行 `jversion` 命令，确认调度器已安装
2. 获取当前主机名（`socket.gethostname()`）
3. 执行 `jhosts -w` 命令，确认当前主机在集群节点列表中

## 认证优先级

CLI 工具（`appform` 和 `job_submit`）按以下优先级自动选择认证方式：

| 优先级 | `appform` CLI | `job_submit` |
|--------|--------------|-------------|
| 1 | CLI `--username --password` 密码登录 | CLI `-u -p` 密码登录 |
| 2 | CLI `--access-key` AccessKey 认证 | 配置文件 `username` + `password` 密码登录 |
| 3 | 配置文件/环境变量 AccessKey | 配置文件 AccessKey（需 6.4+） |
| 4 | 配置文件/环境变量 Token | 配置文件 Token |
| 5 | — | AES Token 集群自动检测（需配置 aes_key） |

> **版本兼容性说明**：
> - Appform 6.0-6.3：使用密码登录（username + password）
> - Appform 6.4+：推荐使用 AccessKey 认证

## 环境变量完整列表

| 环境变量 | 说明 |
|----------|------|
| `APPFORM_BASE_URL` | API 基础 URL |
| `APPFORM_USERNAME` | 用户名 |
| `APPFORM_PASSWORD` | 密码 |
| `APPFORM_ACCESS_KEY` | AccessKey（需 6.4+） |
| `APPFORM_ACCESS_KEY_SECRET` | AccessKey 密钥（需 6.4+） |
| `APPFORM_TOKEN` | 认证 Token |
| `APPFORM_AES_KEY` | AES 加密密钥（仅集群环境） |
| `APPFORM_API_VERSION` | API 版本 |
| `APPFORM_JOB_PROFILE_CONFIG` | 作业配置文件路径 |
