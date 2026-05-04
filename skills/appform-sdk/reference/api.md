# Appform SDK API 参考

所有 API 模块的完整方法签名和参数说明。

## 导入

```python
from appform_sdk import AppformClient, Config
from appform_sdk.exceptions import APIError, AppformError, AuthenticationError, SFTPError
from appform_sdk.compute import ComputeError
```

## AppformClient

### 构造函数

```python
AppformClient(
    base_url: Optional[str] = None,
    token: Optional[str] = None,
    access_key: Optional[str] = None,
    access_key_secret: Optional[str] = None,
    username: Optional[str] = None,
    aes_key: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3,
    verify_ssl: Optional[bool] = None,
    api_version: Optional[str] = None,
    extensions_dir: Optional[str] = None,
    config: Optional[Config] = None,
)
```

username 未指定时自动检测当前系统用户。`config` 传入 `Config()` 可从配置文件加载所有参数。

### 属性 / 方法

| 属性 | 类型 | 说明 |
|---|---|---|
| `client.auth` | `AuthAPI` | 认证 API |
| `client.jobs` | `JobsAPI` | 作业 API |
| `client.sessions` | `SessionsAPI` | 会话 API |
| `client.apps` | `AppsAPI` | 应用 API |
| `client.files` | `FilesAPI` | 文件 API |
| `client.organization` | `OrganizationAPI` | 组织 API |
| `client.sftp` | `SFTPAPI` | SFTP API（懒初始化） |
| `client.api` | `DynamicAPI` | 动态 API |
| `client.token` | `str` | 读写 token |
| `client.access_key` | `str` | 读写 access_key |
| `client.access_key_secret` | `str` | 读写 access_key_secret |
| `client.username` | `str` | 读写 username |
| `client.api_version` | `str` | 只读 API 版本 |

```python
client.call_endpoint(endpoint_name, path_params=None, **kwargs)
client.close()
# 上下文管理器
with AppformClient(...) as client:
    ...
```

---

## JobsAPI

### 状态常量

```python
JobsAPI.STATUS_RUNNING   # "RUN"
JobsAPI.STATUS_PENDING   # "PEND"
JobsAPI.STATUS_UNKNOWN   # "UNKNOWN"
JobsAPI.STATUS_PSUSP     # "PSUSP" 等待中挂起
JobsAPI.STATUS_USUSP     # "USUSP" 用户挂起
JobsAPI.STATUS_SSUSP     # "SSUSP" 系统挂起
JobsAPI.STATUS_ZOMBI     # "ZOMBI" 僵尸
JobsAPI.STATUS_DONE      # "DONE"  完成
JobsAPI.STATUS_EXIT      # "EXIT"  退出
```

### 方法

```python
# 提交
client.jobs.submit(app_id: str, params: Dict) -> Dict
client.jobs.submit_v2(app_id: str, params: Dict) -> Dict  # 6.6+

# 查询
client.jobs.get_job(job_id: str) -> Dict
client.jobs.list_jobs(
    page: int = 1, page_size: int = 20,
    name_filter: Optional[str] = None,
    status_filter: Optional[List[str]] = None,
    app_name_filter: Optional[str] = None,
    queue_filter: Optional[str] = None,
    condition: Optional[Dict] = None,  # 与上面过滤互斥
) -> Dict
client.jobs.list_jobs_by_ids(job_ids: List[str]) -> Dict
client.jobs.list_jobs_v2(
    page: int = 1, page_size: int = 20,
    condition: Optional[Dict] = None,
) -> Dict  # 6.6+

# 历史
client.jobs.get_history(job_id: str) -> Dict
client.jobs.get_batch_history(job_ids: List[str]) -> Dict
client.jobs.list_history(
    page: int = 1, page_size: int = 20,
    condition: Optional[Dict] = None,
) -> Dict

# 输出 / 文件
client.jobs.get_output(job_id: str) -> Dict
client.jobs.get_files(job_id: str) -> Dict

# 控制 — 单个
client.jobs.stop(job_id: str) -> Dict
client.jobs.suspend(job_id: str) -> Dict
client.jobs.resume(job_id: str) -> Dict
client.jobs.requeue(job_id: str) -> Dict
client.jobs.perform_action(job_id: str, action: str) -> Dict

# 控制 — 批量
client.jobs.batch_stop(job_ids: List[str]) -> Dict
client.jobs.batch_suspend(job_ids: List[str]) -> Dict
client.jobs.batch_resume(job_ids: List[str]) -> Dict
client.jobs.batch_requeue(job_ids: List[str]) -> Dict
client.jobs.batch_action(job_ids: List[str], action: str) -> Dict

# 连接图形会话
client.jobs.connect(job_id: str) -> Dict

# V2 专用 (6.6+)
client.jobs.delete_job(job_id: str) -> Dict
client.jobs.get_form(app_id: str) -> Dict       # 获取作业提交表单
client.jobs.get_tooltip() -> Dict                # 作业监控信息
client.jobs.get_total_history_count() -> Dict    # 历史作业总数
```

