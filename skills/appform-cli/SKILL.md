---
name: appform-cli
description: 使用 appform 命令行工具提交计算作业、查看作业状态、获取应用列表、启动交互应用。当用户在终端/Shell 中操作 Appform HPC 集群、使用 appform 命令时使用。务必在此类场景下使用此 skill，即使用户用 "提交任务"、"看作业" 等口语化表述。
---

# appform CLI 使用指南

Appform 6.0-6.6 HPC 平台的命令行工具。

## 作业提交流程

提交计算作业的完整流程，按步骤执行。**禁止跳过步骤直接提交。**

```
环境检查 → 上传文件 → 确认应用 → 获取参数 → 预览确认 → 提交 → 监控状态
    ↓                                                            ↓
 文件已在集群上                                              查看计算过程文件
（跳过上传）                                                        ↓
                                                         下载结果 / 后处理分析
```

### 步骤 1：检查环境

确认当前节点位置和操作系统，决定是否需要上传文件：

```bash
# 确认当前节点是否在集群内（集群内节点通常可直接访问共享存储）
hostname && uname -a
# Linux 集群内节点：文件路径直接使用共享存储路径（如 /home/user/file.sim）
# 集群外节点（Windows/Linux）：需要先上传文件到集群

# 确认集群家目录路径
appform files home                          # HTTP API 方式
appform files home --method sftp            # SFTP 方式
```

**环境判断结果：**

| 环境 | 操作 |
|------|------|
| 集群内 Linux 节点 | 文件已在共享存储上，跳过步骤 2，直接步骤 3 |
| 集群内 Windows 节点 | 路径自动转换（`S:\` → `/apps/`），跳过步骤 2 |
| 集群外节点（Linux/Mac） | 需要上传文件，进入步骤 2 |
| 集群外节点（Windows） | 需要上传文件，进入步骤 2 |

### 步骤 2：上传文件

集群外节点需先将本地文件上传到集群共享存储。

```bash
# 上传文件到家目录下的工作目录（始终指定目标目录，省略路径会上传到 /）
appform files put ./test.sim '$HOME/simulations/'

# 上传多个文件
appform files put ./case.cas '$HOME/work/'
appform files put ./data.dat '$HOME/work/'

# 上传整个目录
appform files put ./project_dir '$HOME/work/'

# SFTP 不可用时使用 HTTP 方式
appform files put ./test.sim '$HOME/simulations/' --method http
```

> 远程路径以 `/` 结尾保留原文件名，不以 `/` 结尾作为文件目标路径（可重命名）。
> 省略远程路径时上传到 `/`（根目录），不是期望行为，**必须指定 `$HOME/` 下的目录**。

上传完成后记录远程路径，后续提交时使用。可通过 `appform files home` 获取家目录前缀：

```bash
appform files home                          # 例：/public3/homes/username
# 远程路径 = 家目录 + 上传目录 + 文件名
# 例：/public3/homes/username/simulations/test.sim
```

**设置默认远程路径（推荐）：**

每次指定 `$HOME/simulations/` 很繁琐。设置 `default_remote_path` 后，省略远程路径时自动使用该目录：

```bash
# 设置默认远程路径
appform config set --default-remote-path '$HOME/work/'

# 设置后，以下两条命令等价：
appform files put ./test.sim                          # 自动使用 $HOME/work/
appform files put ./test.sim '$HOME/work/'

# 查看当前配置
appform -o json config show    # 检查 default_remote_path 字段
```

| 设置方式 | 示例 |
|----------|------|
| CLI 配置 | `appform config set --default-remote-path '$HOME/work/'` |
| 环境变量 | `export APPFORM_DEFAULT_REMOTE_PATH='$HOME/work/'` |
| 配置文件 | `~/.appform/config.json` 中 `"default_remote_path": "$HOME/work/"` |

> 优先级：CLI 参数（`--default-remote-path`）> 环境变量（`APPFORM_DEFAULT_REMOTE_PATH`）> 配置文件（`default_remote_path` 字段）。默认值为 `/`。
>
> 注意：`default_remote_path` 只在省略远程路径时生效。如果命令中已指定远程路径（如 `appform files put ./file.txt /other/path/`），不会使用默认值。

### 步骤 3：确认应用

确定使用哪个应用提交作业。应用类型决定了操作方式：

```bash
# 列出所有应用
appform apps list
```

| TYPE | 用途 | 操作 |
|------|------|------|
| `batch` | 计算应用（starccm、fluent 等） | `jobs submit -a <app_id>` |
| `desktop` | 交互应用（meta_post、ParaView 等） | `sessions start --app-id <app_id>` |
| 无 TYPE | 管理入口（应用仓库、我的数据等） | 不用于提交或会话 |

```bash
# 按关键词搜索应用
appform apps list | grep -i fluent
appform apps list | grep -i post

