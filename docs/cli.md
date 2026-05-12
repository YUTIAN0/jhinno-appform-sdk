# CLI 命令参考

`appform` 命令行工具完整参考。

## 全局选项

| 选项 | 说明 |
|------|------|
| `--version` | 显示版本号 |
| `--base-url URL` | API 基础 URL |
| `--access-key KEY` | AccessKey |
| `--access-key-secret SECRET` | AccessKey 密钥 |
| `--username USER` | 用户名 |
| `--password PASS` | 密码 |
| `--token TOKEN` | 认证 Token |
| `--api-version VER` | API 版本（默认 6.5） |
| `--config FILE` | 配置文件路径 |
| `--env ENV` | 目标环境（或设置 APPFORM_ENV） |
| `--profile-config FILE` | 作业配置文件路径 |
| `-o, --output FORMAT` | 输出格式：`raw`/`json`/`table`/`text`（默认 `table`） |
| `--output-template FILE` | 自定义输出模板文件（`.yaml`/`.yml`/`.json`） |

## 输出格式

`-o` 参数控制 CLI 输出的数据格式：

| 格式 | 说明 | 数据 |
|------|------|------|
| `table` | 表格格式（默认），人类可读 | 模板定义的字段，格式化显示 |
| `json` | JSON 格式，模板过滤后的字段 | 模板定义的字段，结构化输出 |
| `raw` | 原始格式，API 返回的完整数据 | 完整原始响应，无任何过滤 |
| `text` | 纯文本格式 | 同 table |

```bash
# 表格格式（默认）—— 只显示模板定义的字段
appform jobs list
appform -o table jobs list

# JSON 格式 —— 只输出模板定义的字段，用标签名作 key
appform -o json jobs list
# 输出: {"total": 9, "items": [{"JOB_ID": "494825", "STATUS": "RUN", ...}]}

# 原始格式 —— API 返回的完整数据，无任何过滤
appform -o raw jobs list
# 输出: {"code": 200, "result": "success", "data": {"total": 9, "jobs": [{"id": "494825", "jobId": "494825", "status": "RUN", "host": "", "queue": "debug", ...完整字段...}]}}

# 纯文本
appform -o text jobs list
```

### 输出模板

`-o table` 和 `-o json` 使用模板定义显示的字段。SDK 内置了默认模板，也可以自定义：

```bash
# 使用自定义模板文件
appform --output-template /path/to/my_template.yaml jobs list

# 通过配置文件设置默认模板
appform config set --output-template /path/to/my_template.yaml

# 通过环境变量
export APPFORM_OUTPUT_TEMPLATE=/path/to/my_template.yaml
```

自定义模板文件格式（YAML）：

```yaml
# 只显示这些字段，顺序和宽度可自定义
jobs.list:
  type: table
  title: My Jobs
  items_path: data.jobs
  total_key: data.total
  fields:
    - {key: jobId,      label: ID,        width: 10}
    - {key: status,     label: ST,        width: 5}
    - {key: name,       label: Job Name,  width: 35}
    - {key: owner,      label: User,      width: 10}
    - {key: submitTime, label: Submitted, width: 19}

jobs.get:
  type: detail
  title: Job Detail
  item_path: data
  fields:
    - {key: jobId,  label: ID}
    - {key: name,   label: Name}
    - {key: status, label: Status}
    - {key: owner,  label: Owner}
    - {key: cwd,    label: Work Dir}
```

**模板字段说明：**

| 字段 | 说明 |
|------|------|
| `type` | `table`（列表）、`detail`（键值对）、`tree`（树形） |
| `title` | 显示标题 |
| `items_path` | 数据路径（如 `data.jobs`） |
| `total_key` | 总数路径（如 `data.total`） |
| `item_path` | 单条数据路径（detail 类型） |
| `fields[].key` | 响应数据中的字段名 |
| `fields[].label` | 显示的列名/标签 |
| `fields[].width` | 列宽（table 类型） |
| `fields[].fallback` | key 为空时的备选字段 |
| `fields[].format` | 格式化：`size`（字节）、`join`（列表拼接）、`json` |
| `fields[].min_version` | 最低 API 版本（低于此版本隐藏该字段） |

## config - 配置管理

