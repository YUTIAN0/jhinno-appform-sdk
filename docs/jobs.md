# 作业管理

JobsAPI 提供作业的提交、查询、操作等功能。

## 作业状态

| 状态 | 值 | 说明 |
|------|------|------|
| 运行 | `RUN` | 作业正在运行 |
| 等待 | `PEND` | 作业排队等待中 |
| 状态不明 | `UNKNOWN` | 作业状态不明 |
| 等待中挂起 | `PSUSP` | 排队等待中被挂起 |
| 用户挂起 | `USUSP` | 被用户挂起 |
| 系统挂起 | `SSUSP` | 被系统挂起 |
| 僵尸 | `ZOMBI` | 僵尸状态（异常） |
| 完成 | `DONE` | 作业正常完成 |
| 退出 | `EXIT` | 作业异常退出 |

终态（`--wait` 模式下结束等待）：`DONE`（成功）、`EXIT`（失败）、`ZOMBI`（异常）

## 提交作业

### 基础提交（6.0+）

使用 `multipart/form-data` 方式提交，需要传入 `appId` 和 `params`（JSON 字符串）。

```python
result = client.jobs.submit(
    app_id="fluent",
    params={
        "JH_JOB_NAME": "test_job",
        "JH_CAS": "/home/user/cases/test.cas",
        "JH_NCPU": "8",
        "JH_ITERATION": "100",
        "JH_GUI_ENABLED": "off",
    },
)
print(result)  # 包含 jobid
```

常用参数说明：

| 参数 | 说明 |
|------|------|
| `JH_JOB_NAME` | 作业名称 |
| `JH_CAS` | 算例文件路径（必填） |
| `JH_DAT` | 其他输入文件路径 |
| `JH_NCPU` | CPU 核数（默认 2） |
| `JH_PROJECT` | 项目名称（默认 default） |
| `JH_RELEASE` | 应用版本 |
| `JH_GUI_ENABLED` | 图形界面（on/off） |
| `JH_JOB_CONF` | 作业密级 |
| `JOB_PRIORITY` | 优先级（normal/high） |

### V2 提交（6.6+）

使用 `application/json` 方式提交。参数结构可通过 `get_form()` 获取。

```python
# 1. 获取作业表单（查看可用参数）
form = client.jobs.get_form("fluent")
print(form)

# 2. 提交作业
result = client.jobs.submit_v2(
    app_id="fluent",
    params={
        "JH_CAS": "/home/user/cases/test.cas",
        "JH_NCPU": "8",
        "JH_ITERATION": "100",
    },
)
```

### 通过配置文件提交

使用 `JobProfileManager` 自动加载应用参数定义，填充默认值：

```python
from appform_sdk import JobProfileManager

pm = JobProfileManager("/path/to/job_submit.yaml")
result = pm.submit_job(
    client=client,
    app_id="starccm",
    overrides={"JH_CAS": "/path/to/file.sim", "JH_NCPU": "16"},
)
```

详见 [作业配置文件](job-profiles.md)。

## 查询作业

### 分页查询

```python
# 基础查询
result = client.jobs.list_jobs(page=1, page_size=20)

# 带过滤条件
result = client.jobs.list_jobs(
    page=1,
    page_size=20,
    name_filter="test",
    status_filter=["RUN", "PEND"],
)

# 按应用名过滤
result = client.jobs.list_jobs(app_name_filter="fluent")

# 按队列过滤
result = client.jobs.list_jobs(queue_filter="normal")
```

### 查询单个作业

```python
job = client.jobs.get_job("job_id_123")
```

### 批量查询

```python
jobs = client.jobs.list_jobs_by_ids(["job_id_1", "job_id_2", "job_id_3"])
```

### 查询历史作业

```python
# 分页查询历史
history = client.jobs.list_history(page=1, page_size=20)

# 获取历史作业总数（6.6+）
count = client.jobs.get_total_history_count()
```

### V2 查询（6.6+）

```python
result = client.jobs.list_jobs_v2(page=1, page_size=20)
```

## 作业操作

```python
# 停止（挂起，可 resume 恢复）
client.jobs.stop("job_id")

# 终止运行中的作业（不可恢复）
client.jobs.kill("job_id")

# 暂停
client.jobs.suspend("job_id")

# 恢复
client.jobs.resume("job_id")

# 重新排队
client.jobs.requeue("job_id")

# 删除作业记录（6.6+，低版本返回 405）
client.jobs.delete_job("job_id")
```

### 批量操作

```python
client.jobs.batch_stop(["job_id_1", "job_id_2"])
client.jobs.batch_kill(["job_id_1", "job_id_2"])
client.jobs.batch_suspend(["job_id_1", "job_id_2"])
client.jobs.batch_resume(["job_id_1", "job_id_2"])
client.jobs.batch_requeue(["job_id_1", "job_id_2"])
```

## 获取作业输出

```python
# 动态输出
output = client.jobs.get_output("job_id")

# 作业文件列表
files = client.jobs.get_files("job_id")

# 作业历史
history = client.jobs.get_history("job_id")

# 批量历史
histories = client.jobs.get_batch_history(["job_id_1", "job_id_2"])
```

## 连接作业图形

```python
info = client.jobs.connect("job_id")
```

## 作业监控（6.6+）

```python
tooltip = client.jobs.get_tooltip()
```

## 作业表单（6.6+）

```python
form = client.jobs.get_form("fluent")
```

## CLI 使用

```bash
# 列出已配置应用
appform jobs apps
appform jobs submit -l

# 查看应用参数
appform jobs params starccm
appform jobs submit -a starccm --help

# 提交作业（使用应用自定义参数，兼容 job_submit.py）
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run
appform jobs submit -a starccm -i /path/to/file.sim -n 8 -r 20.02.007
appform jobs submit -a starccm -i /path/to/file.sim -n 8 -post

# 提交作业（使用 --set）
appform jobs submit -a starccm --set JH_CAS=/path/to/file.sim --set JH_NCPU=8

# 提交作业（原始 JSON）
appform jobs submit-raw --app-id fluent --params '{"JH_CAS":"/path/to/file.cas","JH_NCPU":"8"}'

# 查询作业
appform jobs list
appform jobs list --status RUN --name test

# 按状态查看
appform jobs status RUN
appform jobs status all

# 获取作业详情
appform jobs get <job_id>

# 作业操作
appform jobs stop <job_id>
appform jobs kill <job_id>                           # 终止（不可恢复）
appform jobs suspend <job_id>
appform jobs resume <job_id>

# 获取输出
appform jobs output <job_id>
appform jobs files <job_id>
appform jobs files <job_id> tailf /path/to/file      # 跟踪作业输出文件
appform jobs files <job_id> custom ls [path]         # 计算节点目录
appform jobs files <job_id> custom get <remote> [local] # 下载计算节点文件
appform jobs files <job_id> custom cat <path>        # 查看计算节点文件
appform jobs files <job_id> custom tailf <path>      # 跟踪计算节点文件
appform jobs history <job_id>
appform jobs history-page --page 1 --page-size 20

# 删除作业（6.6+）
appform jobs delete <job_id>

# 获取作业表单（6.6+）
appform jobs form fluent
```