# 如果关键词未匹配，扩大搜索范围
appform apps list | grep -i ls-dyna
appform apps list | grep -i dyna        # 去掉前缀重试
```

### 步骤 4：获取应用参数

查询应用需要哪些参数、哪些是必填、默认值是什么。

**6.6+ 版本 —— 优先使用服务器 API（参数与服务端同步）：**

```bash
appform jobs form <app_id>                      # 表格形式
appform -o json jobs form <app_id>              # JSON 格式
```

**6.3 及以下版本 —— 使用 YAML 配置文件：**

```bash
appform jobs params <app_id>
# 输出示例：
# Parameter        Type     Required Default      CLI Arg       Short  Description
# JH_CAS           upload   Yes                   input         -i     算例文件路径
# JH_NCPU          text     No       1            ncpu          -n     节点数
```

**确认 API 版本：**

```bash
appform -o json config show    # 查看 API Version 字段
```

### 步骤 5：预览并确认参数

**必须先用 `--dry-run` 预览参数，用户确认后再提交：**

```bash
appform jobs submit -a <app_id> -i <远程文件路径> --dry-run
```

如果用户未指定关键参数（CPU 数、队列、版本等），**必须先询问**，不要自行假设默认值。

预览确认后，去掉 `--dry-run` 执行提交。

### 步骤 6：提交作业

```bash
# 方式 1：使用应用参数（需要 YAML profile）
appform jobs submit -a starccm -i /path/test.sim -n 32 -r 16.02

# 方式 2：使用 --set 覆盖任意参数
appform jobs submit -a starccm \
  --set JH_CAS=/path/test.sim \
  --set JH_NCPU=32 \
  --set JH_RELEASE=16.02

# 方式 3：原始 JSON 提交（无 YAML profile 或 6.6+）
appform jobs submit-raw --app-id starccm \
  --params '{"JH_CAS":"/path/test.sim","JH_NCPU":"32"}'
```

提交成功后记录返回的 **job_id**，后续步骤均需要。

### 步骤 7：监控作业状态

```bash
# 查看单个作业状态
appform jobs get <job_id>                # 详情中 Status 字段

# 按状态过滤列表
appform jobs list --status RUN           # 运行中
appform jobs list --status PEND          # 等待中
appform jobs list --job-id <job_id>      # 按 ID 查询
```

**状态含义：**

| 状态 | 说明 | 是否终态 |
|------|------|---------|
| `RUN` | 运行中 | 否 |
| `PEND` | 排队等待 | 否 |
| `PSUSP`/`USUSP`/`SSUSP` | 挂起 | 否 |
| `DONE` | 正常完成 | 是 |
| `EXIT` | 异常退出 | 是 |
| `ZOMBI` | 异常 | 是 |

非终态需要继续轮询。终态后进入步骤 8。

### 步骤 8：查看计算过程中的文件

作业运行中可实时查看计算进度和输出：

```bash
# 列出作业目录文件
appform jobs files <job_id> ls

# 查看输出文件内容
appform jobs files <job_id> cat /output.log --tail 50

# 实时跟踪输出文件（类似 tail -f，Ctrl+C 停止）
appform jobs files <job_id> tailf /output.log

# 通过计算节点 SSH 操作（需 ~/.appform/compute.yaml）
appform jobs files <job_id> custom ls
appform jobs files <job_id> custom cat /work_path/output.log --tail 50
appform jobs files <job_id> custom tailf /work_path/output.log
```

### 步骤 9：下载结果文件

作业完成后（`DONE`）下载结果：

```bash
# 查看作业输出摘要
appform jobs output <job_id>

# 列出结果文件
appform jobs files <job_id> ls

# 下载单个文件到当前目录
appform jobs files <job_id> get /result.dat ./

# 下载到指定目录
appform jobs files <job_id> get /result.dat /local/results/

# 下载整个目录
appform jobs files <job_id> get /output/ ./job_results/
```

### 步骤 10：分析结果

下载结果后，可启动交互应用进行后处理分析：

```bash
# 查找后处理应用（desktop 类型）
appform apps list | grep -i post
appform apps list | grep -i view

# 启动后处理应用并加载结果文件
appform sessions start --app-id meta_post --start-new --work-file '$HOME/output/result.dat'

