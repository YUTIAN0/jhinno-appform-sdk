# 会话管理

SessionsAPI 提供交互式应用会话的管理功能。

## 启动会话

### 基础启动（6.0+）

```python
result = client.sessions.start(
    app_id="gedit",
    start_new=True,
    cwd="${HOME}",
    work_file="${HOME}/test.txt",
    param="",  # 启动参数（URL 编码）
)
print(result)  # 包含 desktopId 和 jhappUrl
```

参数说明：

| 参数 | 说明 | 必填 |
|------|------|------|
| `app_id` | 应用 ID（URL 路径参数） | 是 |
| `start_new` | 是否启动新会话 | 否 |
| `cwd` | 工作目录 | 否 |
| `work_file` | 启动时打开的文件 | 否 |
| `param` | 启动参数（URL 编码） | 否 |

### V2 启动（6.6+）

返回客户端连接和 Web 连接信息。

```python
result = client.sessions.start_v2(
    app_id="common_sub",
    start_new=True,
    cwd="${HOME}",
)
print(result)  # 包含 desktopId, clientUrl, webUrl
```

## 查询会话

### 按 ID、名称或用户查询

```python
# 无参数：查询当前登录用户的会话
result = client.sessions.list()

# 按会话 ID 查询
result = client.sessions.list(session_ids=["494039"])

# 按名称查询
result = client.sessions.list(session_name="my_session")

# 多个 ID 查询
result = client.sessions.list(session_ids=["494039", "494040"])
```

> **注意**: `list()` 无参调用时返回全部会话，然后在客户端按当前登录用户的 `owner` 字段过滤。

### 列出所有会话（分页）

```python
result = client.sessions.list_all(page=1, page_size=20)
```

## 会话操作

### 连接会话

```python
# 获取连接信息（包含 jhappUrl）
result = client.sessions.connect("session_id")
print(result["data"][0]["jhappUrl"])
```

### 连接会话并自动启动客户端

```python
# 获取连接信息，检测本地 JHApp 客户端（端口 60540）
# 客户端运行中则自动发送启动请求，否则仅返回 jhappUrl
result = client.sessions.connect_and_launch("session_id")
```

工作原理：

1. 调用 API 获取 `jhappUrl` 连接信息
2. 检测本地端口 `60540`（JHApp 客户端本地 API 端口）
3. 如果端口可用，发送启动请求到 `http://127.0.0.1:60540/jhclientstarter`
4. 如果端口不可用，打印 `jhappUrl` 供手动打开

### 断开、关闭、批量操作

```python
# 断开会话
result = client.sessions.disconnect("session_id")

# 批量断开
result = client.sessions.batch_disconnect(["session_id_1", "session_id_2"])

# 关闭会话
result = client.sessions.close("session_id")

# 批量关闭
result = client.sessions.batch_close(["session_id_1", "session_id_2"])

# 浏览器连接
result = client.sessions.webclient_connect("session_id")
```

## 会话共享

```python
# 共享会话
result = client.sessions.share("session_id", usernames=["user1", "user2"])

# 取消共享
result = client.sessions.cancel_share("session_id")

# 转移操作权
result = client.sessions.transfer_operation("session_id", "new_operator")
```

## 会话字段说明

查询会话返回的字段：

| 字段 | 说明 |
|------|------|
| `session_id` / `id` | 会话 ID |
| `name` | 会话名称 |
| `app_id` | 应用 ID |
| `owner` / `ownername` | 会话所有者 |
| `host` | 会话所属节点 |
| `status` | 会话状态 |
| `protocol` | 启动协议（如 jhapp） |
| `desktop_type` | 会话类型 |
| `createDate` | 创建时间 |
| `lastUseTime` | 最后使用时间 |
| `executionTime` | 过期时间 |
| `isDocker` | 是否为 Docker 会话 |
| `isShare` | 是否已共享 |
| `shareMe` | 是否为共享的会话 |
| `os` | 会话所属系统 |
| `startmode` | 启动模式 |
| `jhappUrl` | jhapp 客户端启动链接 |
| `confidential` | 会话密级 |
| `confidential_cn` | 中文密级 |
| `confidentialEn` | 英文密级 |

## CLI 使用

```bash
# 启动会话
appform sessions start --app-id gedit --start-new --cwd '${HOME}'

# 列出当前用户的会话（默认）
appform sessions list

# 按 ID 查询会话
appform sessions list --ids 494039

# 按名称查询会话
appform sessions list --name my_session

# 列出所有会话
appform sessions list-all

# 获取会话连接信息
appform sessions connect <session_id>

# 连接会话并自动启动客户端
appform sessions connect-launch <session_id>

# 断开会话
appform sessions disconnect <session_id>

# 关闭会话
appform sessions close <session_id>

# 共享会话
appform sessions share <session_id> --usernames user1,user2
```
