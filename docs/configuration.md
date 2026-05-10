# 配置管理

Appform SDK 支持多种配置方式，按优先级从高到低：

1. 直接参数（CLI `--output` 等）
2. 环境变量
3. 配置文件 (`~/.appform/config.json`)

## 环境变量

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `APPFORM_BASE_URL` | API 基础 URL | `https://server` |
| `APPFORM_USERNAME` | 用户名（可省略，自动使用当前系统用户） | `your_username` |
| `APPFORM_PASSWORD` | 密码 | `your_password` |
| `APPFORM_ACCESS_KEY` | AccessKey（需 6.4+） | `your_key` |
| `APPFORM_ACCESS_KEY_SECRET` | AccessKey 密钥（需 6.4+） | `your_secret` |
| `APPFORM_TOKEN` | 认证 Token | `your_token` |
| `APPFORM_AES_KEY` | AES 加密密钥（仅集群环境） | `your_aes_key` |
| `APPFORM_API_VERSION` | API 版本 | `6.3` |
| `APPFORM_TIMEOUT` | 请求超时（秒） | `30` |
| `APPFORM_VERIFY_SSL` | 是否验证 SSL | `false` |
| `APPFORM_EXTENSIONS_DIR` | 扩展目录 | `/path/to/extensions` |
| `APPFORM_JOB_PROFILE_CONFIG` | 作业配置文件路径 | `/path/to/job_submit.yaml` |
| `APPFORM_OUTPUT_FORMAT` | 默认输出格式 | `json` / `table` / `text` |
| `APPFORM_OUTPUT_TEMPLATE` | 输出模板文件路径 | `/path/to/template.yaml` |
| `APPFORM_DEFAULT_REMOTE_PATH` | 文件操作默认远程路径 | `/home/user/` |
| `APPFORM_CHUNK_SIZE` | 上传/下载分块大小 | `100M` |
| `APPFORM_DEFAULT_METHOD` | 文件操作默认传输方式 | `http` |
| `APPFORM_SFTP_HOST` | SFTP 服务器主机名 | 从 base_url 提取 |
| `APPFORM_SFTP_PORT` | SFTP 服务器端口 | `22` |
| `APPFORM_SFTP_KEY_FILE` | SSH 私钥文件路径 | — |
| `APPFORM_SFTP_KEY_PASSWORD` | SSH 私钥密码 | — |
| `APPFORM_HTTP_PROXY` | HTTP/HTTPS 代理 | — |
| `APPFORM_SFTP_PROXY` | SFTP/SSH 代理 | — |
| `APPFORM_ENV` | 目标环境名称 | — |

```bash
# 密码认证（适用于所有版本）
export APPFORM_BASE_URL=https://server
export APPFORM_USERNAME=your_username
export APPFORM_PASSWORD=your_password

# AccessKey 认证（需 6.4+）
export APPFORM_BASE_URL=https://server
export APPFORM_ACCESS_KEY=your_key
export APPFORM_ACCESS_KEY_SECRET=your_secret

# 设置默认输出格式
export APPFORM_OUTPUT_FORMAT=json
```

## 配置文件

默认路径：`~/.appform/config.json`

```json
{
  "base_url": "https://your-server.com",
  "username": "your_username",
  "password": "your_password",
  "verify_ssl": false,
  "api_version": "6.3",
  "timeout": 30,
  "job_profile_config": "/apps/software/script/job_submit.yaml",
  "output_format": "table"
}
```

**多环境配置**（在单个配置文件中管理多个环境）：

```json
{
  "default_environment": "prod",
  "environments": {
    "prod": {
      "base_url": "https://prod.jhinno.com",
      "api_version": "6.6"
    },
    "dev": {
      "base_url": "https://dev.jhinno.com",
      "api_version": "6.6"
    },
    "test": {
      "base_url": "https://test.jhinno.com",
      "api_version": "6.5"
    }
  }
}
```