---

## SessionsAPI

```python
# 启动
client.sessions.start(
    app_id: str,
    start_new: Optional[bool] = None,
    cwd: Optional[str] = None,
    work_file: Optional[str] = None,
    param: Optional[str] = None,
) -> Dict
client.sessions.start_v2(...) -> Dict  # 6.6+，返回 clientUrl + webUrl

# 查询
client.sessions.list(
    session_ids: Optional[List[str]] = None,
    session_name: Optional[str] = None,
) -> Dict
# 无参数时遍历所有分页查找当前用户会话（较重操作）

client.sessions.list_all(page: int = 1, page_size: int = 20) -> Dict
client.sessions.get_by_session_ids(session_ids: List[str]) -> Dict  # 已废弃
client.sessions.get_by_session_name(session_name: str) -> Dict      # 已废弃

# 连接
client.sessions.connect(session_id: str) -> Dict
client.sessions.connect_and_launch(session_id: str, timeout: int = 30) -> Dict
client.sessions.webclient_connect(session_id: str) -> Dict

# 断开 / 关闭
client.sessions.disconnect(session_id: str) -> Dict
client.sessions.batch_disconnect(session_ids: List[str]) -> Dict
client.sessions.close(session_id: str) -> Dict
client.sessions.batch_close(session_ids: List[str]) -> Dict

# 分享
client.sessions.share(session_id: str, usernames: List[str]) -> Dict
client.sessions.cancel_share(session_id: str) -> Dict
client.sessions.transfer_operation(session_id: str, username: str) -> Dict
```

### 模块级函数

```python
from appform_sdk.sessions import check_jhapp_client, try_launch_jhapp_client

check_jhapp_client(port: int = 60540, timeout: float = 1.0) -> bool
try_launch_jhapp_client(jhapp_url: str, desktop_id: str, timeout: int = 30) -> bool
```

---

## AppsAPI

```python
client.apps.list_all() -> Dict                               # 所有应用菜单
client.apps.list_v2() -> Dict                                # 6.6+，含计算/交互/Web 应用
client.apps.get_url(app_name: str) -> Dict                   # 获取应用 URL
client.apps.get_form_params(app_id: str) -> Dict             # 获取表单参数
client.apps.get_file_extensions() -> Dict                    # 文件扩展名关联
```

---

## FilesAPI

## FilesAPI

以下方法支持 `transfer_method: str = "http"` 参数，可传 `"sftp"` 切换传输协议：
`list`, `list_all`, `mkdir`, `copy`, `move`, `delete`, `upload`, `upload_directory`, `download`, `download_directory`。

`rename`, `cat`, `compress`, `uncompress`, `get_confidentiality_levels`, `set_confidentiality`, `get_root_dir` 不支持该参数。

