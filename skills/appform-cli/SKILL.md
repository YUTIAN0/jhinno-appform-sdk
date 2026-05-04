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

提交前先查询需要哪些参数、是否必填、默认值是什么。两种方式：

```bash
# 方式 1 — 从 YAML 配置文件查询（基于本地 profile，推荐）
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

# 方式 2 — 从服务器 API 查询表单（6.6+）
appform jobs form starccm
appform -o json jobs form starccm             # JSON 格式，便于解析
```

YAML 配置文件路径：`~/.appform/config.json` 中的 `job_profile_config` 字段，或环境变量 `APPFORM_JOB_PROFILE_CONFIG`。

### 提交

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
appform jobs stop 1001
appform jobs suspend 1001
appform jobs resume 1001
appform jobs delete 1001

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
appform files ls /home/user
appform files ls /home/user --all          # 自动分页列出所有
appform files ls /home/user --method sftp
appform files ls /home/user --method sftp -A  # 显示隐藏文件

# 上传 / 下载
appform files put local.txt /remote/path
appform files get /remote/file ./local

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
