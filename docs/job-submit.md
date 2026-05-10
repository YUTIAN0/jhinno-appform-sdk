# job_submit 快速开始

`job_submit` 是 Appform SDK 提供的通用作业提交工具。它从 YAML 配置文件读取应用参数定义，支持自定义 CLI 短参数/长参数，并在提交前自动处理本地文件上传。

## 安装

```bash
pip install jhinno-appform-sdk
```

## 快速开始

```bash
# 列出已配置的应用
job_submit -l

# 查看应用参数帮助
job_submit -a starccm -h

# 提交作业（文件已在远程映射路径下）
job_submit -a starccm -i /apps/project/file.sim -n 16

# 提交作业（自动上传本地文件）
job_submit -a starccm -i /local/file.sim -n 8

# 上传到指定远程目录
job_submit -a starccm -i /local/file.sim -n 8 --upload-path /custom/path

# 提交并等待完成（默认每 10 分钟查询一次）
job_submit -a starccm -i /local/file.sim -n 8 --wait

# 提交并等待完成（每 5 分钟查询一次）
job_submit -a starccm -i /local/file.sim -n 8 --wait 5

# 使用用户名密码认证
job_submit -a starccm -i /local/file.sim -n 8 -u username -p password
```

## 文件上传

当 `param_type: upload` 类型的参数指定的文件不在远程映射路径下时，`job_submit` 会自动上传文件后再提交作业。

### 自动上传规则

1. 检查所有 `upload` 类型参数的文件路径
2. 通过 `windows_disk_mapping` 配置的目标路径（如 `/apps`, `/data`）判断文件是否已在远程
3. 不在映射路径下的文件自动上传
4. 上传后自动替换为远程路径

### 上传目标路径

| 方式 | 路径 |
|------|------|
| `--upload-path /path` | 指定的远程目录 |
| 未指定 | `$HOME/<YYYYMMDD_HHMMSS>/` |

### 多文件和目录

```bash
# 上传多个文件（逗号分隔）
job_submit -a starccm -i /local/file1.sim,/local/file2.dat -n 8

# 上传整个目录
job_submit -a starccm -i /local/project_dir/ -n 8
```

### 传输方式

文件上传方式跟随 `APPFORM_DEFAULT_METHOD` 配置：
- `http`（默认）：通过 Appform API 上传，服务端解析 `$HOME`
- `sftp`：通过 SFTP 直连上传，自动获取远端家目录

## 配置文件

`job_submit.yaml` 示例：

```yaml
job_submit_config:
  appform_base_url: https://your-server.com/appform
  windows_disk_mapping:
    'S:': '/apps'
    'D:': '/data'
  applications:
    starccm:
      name: STAR-CCM+
      parameters:
        - name: JH_CAS
          type: upload
          required: true
          cli_arg: input
          short_arg: i
          description: 算例文件路径
        - name: JH_NCPU
          type: text
          default: '2'
          cli_arg: ncpu
          short_arg: n
          description: CPU 核心数
        - name: JH_RELEASE
          type: select
          default: '16.02'
          cli_arg: release
          short_arg: r
          description: 软件版本
        - name: STAR_POST_SWITCH
          type: switch
          default: 'off'
          cli_arg: post
          short_arg: post
          description: 是否启用后处理
```

### 参数类型

| 类型 | 说明 | CLI 行为 |
|------|------|---------|
| `text` | 文本输入 | 单个值 |
| `select` | 下拉选择 | 单个值 |
| `upload` | 文件路径 | 支持多个文件/目录 |
| `switch` | 开关（on/off） | 布尔标志 |

### 路径映射判断

```
配置:  S: -> /apps,  D: -> /data

/app/project/file.sim     -> 已在远程，不上传
/data/cases/test.cas      -> 已在远程，不上传
/home/user/local.sim      -> 本地文件，自动上传
/tmp/scratch/file.dat     -> 本地文件，自动上传
```

## 认证方式

优先级从高到低：

| 优先级 | 方式 | 说明 |
|--------|------|------|
| 1 | `-u/-p` | 命令行用户名密码 |
| 2 | 配置文件密码 | `~/.appform/config.json` 中的 username/password |
| 3 | AccessKey | 配置文件或环境变量中的 AccessKey |
| 4 | Token | 配置文件或环境变量中的 Token |
| 5 | AES Token | 集群环境自动认证 |

## 完整示例

### 示例 1：远程文件直接提交

```bash
# 文件在 /apps 下（映射路径），无需上传
job_submit -a starccm -i /apps/project/simulation.sim -n 16 -r 20.02.007
```

### 示例 2：本地文件自动上传

```bash
# 文件在本地 /tmp 下，自动上传到 ~/<timestamp>/
job_submit -a starccm -i /tmp/simulation.sim -n 8
# 输出:
#   Authenticated as 'user' (password from config)
#   Uploading 1 local file(s) to /home/user/20260503_153000...
#     Uploading file: /tmp/simulation.sim
#   Upload complete.
#   Job submitted successfully!
#     Application: starccm
#     Job ID: 123456
```

### 示例 3：多文件 + 目录

```bash
# 混合上传多个文件和一个目录
job_submit -a fluent -i /local/case.cas /local/data.dat /local/mesh_dir/ -n 32 --upload-path /projects/my_sim
```

### 示例 4：指定上传路径

```bash
job_submit -a starccm -i /local/file.sim -n 8 --upload-path /shared/job_inputs
```

## 命令选项

| 选项 | 说明 |
|------|------|
| `-a, --app APP` | 应用类型（必填） |
| `-l, --list-apps` | 列出已配置应用 |
| `-u, --username USER` | 用户名 |
| `-p, --password PASS` | 密码 |
| `-e, --env ENV` | 目标环境（或设置 APPFORM_ENV） |
| `--upload-path PATH` | 本地文件上传到的远程目录 |
| `--wait [MINUTES]` | 提交后等待作业完成（默认 10 分钟轮询） |
| `-h, --help` | 显示帮助 |

应用特定的参数由配置文件定义，通过 `-a <app> -h` 查看。