```python
# 列表
client.files.list(path: str = "/", page: int = 1, page_size: int = 100, transfer_method: str = "http") -> Dict
client.files.list_all(path: str = "/", transfer_method: str = "http") -> List[Dict]

# 目录
client.files.mkdir(path: str, force: bool = True, transfer_method: str = "http") -> Dict

# 复制 / 移动 / 删除
client.files.copy(src_path: str, dest_dir: str, transfer_method: str = "http") -> Dict
client.files.move(src_path: str, dest_dir: str, transfer_method: str = "http") -> Dict
client.files.delete(path: str, transfer_method: str = "http") -> Dict

# 重命名（仅 HTTP，无 transfer_method）
client.files.rename(old_path: str, new_name: str) -> Dict

# 上传
client.files.upload(
    file_path: str, remote_path: str,
    on_progress: Optional[Callable] = None,
    chunk_size: int = 104857600,
    transfer_method: str = "http",
) -> Dict
client.files.upload_directory(
    local_dir: str, remote_dir: str,
    on_progress: Optional[Callable] = None,
    check_exists: Optional[Callable] = None,
    confirm: Optional[Callable] = None,
    chunk_size: int = 104857600,
    transfer_method: str = "http",
) -> List[Dict]

# 下载
client.files.download(
    remote_path: str, local_path: Optional[str] = None,
    on_progress: Optional[Callable] = None,
    chunk_size: int = 104857600,
    transfer_method: str = "http",
) -> bytes  # local_path 为 None 时返回 bytes
client.files.download_directory(
    remote_dir: str, local_dir: str,
    on_progress: Optional[Callable] = None,
    chunk_size: int = 104857600,
    transfer_method: str = "http",
) -> List[Dict]

# 查看文件内容（仅 SFTP，无 transfer_method）
client.files.cat(
    remote_path: str,
    head: Optional[int] = None,
    tail: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    encoding: str = "utf-8",
    all_lines: bool = False,
) -> List[str]

# 压缩 / 解压（无 transfer_method）
client.files.compress(source_dir: str, target_path: str) -> Dict
client.files.uncompress(archive_path: str, dest_dir: str, password: Optional[str] = None) -> Dict

# 密级
client.files.get_confidentiality_levels() -> Dict
client.files.set_confidentiality(path: str, level: str) -> Dict

# 根目录
client.files.get_root_dir() -> Dict
```

---

## SFTPAPI

需要 `pip install jhinno-appform-sdk[sftp]`。通过 `client.sftp` 访问。

```python
# 获取 home 目录（通过 SSH exec echo ~）
client.sftp.get_home_dir() -> str

# 文件操作（与 FilesAPI 签名一致）
client.sftp.list(path: str = "/", page: int = 1, page_size: int = 100) -> Dict
client.sftp.list_all(path: str = "/") -> List[Dict]
client.sftp.mkdir(path: str, force: bool = True) -> Dict
client.sftp.copy(src_path: str, dest_dir: str) -> Dict
client.sftp.move(src_path: str, dest_dir: str) -> Dict
client.sftp.delete(path: str) -> Dict
client.sftp.upload(file_path: str, remote_path: str, ...) -> Dict
client.sftp.upload_directory(local_dir: str, remote_dir: str, ...) -> List[Dict]
client.sftp.download(remote_path: str, local_path: Optional[str] = None, ...) -> bytes
client.sftp.download_directory(remote_dir: str, local_dir: str, ...) -> List[Dict]
client.sftp.cat(remote_path: str, head=None, tail=None, start=None, end=None, ...) -> List[str]

# SSH 命令
client.sftp.tailf(remote_path: str, encoding: str = "utf-8") -> Tuple[str, Channel]
client.sftp.kill_tail(tail_pid: str) -> None

# 关闭
client.sftp.close() -> None
```

---

## AuthAPI

```python
# 登录
client.auth.login(username: str, password: str) -> Dict
client.auth.login_with_token(
    username: Optional[str] = None, timeout: Optional[int] = None,
) -> Dict
# AES token 登录，仅限集群内环境，自动检测当前用户

client.auth.login_with_access_key(
    access_key: str, access_key_secret: str, username: str,
) -> None
client.auth.set_access_key(access_key, access_key_secret, username) -> None  # 别名

# 登出 / 测试
client.auth.logout() -> Dict
client.auth.ping() -> Dict

# 注册
client.auth.register(
    username: str, chusername: str, password: str,
    phone: Optional[str] = None,
    mail: Optional[str] = None,
    dep: Optional[str] = None,
    card: Optional[str] = None,
) -> Dict

# 权限检查
client.auth.check_upload_permission() -> Dict
client.auth.check_download_permission() -> Dict
client.auth.has_upload_permission() -> bool
client.auth.has_download_permission() -> bool
client.auth.is_authenticated() -> bool
client.auth.is_token_authenticated() -> bool
client.auth.is_access_key_authenticated() -> bool
client.auth.clear_access_key() -> None
```

---

## OrganizationAPI

### 部门

```python
client.organization.get_departments() -> Dict
client.organization.create_department(
    dep_name: str, dep_chname: str,
    parent_dep: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict
client.organization.update_department(
    dep_name: str,
    dep_chname: Optional[str] = None,
    parent_dep: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict
client.organization.delete_department(dep_name: str) -> Dict
```

### 用户