```bash
# 设置配置值
appform config set --base-url https://server
appform config set --access-key KEY --access-key-secret SECRET --username USER
appform config set --api-version 6.3
appform config set --verify-ssl false
appform config set --job-profile-config /path/to/job_submit.yaml
appform config set --output-format table
appform config set --output-template /path/to/template.yaml
appform config set --default-remote-path /home/user/
appform config set --aes-key YOUR_AES_KEY
appform config set --default-remote-path /home/user/
appform config set --chunk-size 100M

# 设置默认文件传输方式
appform config set --default-method sftp

# SFTP 配置
appform config set --sftp-host mycluster.example.com
appform config set --sftp-port 22
appform config set --sftp-key-file ~/.ssh/id_rsa

# Proxy 配置
appform config set --http-proxy http://proxy:8080
appform config set --sftp-proxy socks5://proxy:1080

# 查看当前配置
appform config show
```

### 代理配置

SDK 支持 HTTP/HTTPS 和 SFTP/SSH 连接的代理：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `http_proxy` | HTTP API 请求代理 | `http://proxy:8080` 或 `socks5://proxy:1080` |
| `sftp_proxy` | SFTP/SSH 连接代理 | `socks5://proxy:1080` 或 `http://proxy:8080` |

设置方式（优先级从高到低）：
1. 环境变量：`APPFORM_HTTP_PROXY`、`APPFORM_SFTP_PROXY`
2. 配置文件：`~/.appform/config.json` 中的 `http_proxy`、`sftp_proxy`
3. CLI：`appform config set --http-proxy URL --sftp-proxy URL`

HTTP/SOCKS 代理依赖 `PySocks`，安装方式：
```bash
pip install jhinno-appform-sdk[sftp]
```

当使用 HTTP 代理进行 SFTP 连接时，SDK 会通过 HTTP CONNECT 隧道建立 SSH 连接。

## auth - 认证

```bash
appform auth login --username USER --password PASS   # 密码登录
appform auth ping                                    # 测试连接
appform auth logout                                  # 登出
```

## jobs - 作业管理

### 查看应用和参数

```bash
appform jobs apps                                    # 列出已配置应用
appform jobs params <app_id>                         # 查看应用参数
appform jobs submit -l                               # 列出已配置应用
appform jobs submit -a <app> --help                  # 查看应用提交帮助
```

### 提交作业

```bash
# 使用应用自定义参数（兼容 job_submit.py）
appform jobs submit -a starccm -i /path/to/file.sim -n 16
appform jobs submit -a starccm -i /path/to/file.sim -r 20.02.007 -post
appform jobs submit -a nastran --cas /path/to/test.bdf --ncpu 16

# 使用 --set 覆盖参数
appform jobs submit -a starccm --set JH_CAS=/path/to/file.sim --set JH_NCPU=8

# 使用 --params JSON
appform jobs submit -a starccm --params '{"JH_CAS":"/path/to/file.sim","JH_NCPU":"8"}'

# 混合使用
appform jobs submit -a starccm -i /path/to/file.sim --set JH_NCPU=8 -r 20.02.007 -post

# 预览不提交
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run

# 原始 JSON 提交（不依赖配置文件）
appform jobs submit-raw --app-id fluent --params '{"JH_CAS":"/path/to/file.cas","JH_NCPU":"8"}'
```

### 查询作业

```bash
appform jobs list                                    # 列出当前用户作业（表格）
appform jobs list --status RUN --name test           # 带过滤
appform jobs list --job-id 494825                    # 按作业号查询
appform jobs list --job-id 494825,494824             # 多个作业号
appform -o raw jobs list                             # 原始 API 数据
appform -o json jobs list                            # 模板过滤后的 JSON
appform jobs status RUN                              # 按状态查看
appform jobs status all                              # 查看所有状态
appform jobs get <job_id>                            # 获取作业详情
appform jobs history <job_id>                        # 获取作业历史
appform jobs history-page --page 1 --page-size 20    # 分页历史
```

### 作业操作

```bash
appform jobs stop <job_id>                           # 停止作业（挂起，可恢复）
appform jobs kill <job_id>                           # 终止运行中的作业（不可恢复）
appform jobs suspend <job_id>                        # 暂停作业
appform jobs resume <job_id>                         # 恢复作业
appform jobs delete <job_id>                         # 删除作业记录（6.6+，低版本返回 405）
appform jobs output <job_id>                         # 获取作业输出
appform jobs files <job_id>                          # 获取作业文件列表
appform jobs files <job_id> ls /path/to/dir          # 列出作业文件目录
appform jobs files <job_id> tailf /path/to/file      # 跟踪作业输出文件
appform jobs files <job_id> custom ls [path]         # 列出计算节点目录
appform jobs files <job_id> custom get <remote> [local] # 下载计算节点文件
appform jobs files <job_id> custom cat <path>        # 查看计算节点文件
appform jobs files <job_id> custom tailf <path>      # 跟踪计算节点文件
appform jobs form <app_id>                           # 获取作业表单（6.6+）
appform jobs tooltip                                 # 获取作业监控信息（6.6+）
```

