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

### 按 ID 或名称查询

```python
# 按会话 ID 查询
result = client.sessions.list(session_ids=["494039"])

# 按名称查询
result = client.sessions.list(session_name="my_session")

# 多个 ID 查询
result = client.sessions.list(session_ids=["494039", "494040"])
```

### 列出所有会话（分页）

```python
result = client.sessions.list_all(page=1, page_size=20)
```

## 会话操作

```python
# 连接会话
result = client.sessions.connect("session_id")

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

## CLI 使用

```bash
# 启动会话
appform sessions start --app-id gedit --start-new --cwd '${HOME}'

# 按 ID 查询会话
appform sessions list --ids 494039

# 按名称查询会话
appform sessions list --name my_session

# 列出所有会话
appform sessions list-all

# 连接会话
appform sessions connect <session_id>

# 断开会话
appform sessions disconnect <session_id>

# 关闭会话
appform sessions close <session_id>

# 共享会话
appform sessions share <session_id> --usernames user1,user2
```
