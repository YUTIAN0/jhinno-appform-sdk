---
name: appform-cli
version: 3.0.0
description: >
  使用 appform 命令行工具或调度命令（jsub/jjobs/jctrl）提交计算作业、
  查看作业状态、获取应用列表、启动交互应用。
  当用户在终端/Shell 中操作 Appform HPC 集群时使用。
  务必在此类场景下使用此 skill，即使用户用 "提交任务"、"看作业" 等口语化表述。
---

# appform CLI 使用指南

Appform 6.0-6.6 HPC 平台，支持两种方式操作集群：

## 安装

```bash
pip install git+https://github.com/YUTIAN0/jhinno-appform-sdk.git

# SFTP 可选（文件传输使用 SFTP 时需要）
pip install "git+https://github.com/YUTIAN0/jhinno-appform-sdk.git#egg=jhinno-appform-sdk[sftp]"
```

安装后 `appform` 命令即可使用。调度命令（`jsub`/`jjobs`/`jctrl` 等）为集群自带，无需安装。

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **appform CLI**（HTTP API） | `appform jobs submit` | 集群内外均可，需认证配置 |
| **调度命令**（直连） | `jsub` / `jjobs` / `jctrl` | 集群节点上直接使用，无需 API |

详细命令参考 → [appform CLI 命令参考](reference/commands.md) | [调度命令参考](reference/scheduler.md)

---

## 认证

**禁止将密码、密钥、令牌等敏感信息发送给 AI。** 引导用户自行在终端执行配置命令。

### 配置步骤

1. 引导用户确认是否已有配置：

```bash
appform -o json config show    # 查看当前配置
```

2. 如果未配置，提示用户在终端中自行执行以下命令（不要代为执行含敏感信息的命令）：

```bash
# 方式 1：AccessKey（推荐，一次性配置）
appform config set \
  --base-url <服务器地址> \
  --access-key <用户的 AccessKey> \
  --access-key-secret <用户的 AccessKeySecret> \
  --username <用户名>

# 方式 2：用户名密码登录（每次会话）
appform auth login --username <用户名> --password <密码>
```

3. 用户配置完成后，验证连接：

```bash
appform auth ping
```

### 说明

- 环境变量：`APPFORM_BASE_URL`, `APPFORM_ACCESS_KEY`, `APPFORM_ACCESS_KEY_SECRET`, `APPFORM_USERNAME`
- 每次命令可用 `--base-url` 等参数覆盖
- **禁止直接读取 `~/.appform/config.json` 文件。始终使用 `appform -o json config show` 命令获取配置内容。**

---

## 作业提交流程（禁止跳过步骤直接提交）

```
环境检查 → 上传文件 → 确认应用 → 获取参数 → 预览确认 → 提交 → 监控 → 下载结果
    ↓                                                            ↓
 文件已在集群上                                              查看计算过程文件
（跳过上传）                                                        ↓
                                                         下载结果 / 后处理分析
```

### 步骤 1：检查环境

```bash
hostname && uname -a                    # 确认节点位置
appform files home                      # 获取集群家目录路径
```

| 环境 | 操作 |
|------|------|
| 集群内 Linux/Windows | 文件已在共享存储上，跳过步骤 2 |
| 集群外节点 | 需要上传文件，进入步骤 2 |

### 步骤 2：上传文件（集群外节点）

```bash
appform files put ./test.sim '$HOME/work/'              # 始终指定目标目录
appform files put ./test.sim '$HOME/work/' --method http  # SFTP 不可用时
```

> 省略远程路径时上传到 `/`（根目录），**必须指定 `$HOME/` 下的目录**。

设置默认路径后可省略：`appform config set --default-remote-path '$HOME/work/'`

### 步骤 3：确认应用

```bash
appform apps list                       # 查看所有应用
appform apps list | grep -i fluent      # 按关键词搜索
```

- `TYPE=batch` → 计算应用，用 `jobs submit -a <app_id>`
- `TYPE=desktop` → 交互应用，用 `sessions start --app-id <app_id>`

### 步骤 4：获取应用参数

**不同环境参数可能不同，提交前必须查询。** → [应用参数参考](reference/apps.md)

```bash
appform jobs form <app_id>              # 6.6+（推荐）
appform jobs params <app_id>            # 6.3 及以下
```

### 步骤 5：预览并确认

```bash
appform jobs submit -a <app_id> -i <远程文件路径> --dry-run
```

**用户未指定关键参数时必须询问，不要自行假设默认值。**

### 步骤 6：提交作业

```bash
appform jobs submit -a starccm -i /path/test.sim -n 32 -r 16.02
```

提交成功后记录 **job_id**。更多提交方式 → [命令参考 - 提交作业](reference/commands.md#提交作业)

### 步骤 7-10：监控 → 查看文件 → 下载结果 → 后处理

```bash
appform jobs get <job_id>                              # 查看状态
appform jobs files <job_id> cat /output.log --tail 50  # 查看输出
appform jobs files <job_id> get /result.dat ./         # 下载结果
```

状态：`RUN`(运行) / `PEND`(等待) / `DONE`(完成，终态) / `EXIT`(异常退出，终态)

---

## 常见应用

→ [应用参数参考](reference/apps.md) | [StarCCM+](apps/starccm.md) | [Fluent](apps/fluent.md) | [LS-DYNA](apps/ls-dyna.md)

---

## 后处理脚本

```bash
# 方式 1：post-exec 自动触发
jsub -Ep post_script.sh -a starccm -i /path/test.sim -n 16

# 方式 2：监控完成后手动执行
appform jobs list --status DONE && ./post_process.sh <job_id> <result_dir>
```

---

## 命令索引

| 分类 | 详情 |
|------|------|
| appform CLI 命令 | [commands.md](reference/commands.md) — 提交、查看、控制、文件、会话 |
| 调度命令（jsub 等） | [scheduler.md](reference/scheduler.md) — jsub/jjobs/jctrl/jhist |
| 应用参数 | [apps.md](reference/apps.md) — 参数查询方法 + 各应用文档 |
| 全局选项 | `--base-url`, `--access-key`, `-o json/raw/table/text`, `--env` |
