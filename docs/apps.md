# 应用管理

AppsAPI 提供应用信息查询功能。

## 获取应用列表

### 基础列表（6.0+）

```python
# 获取所有应用
apps = client.apps.list_all()
```

### V2 列表（6.6+）

```python
# 获取可用的计算、交互、web 应用
apps = client.apps.list_v2()
```

## 获取应用信息

```python
# 获取应用 URL
url_info = client.apps.get_url("fluent")

# 获取计算应用表单参数
params = client.apps.get_form_params("app_id")

# 获取图形应用关联的文件后缀
extensions = client.apps.get_file_extensions()
```

## CLI 使用

```bash
# 列出所有应用
appform apps list

# 获取应用 URL
# (通过 endpoint call)
appform endpoint call apps.url --path-params '{"appName":"fluent"}'
```
