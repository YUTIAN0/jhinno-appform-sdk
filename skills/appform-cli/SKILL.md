---
name: appform-cli
description: 使用 appform 命令行工具提交计算作业、查看作业状态、获取应用列表、启动交互应用。当用户在终端/Shell 中操作 Appform HPC 集群、使用 appform 命令时使用。务必在此类场景下使用此 skill，即使用户用 "提交任务"、"看作业" 等口语化表述。
---

# appform CLI 使用指南

Appform 6.0-6.6 HPC 平台的命令行工具。

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

## 提交作业

### 查询作业提交参数

提交前先查询需要哪些参数、是否必填、默认值是什么。

**先确认 API 版本**（影响参数查询方式）：

```bash
appform -o json config show    # 查看 api_version 字段
```

**6.6+ 版本 —— 优先使用服务器 API 查询表单**（参数与服务端同步，最准确）：

```bash
appform jobs form starccm                      # 查看 starccm 的参数表
appform -o json jobs form starccm              # JSON 格式，便于解析
```

**6.3 及以下版本 —— 使用 YAML 配置文件查询**：

```bash
appform jobs apps                             # 列出支持的应用
appform jobs params starccm                   # 查看 starccm 的参数表
# 输出示例：
# Application: starccm - STAR-CCM+
# Parameter        Type     Required Default      CLI Arg       Short  Description
# JH_CAS           upload   Yes                   input         -i     算例文件路径
# JH_NCPU          text     No       1            ncpu          -n     节点数
# JH_RELEASE       select   No       16.02        release       -r     软件版本
# STAR_POST_SWITCH switch   No       off          post          -post  是否启用后处理
# ...（更多参数）
```

YAML 配置文件路径：`~/.appform/config.json` 中的 `job_profile_config` 字段，或环境变量 `APPFORM_JOB_PROFILE_CONFIG`。

> 两种方式均可用于提交，`appform jobs submit` 会自动读取 YAML profile 生成参数。区别在于：6.6+ 的 `jobs form` 返回的是服务端最新表单定义，YAML 配置可能与服务端不同步。

### 提交

> **注意**：`-i`、`--set JH_CAS=...` 等参数中的文件路径必须是集群共享存储上的路径。集群外节点需先上传再提交（见下方）。

**两种提交方式：**

| 方式 | 依赖 | 适用场景 |
|------|------|---------|
| `appform jobs submit -a <app>` | 需要 YAML profile（`job_profile_config`） | 有配置文件的环境，自动生成参数 |
| `appform jobs submit-raw --app-id <app> --params '{...}'` | 无依赖 | 6.6+ 或无 YAML profile 时，直接传 JSON 参数 |

> **重要**：`appform jobs submit -a <app>` 从本地 YAML profile 文件读取应用配置。如果 `job_profile_config` 未配置或 profile 中没有该应用，会报 `Unknown application` 错误。此时应使用 `submit-raw` 方式。

**`$HOME` 路径变量：**

集群上 `$HOME` 表示当前用户的主目录（如 `/public3/homes/username`）。查看实际路径：

```bash
appform files home                          # 输出家目录绝对路径（HTTP API，支持所有版本）
appform files home --method sftp            # SFTP 方式（SSH echo ~）
```

在路径中使用时必须用**单引号**防止本地 shell 展开：

```bash
# 正确 — 单引号防止 $HOME 被本地 shell 替换
appform files put ./test.sim '$HOME/simulations/'
appform files ls '$HOME/'
appform jobs files 1001 get '$HOME/output.log'

# 错误 — 双引号或无引号会导致 $HOME 被本地 shell 展开为空或本地路径
appform files put ./test.sim "$HOME/simulations/"    # 本地 $HOME，非集群
appform files put ./test.sim $HOME/simulations/      # 同上
```

> 可通过 `config set --default-remote-path '$HOME/'` 设置默认远程路径，后续操作无需每次指定。

**集群外节点（Windows / Linux）—— 先上传再提交：**

```bash
# 1. 上传本地文件到集群共享存储（始终指定目标目录，避免上传到根目录）
appform files put ./test.sim '$HOME/simulations/'
# 省略远程路径时上传到 /（根目录），不是期望行为

# 2. 用远程路径提交作业（有 YAML profile 时）
appform jobs submit -a starccm \
  -i /public3/homes/user/simulations/test.sim \
  -n 32 -r 16.02

# 2. 用远程路径提交作业（无 YAML profile 或 6.6+ 时）
appform jobs submit-raw --app-id starccm \
  --params '{"JH_CAS":"/public3/homes/user/simulations/test.sim","JH_NCPU":"32","JH_RELEASE":"16.02"}'
```

**集群内节点 —— 直接提交：**

文件已在共享存储上，直接使用远程路径。根据是否有 YAML profile 选择 `submit` 或 `submit-raw`：

```bash
# 有 YAML profile
appform jobs submit -a starccm \
  -i /home/user/simulations/test.sim \
  -n 32 -r 16.02

# 无 YAML profile / 6.6+（6.6 可先用 jobs form 查看参数）
appform jobs form starccm                                # 查看可用参数
appform jobs submit-raw --app-id starccm \
  --params '{"JH_CAS":"/home/user/simulations/test.sim","JH_NCPU":"32","JH_ITERATION":"100"}'
```

**集群内 Windows 节点 —— 路径自动转换：**

Windows 路径会根据 `job_profile_config` YAML 中的 `windows_disk_mapping` 自动转换：

```bash
# 本地路径 S:\project\test.sim 自动转换为 /apps/project/test.sim
appform jobs submit -a starccm -i S:\project\test.sim -n 32
# 输出: Path conversion: S:\project\test.sim -> /apps/project/test.sim
```

> **传输方式**：SFTP 连接失败时可用 `--method http` 代替。

```bash
# 使用应用专用参数（由 YAML profile 自动生成）
appform jobs submit -a starccm \
  -i /home/user/simulations/test.sim \
  -n 32 -r 16.02

# 使用 --set 覆盖任意 JH_* 参数
appform jobs submit -a starccm \
  --set JH_JOB_NAME=cfd_run \
  --set JH_CAS=/home/user/simulations/test.sim \
  --set JH_NCPU=32 \
  --set JH_RELEASE=16.02 \
  --set JH_NODE_GROUP=batch

# 启用后处理
appform jobs submit -a starccm \
  -i /home/user/simulations/test.sim -n 32 \
  -post on -j2 /scripts/post.py -n2 8

# 预览参数而不提交
appform jobs submit -a starccm --dry-run -i /home/user/simulations/test.sim

# 查看应用的完整帮助
appform jobs submit -a starccm --help

# 列出所有支持的应用
appform jobs submit -l

# 直接提交（传 JSON）
appform jobs submit-raw --app-id starccm \
  --params '{"JH_JOB_NAME":"test","JH_CAS":"/path/file.sim","JH_NCPU":"8"}'
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
appform files put local.txt /remote/path     # 不指定远程路径时上传到 /（根目录）
appform files put local.txt /remote/path/newname.txt  # 远程路径不以 / 结尾时，作为文件目标路径（重命名）
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