环境选择优先级：
1. 构造函数参数：`Config(env="prod")`、CLI `--env prod`
2. 环境变量：`export APPFORM_ENV=prod`
3. 配置文件的 `default_environment` 字段
4. 未指定时回退到根级别配置（兼容旧格式）

### 通过 CLI 保存配置

```bash
# 基础配置
appform config set --base-url https://server
appform config set --username your_username --password your_password

# 保存到指定环境
appform config set --environment prod --base-url https://prod.jhinno.com
appform config set --environment dev --base-url https://dev.jhinno.com

# AccessKey（需 6.4+）
appform config set --access-key KEY --access-key-secret SECRET

# 其他设置
appform config set --api-version 6.3
appform config set --verify-ssl false
appform config set --job-profile-config /path/to/job_submit.yaml
appform config set --aes-key your_aes_key

# 设置默认输出格式
appform config set --output-format table

# 设置默认文件传输方式
appform config set --default-method sftp

# SFTP 配置
appform config set --sftp-host mycluster.example.com
appform config set --sftp-port 22
appform config set --sftp-key-file ~/.ssh/id_rsa

# 代理配置
appform config set --http-proxy http://proxy:8080
appform config set --sftp-proxy socks5://proxy:1080

# 查看当前配置
appform config show
```

> **注意**：`config set` 会保留已有配置，只更新指定的字段。

## Python 中使用 Config

```python
from appform_sdk import Config

# 自动加载 ~/.appform/config.json
config = Config()

# 指定配置文件
config = Config(config_file="/path/to/config.json")

# 直接参数（优先级最高）
config = Config(
    base_url="https://server",
    username="your_username",
    password="your_password",
)

# 使用环境配置
config = Config(env="prod")
# 等效于 Config(config_file="~/.appform/config.json", env="prod")

# 查看配置（敏感字段自动脱敏）
print(config.to_dict())

# 保存配置（保留已有字段）
Config.save_config_file(
    base_url="https://server",
    username="your_username",
    password="your_password",
    job_profile_config="/path/to/job_submit.yaml",
    output_format="table",
)

# 保存到指定环境
Config.save_config_file(
    environment="prod",
    base_url="https://prod.jhinno.com",
)
```

## 在 Client 中使用

```python
from appform_sdk import AppformClient, Config

# 方式1：直接传参
client = AppformClient(
    base_url="https://server",
    username="your_username",
    password="your_password",
    verify_ssl=False,
)

# 方式2：使用 Config 对象
config = Config()
client = AppformClient(config=config)

# 方式3：混合使用（直接参数覆盖配置文件）
client = AppformClient(base_url="https://other-server", config=config)
```

## 配置文件完整字段

```json
{
  "base_url": "https://server",
  "username": "your_username",
  "password": "your_password",
  "access_key": "your_key",
  "access_key_secret": "your_secret",
  "token": "your_token",
  "aes_key": "your_aes_key",
  "api_version": "6.3",
  "timeout": 30,
  "verify_ssl": false,
  "extensions_dir": "/path/to/extensions",
  "job_profile_config": "/path/to/job_submit.yaml",
  "output_format": "table",
  "output_template": "/path/to/template.yaml",
  "default_remote_path": "/home/user/",
  "chunk_size": "100M"
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `base_url` | API 基础 URL | — |
| `username` | 用户名 | 自动检测当前系统用户 |
| `password` | 密码 | — |
| `access_key` | AccessKey（需 6.4+） | — |
| `access_key_secret` | AccessKey 密钥 | — |
| `token` | 认证 Token | — |
| `aes_key` | AES 加密密钥（仅集群） | — |
| `api_version` | API 版本 | `6.5` |
| `timeout` | 请求超时（秒） | `30` |
| `verify_ssl` | 是否验证 SSL | `true` |
| `extensions_dir` | 扩展目录 | — |
| `job_profile_config` | 作业配置文件路径 | 自动检测 |
| `output_format` | 默认输出格式 | `table` |
| `output_template` | 输出模板文件路径 | 内置模板 |
| `default_remote_path` | 文件操作默认远程路径 | `/` |
