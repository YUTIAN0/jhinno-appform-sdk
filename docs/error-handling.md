# 错误处理与最佳实践

## 异常类型

| 异常类 | 说明 | 触发场景 |
|--------|------|---------|
| `AppformError` | 基础异常 | 网络错误、通用错误 |
| `AuthenticationError` | 认证异常 | Token 无效、登录失败 |
| `APIError` | API 错误 | HTTP 4xx/5xx 响应 |
| `ValidationError` | 参数校验错误 | 参数格式不正确 |
| `FileError` | 文件操作错误 | 文件不存在、上传失败 |
| `JobError` | 作业错误 | 作业提交失败 |
| `SessionError` | 会话错误 | 会话操作失败 |

## 错误处理示例

```python
from appform_sdk import AppformClient, AuthenticationError, APIError, AppformError

try:
    client = AppformClient(base_url="...", token="...")
    result = client.jobs.submit(app_id="fluent", params={"JH_CAS": "/path/to/file.cas"})
except AuthenticationError:
    print("认证失败，请检查 token 或重新登录")
except APIError as e:
    print(f"API 错误: {e.message}, 状态码: {e.status_code}")
except AppformError as e:
    print(f"请求失败: {e}")
```

## CLI 错误处理

CLI 工具遇到错误时会输出到 stderr 并退出：

```bash
# 错误的应用 ID
appform jobs submit -a unknown_app -i /path/to/file
# Error: Unknown application 'unknown_app'. Available: starccm, lsdyna2, ...

# 缺少必填参数
appform jobs submit -a starccm --dry-run
# Error: Required parameter missing: JH_CAS (算例文件路径)

# 参数校验失败
appform jobs submit -a starccm -i /path/to/file.txt --dry-run
# Error: Parameter JH_CAS='/path/to/file.txt' does not match pattern '^.*\.(sim)$'
```

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐
with AppformClient(base_url="...", token="...") as client:
    jobs = client.jobs.list_jobs()
# 自动关闭连接
```

### 2. 使用配置文件

```python
# 推荐：使用配置文件
config = Config()
client = AppformClient(config=config)

# 不推荐：硬编码
client = AppformClient(base_url="https://...", access_key="...")
```

### 3. 错误处理

```python
# 推荐：处理特定错误
try:
    result = client.jobs.submit(...)
except AuthenticationError:
    # 重新认证
    client.auth.login(username="...", password="...")
    result = client.jobs.submit(...)
except APIError as e:
    print(f"API error: {e}")

# 不推荐：忽略错误
result = client.jobs.submit(...)  # 可能抛出异常
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
if client.api_version >= "6.6":
    result = client.jobs.submit_v2(...)
else:
    result = client.jobs.submit(...)

# 或使用 try-except
try:
    result = client.jobs.delete_job(job_id)  # 6.6+ only
except AttributeError:
    print("当前版本不支持删除作业")
```

### 6. 使用 --dry-run 预览

```bash
# 提交前先预览参数
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run
# 确认参数无误后再实际提交
appform jobs submit -a starccm -i /path/to/file.sim -n 16
```