## sessions - 会话管理

```bash
appform sessions start --app-id gedit --start-new --cwd '${HOME}'
appform sessions start --app-id xterm --work-file /path/to/file

appform sessions list --ids 494039                   # 按 ID 查询（当前用户默认）
appform sessions list --name my_session              # 按名称查询
appform sessions list-all                            # 列出所有会话
appform sessions connect <session_id>                # 获取会话连接信息
appform sessions connect-launch <session_id>         # 连接并自动启动客户端
appform sessions disconnect <session_id>             # 断开会话
appform sessions close <session_id>                  # 关闭会话
appform sessions share <session_id> --usernames user1,user2  # 共享会话
```

## files - 文件管理

文件命令参考 Linux 文件操作风格，详见 [文件管理文档](files.md)。

```bash
# 列出远程目录
appform files ls /                          # 列出根目录
appform files ls '$HOME'                    # 列出家目录（第一行显示解析后的绝对路径）
appform files ls --all /home/user           # 列出所有（自动翻页）

# 获取远程用户家目录
appform files home                          # HTTP API 方式（默认）
appform files home --method sftp            # SFTP 方式（SSH echo ~）

# 创建远程目录
appform files mkdir /home/user/new_folder

# 复制远程文件
appform files cp /home/user/file.txt /home/user/backup/

# 移动/重命名远程文件
appform files mv /home/user/old.txt /home/user/new.txt

# 删除远程文件
appform files rm /home/user/file.txt

# 上传文件到远程
appform files put ./local_file.txt /home/user/          # 上传文件
appform files put ./local_folder /home/user/remote/     # 上传目录（含进度）

# 从远程下载文件
appform files get /home/user/file.txt                   # 下载到当前目录
appform files get /home/user/file.txt /tmp/             # 下载到指定目录
appform files get /home/user/folder ./backup/           # 下载目录（含进度）

# 查看远程文件内容
appform files cat /home/user/file.txt                   # 查看内容
appform files cat /home/user/file.txt --head 10         # 前 10 行
appform files cat /home/user/file.txt --lines 10-20     # 第 10-20 行
appform files cat /home/user/file.txt --all             # 输出所有行

# 实时跟踪文件输出（SFTP  only）
appform files tailf /home/user/output.log               # 类似 tail -f
appform files tailf /home/user/output.log --encoding gbk # 指定编码

# 压缩解压
appform files compress /home/user/folder /home/user/archive.tar.gz
appform files uncompress /home/user/archive.tar.gz /home/user/extracted/

# 文件密级
appform files conf --get-levels
appform files conf --set /home/user/file.txt secret
```

## apps - 应用管理

```bash
appform apps list                                    # 列出所有应用
```

## departments - 部门管理

```bash
appform departments list                             # 列出部门（树形）
appform departments create --name IT --display-name IT部门 --parent root      # 创建部门
appform departments create --name dev --display-name 开发部 --parent IT       # 创建子部门
appform departments update --name IT --display-name 信息技术部                # 更新部门
appform departments delete --name IT                                          # 删除部门
```

## users - 用户管理

```bash
appform users list                                   # 列出用户
appform users list --page 1 --page-size 50           # 分页列出
appform users list --dep IT                          # 按部门过滤
appform users list --filter-username admin            # 按用户名过滤

appform users create --user john --display-name John --new-password your_password
appform users create --user john --display-name John --new-password your_password --dep IT --mail john@example.com

appform users update --user john --display-name "John Doe" --mail john@example.com
appform users delete --user john
appform users reset-password --user john --new-password your_new_password
```

## extension - 扩展管理

```bash
appform extension list                               # 列出已加载扩展
appform extension load /path/to/extension.json       # 加载扩展
```

## endpoint - 端点管理

```bash
appform endpoint list                                # 列出所有端点
appform endpoint list --version 6.5                  # 列出特定版本端点
appform endpoint call jobs.list --params '{"page":1}'  # 调用端点
```
