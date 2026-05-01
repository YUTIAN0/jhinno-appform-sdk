# 扩展系统

Appform SDK 支持通过扩展系统添加自定义端点、覆盖已有端点，并支持版本化端点管理。

## 版本管理

SDK 支持 Appform 6.0、6.3、6.5、6.6 四个版本的端点。不同版本的端点差异：

| 版本 | 新增端点 |
|------|---------|
| 6.0 | 基础端点（认证、作业、会话、文件、组织等） |
| 6.3 | 与 6.0 相同 |
| 6.5 | `files.getConfidentiality`, `files.setConfidentiality` |
| 6.6 | V2 接口（jobs、sessions、apps）、作业删除、表单查询、存储配额、CPU 统计、项目管理、工作流管理 |

### 设置版本

```python
from appform_sdk import AppformClient, VERSION_6_0, VERSION_6_5, VERSION_6_6

# 使用指定版本
client = AppformClient(
    base_url="https://server/appform",
    api_version="6.6",
    token="...",
)

# 使用版本常量
client = AppformClient(
    base_url="https://server/appform",
    api_version=VERSION_6_6,
)
```

### 查询版本端点

```python
# 获取当前版本的所有端点
endpoints = client.registry.get_all()

# 获取特定版本的端点
endpoints_65 = client.registry.get_for_version("6.5")
```

## 注册自定义端点

### 通过 Client 注册

```python
# 注册新端点
client.register_endpoint(
    name="custom.myEndpoint",
    path="/appform/ws/api/custom/endpoint",
    method="GET",
    description="My custom endpoint",
)

# 覆盖已有端点
client.register_endpoint(
    name="jobs.list",
    path="/appform/ws/api/custom/jobs",
    method="GET",
    override=True,
)

# 使用注册的端点
result = client.call_endpoint("custom.myEndpoint")
```

### 通过 Registry 注册

```python
from appform_sdk import APIRegistry

registry = client.registry
registry.register(
    name="custom.endpoint",
    path="/appform/ws/api/custom",
    method="GET",
    description="Custom endpoint",
    version_added="6.0",
)
```

## 扩展管理

### 从文件加载扩展

```python
# 扩展文件格式 (JSON)
# {
#   "name": "my-extension",
#   "version": "1.0.0",
#   "description": "My custom extension",
#   "endpoints": {
#     "custom.myApi": {
#       "path": "/appform/ws/api/custom",
#       "method": "GET",
#       "description": "My custom API"
#     }
#   }
# }

# 加载扩展文件
client.load_extension_file("/path/to/extension.json")

# 或从字典加载
client.load_extension({
    "name": "my-extension",
    "version": "1.0.0",
    "endpoints": {
        "custom.myApi": {
            "path": "/appform/ws/api/custom",
            "method": "GET",
        }
    },
})

# 列出已加载扩展
extensions = client.extension_manager.list_extensions()
```

### 独立使用 ExtensionManager

```python
from appform_sdk import ExtensionManager, Extension, ExtensionConfig

manager = ExtensionManager()

# 从文件加载
manager.load_from_file("/path/to/extension.json")

# 从字典加载
manager.load_from_dict({"name": "ext", "endpoints": {...}})

# 列出扩展
print(manager.list_extensions())

# 卸载扩展
manager.unregister("ext")
```

## 动态 API 调用

通过 `DynamicAPI` 可以通过端点名称调用 API。

```python
# 通过 client.api 访问动态 API
result = client.api.call("jobs.list", params={"page": 1, "pageSize": 10})

# 使用 __getattr__ 方式
result = client.api.jobs_list(params={"page": 1})
result = client.api.jobs_list(params={"page": 1})

# 传递路径参数
result = client.api.call(
    "jobs.get",
    path_params={"jobId": "12345"},
)
```

### 自定义处理器

```python
registry = client.registry

# 注册自定义处理器
def my_handler(client, params=None, **kwargs):
    return {"custom": "response"}

registry.register_handler("custom.myEndpoint", my_handler)

# 调用时自动使用处理器
result = client.api.call("custom.myEndpoint")
```

## 初始化默认 Registry

```python
from appform_sdk import init_default_registry

# 创建指定版本的 registry
registry = init_default_registry("6.6")

# 查看所有端点
for name, endpoint in registry.get_all().items():
    print(f"{name}: {endpoint.method} {endpoint.path}")
```

## CLI 使用

```bash
# 列出已加载扩展
appform extension list

# 加载扩展文件
appform extension load /path/to/extension.json

# 列出所有端点
appform endpoint list

# 列出特定版本的端点
appform endpoint list --version 6.5

# 调用端点
appform endpoint call jobs.list --params '{"page":1,"pageSize":10}'

# 调用带路径参数的端点
appform endpoint call jobs.get --path-params '{"jobId":"12345"}'
```