# 不指定文件直接启动
appform sessions start --app-id abaqus_cae --start-new

# 连接并启动 JHApp 客户端
appform sessions connect-launch <session_id>

# 如果 JHApp 未安装，connect-launch 会返回 jhappUrl / webUrl，直接输出给用户
```

## 直接启动交互应用

用户要求打开可视化/后处理工具时（无需先提交计算任务），从步骤 3 开始：

```bash
# 查找应用
appform apps list | grep -i <关键词>

# 启动会话
appform sessions start --app-id <app_id> --start-new
appform sessions start --app-id <app_id> --start-new --work-file '$HOME/data/result.dat'

# 连接
appform sessions connect-launch <session_id>
```

## 认证

方式 1：配置 AccessKey（推荐，写入 `~/.appform/config.json`）：

```bash
appform config set \
  --base-url https://appform.example.com \
  --access-key YOUR_KEY \
  --access-key-secret YOUR_SECRET \
  --username your_username
```

方式 2：用户名密码登录（每次会话）：

```bash
appform auth login --username user --password pass
appform auth ping     # 测试认证
appform auth logout
```

也可用环境变量：`APPFORM_BASE_URL`, `APPFORM_ACCESS_KEY`, `APPFORM_ACCESS_KEY_SECRET`, `APPFORM_USERNAME`。每次命令可用 `--base-url` 等参数覆盖。

查看当前配置：

```bash
appform -o json config show
```

**禁止直接读取 `~/.appform/config.json` 文件。始终使用 `appform -o json config show` 命令获取配置内容。**

## 多环境配置

在单个配置文件中管理多个环境，通过 `--env` 参数或 `APPFORM_ENV` 环境变量切换：

```bash
# 切换环境
appform --env prod jobs list
appform --env dev jobs list

# 保存配置到指定环境
appform config set --environment prod --base-url https://prod.jhinno.com --api-version 6.6
appform config set --environment dev --base-url https://dev.jhinno.com --api-version 6.6

# 查看指定环境的配置
appform --env prod -o json config show

# 环境选择优先级：--env 参数 > APPFORM_ENV 环境变量 > config.json default_environment > 根级别配置
```

## SFTP 主机密钥

首次 SFTP 连接时会验证 SSH 主机密钥。默认交互提示，设置 `auto_add_host_key=true` 可自动接受（适合自动化场景）。密钥保存在 `~/.appform/known_hosts`。

```bash
appform config set --auto-add-host-key true
appform config set --auto-add-host-key false   # 恢复提示模式
```

## 返回数据说明

CLI 默认输出格式化的表格（table），便于直接阅读。与 SDK 不同，CLI 对原始 JSON 进行了列提取和排版处理。可通过 `-o` 参数切换格式，`-o` 必须放在 `appform` 之后、子命令之前：

| `-o` 值 | 输出 |
|---|---|
| `table` (默认) | 格式化表格 |
| `json` | 结构化的 JSON（CLI 处理后） |
| `raw` | 接口原始 JSON（与 SDK 返回一致） |
| `text` | 纯文本 |

```bash
appform -o raw jobs list    # 查看原始 JSON
appform -o json jobs list    # 结构化 JSON
```

## 查看作业

```bash
# 作业列表
appform jobs list
appform jobs list --page 1 --page-size 50
appform jobs list --status RUN          # 按状态过滤
appform jobs list --name cfd            # 按名称过滤
appform jobs list --job-id 1001,1002    # 按 ID 查询

# 按状态查看
appform jobs status RUN

# 单个作业详情
appform jobs get 1001

# 作业输出
appform jobs output 1001

# 作业控制
appform jobs stop 1001          # 挂起作业（PSUSP），可 resume 恢复
appform jobs kill 1001          # 终止运行中的作业，不可恢复
appform jobs suspend 1001       # 挂起（同 stop）
appform jobs resume 1001        # 恢复挂起的作业
appform jobs delete 1001        # 删除作业记录（仅 6.6+，低版本返回 405）

# 历史作业
appform jobs history 1001
appform jobs history-page --page 1 --page-size 20
```

## 作业文件管理

```bash
# 列出作业目录
appform jobs files 1001 ls
appform jobs files 1001 ls /path/inside/job

# 上传 / 下载
appform jobs files 1001 put local.txt
appform jobs files 1001 put local.txt /remote/path
appform jobs files 1001 get /remote/file ./local

# 查看文件内容
appform jobs files 1001 cat /path/to/file --head 20
appform jobs files 1001 cat /path/to/file --lines 10-