```python
client.organization.get_users(
    page: int = 1, page_size: int = 20,
    dep: Optional[str] = None,
    username: Optional[str] = None,
) -> Dict
client.organization.create_user(
    username: str, chusername: str, password: str,
    dep: Optional[str] = None,
    phone: Optional[str] = None,
    mail: Optional[str] = None,
    card: Optional[str] = None,
) -> Dict
client.organization.update_user(
    username: str,
    chusername: Optional[str] = None,
    dep: Optional[str] = None,
    phone: Optional[str] = None,
    mail: Optional[str] = None,
    card: Optional[str] = None,
) -> Dict
client.organization.delete_user(username: str) -> Dict
client.organization.reset_password(username: str, new_password: str) -> Dict
```

---

## Config

### 构造函数

```python
Config(
    base_url: Optional[str] = None,
    access_key: Optional[str] = None,
    access_key_secret: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
    aes_key: Optional[str] = None,
    timeout: Optional[int] = None,
    verify_ssl: Optional[bool] = None,
    api_version: Optional[str] = None,
    extensions_dir: Optional[str] = None,
    job_profile_config: Optional[str] = None,
    output_format: Optional[str] = None,
    output_template: Optional[str] = None,
    chunk_size: Optional[int] = None,
    config_file: Optional[str] = None,
    sftp_host: Optional[str] = None,
    sftp_port: Optional[int] = None,
    sftp_username: Optional[str] = None,
    sftp_password: Optional[str] = None,
    sftp_key_file: Optional[str] = None,
    sftp_key_password: Optional[str] = None,
)
```

优先级：直接参数 > 环境变量 > 配置文件(`~/.appform/config.json`)。

### 类方法

```python
Config.from_env() -> Config
Config.from_file(config_file: str) -> Config
Config.get_default_config_path() -> Path       # ~/.appform/config.json
Config.get_default_extensions_dir() -> Path     # ~/.appform/extensions
Config.save_config_file(...) -> None            # 写入配置文件
```

### 环境变量

| 变量 | 说明 |
|---|---|
| `APPFORM_BASE_URL` | API 地址 |
| `APPFORM_ACCESS_KEY` | 访问密钥 |
| `APPFORM_ACCESS_KEY_SECRET` | 密钥 |
| `APPFORM_USERNAME` | 用户名 |
| `APPFORM_PASSWORD` | 密码 |
| `APPFORM_TOKEN` | 认证令牌 |
| `APPFORM_AES_KEY` | AES 加密密钥 |
| `APPFORM_TIMEOUT` | 超时秒数 |
| `APPFORM_VERIFY_SSL` | SSL 校验 |
| `APPFORM_API_VERSION` | API 版本 |
| `APPFORM_EXTENSIONS_DIR` | 扩展目录 |
| `APPFORM_JOB_PROFILE_CONFIG` | 作业配置文件 |
| `APPFORM_OUTPUT_FORMAT` | 输出格式 json/table/raw/text |
| `APPFORM_OUTPUT_TEMPLATE` | 输出模板文件 |
| `APPFORM_DEFAULT_REMOTE_PATH` | 默认远程路径 |
| `APPFORM_CHUNK_SIZE` | 读取块大小 |
| `APPFORM_DEFAULT_METHOD` | 默认传输方式 http/sftp |
| `APPFORM_SFTP_HOST` | SFTP 主机 |
| `APPFORM_SFTP_PORT` | SFTP 端口 |
| `APPFORM_SFTP_KEY_FILE` | SSH 密钥文件 |
| `APPFORM_SFTP_KEY_PASSWORD` | SSH 密钥密码 |
| `APPFORM_COMPUTE_CONFIG` | 计算节点配置文件 |

---

## 异常

```python
from appform_sdk.exceptions import AppformError, APIError, AuthenticationError, SFTPError
from appform_sdk.compute import ComputeError
```

| 异常 | 继承 | 场景 |
|---|---|---|
| `AppformError` | `Exception` | 基础异常 |
| `APIError` | `AppformError` | API 返回错误 (HTTP 4xx/5xx) |
| `AuthenticationError` | `AppformError` | 认证失败 (401) |
| `SFTPError` | `AppformError` | SFTP 操作失败 |
| `ComputeError` | `AppformError` | 计算节点 SSH 操作失败 |

---

## 工具函数

```python
from appform_sdk.files import parse_size

parse_size("256K")   # 262144
parse_size("30M")    # 31457280
parse_size("1G")     # 1073741824
parse_size(1048576)  # 1048576
```