# 重命名 / 移动 / 删除
appform jobs files 1001 mv /old /new
appform jobs files 1001 cp /src /dst
appform jobs files 1001 rm /path/to/file
appform jobs files 1001 mkdir /new/dir

# 计算节点 SSH 操作（需 ~/.appform/compute.yaml）
appform jobs files 1001 custom ls
appform jobs files 1001 custom cat /path/to/log
appform jobs files 1001 custom get /remote ./local
appform jobs files 1001 custom tailf /path/to/output.log

# 传输方式指定
appform jobs files 1001 ls --method sftp        # 单个命令指定
appform jobs files --method sftp 1001 ls        # 组级别默认所有子命令
```

## 获取应用列表

```bash
appform apps list
# 输出示例（TYPE 列区分应用类型）：
# APP_ID             NAME               TYPE      PROTOCOL
# starccm_aero       Starccm+ aero      batch               # 计算应用 — 用于 jobs submit
# abaqus_cae         Abaqus CAE 2023    desktop   jhapp     # 交互应用 — 用于 sessions start
# ansa22             ansa22.1.0         desktop   jhapp
# common_submit      通用计算             batch
# cluster_node_monitor 集群状态                            # 管理应用
```

- `TYPE=batch` — 计算应用，用 `jobs submit -a <app_id>` 提交作业
- `TYPE=desktop` — 交互应用，用 `sessions start --app-id <app_id>` 启动会话
- 没有 TYPE 的行 — 管理入口（应用仓库、我的数据等），不用于提交或会话

## 启动交互应用

```bash
# 启动会话 — app_id 从 apps list 的 TYPE=desktop 行获取
appform sessions start --app-id abaqus_cae --start-new
appform sessions start --app-id ansa22 --start-new --cwd ${HOME}

# 查看当前用户会话
appform sessions list

# 精确查询
appform sessions list --ids sid1,sid2
appform sessions list --name abaqus_cae

# 所有会话（含其他用户）
appform sessions list-all --page 1 --page-size 20

# 连接（获取连接信息）
appform sessions connect session_id

# 连接并自动启动 JHApp 客户端
appform sessions connect-launch session_id

# 断开 / 关闭
appform sessions disconnect session_id
appform sessions close session_id

# 分享会话
appform sessions share session_id --usernames user2,user3
```

`sessions start` 启动后若返回 jhappUrl，CLI 会自动尝试启动本地 JHApp 客户端，无客户端时静默降级。

## 文件操作（全局）

```bash
# 列出远程目录
# ls 输出第一行自动打印解析后的绝对路径（$HOME → /public3/homes/username）
appform files ls '$HOME'
# 输出示例：
#   /public3/homes/username        ← 解析后的绝对路径
# NAME              OWNER     SIZE      MODIFIED
# [D] simulations   user      4.0KB     2026-05-10
# [F] test.sim      user      1.9MB     2026-05-12

appform files ls '$HOME' --all           # 自动分页列出所有
appform files ls '$HOME' --method sftp   # SFTP 方式（SSH 端口开放时可用）
appform files ls '$HOME' --method http   # HTTP 方式（默认，SSH 不可用时用此方式）

# 上传 / 下载
appform files put local.txt /remote/path     # 指定远程路径
appform files put local.txt /remote/path/newname.txt  # 远程路径不以 / 结尾时，作为文件目标路径（重命名）
appform files put local.txt                   # 省略路径时使用 default_remote_path（未设置则上传到 /）
appform files get /remote/file ./local
appform files put local.txt '$HOME/simulations/'
appform files put local.txt /remote/path --method http  # SFTP 不可用时用 HTTP 上传

# 创建目录 / 复制 / 移动 / 删除
appform files mkdir /new/dir
appform files cp /src /dst
appform files mv /old /new
appform files rm /path/to/file

# 查看文件内容
appform files cat /path/to/file --tail 10 --encoding utf-8

# 压缩 / 解压
appform files compress /source/dir /path/to/archive.tar.gz
appform files uncompress /path/to/archive.tar.gz /dest/dir

# 密级
appform files conf --get-levels
appform files conf --set /path/to/file 机密
```

## 常用全局选项

| 选项 | 说明 |
|---|---|
| `--base-url URL` | API 地址 |
| `--access-key KEY` | 访问密钥 |
| `--access-key-secret SECRET` | 密钥 |
| `--username USER` | 用户名 |
| `--token TOKEN` | 认证令牌 |
| `--api-version VER` | API 版本 |
| `-o FORMAT` | 输出格式 json/raw/table/text |
| `--config PATH` | 指定配置文件 |
