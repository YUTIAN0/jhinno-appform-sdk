# 作业配置文件

Job Profile 系统允许通过 YAML 配置文件定义应用参数，支持默认值、参数校验、自定义 CLI 参数名。

## 配置文件格式

配置文件兼容 `job_submit.py` 的 YAML 格式：

```yaml
job_submit_config:
  version: '1.0'
  description: 提交作业配置文件
  appform_base_url: https://server/appform
  applications:
    starccm:
      name: STAR-CCM+
      description: 计算流体力学仿真软件
      parameters:
      - name: JH_CAS
        type: upload
        required: true
        validation: ^.*\.(sim)$
        description: 算例文件路径
        cli_arg: input
        short_arg: i
      - name: JH_NCPU
        type: text
        required: false
        validation: ^[0-9]+$
        default: '1'
        description: 节点数
        cli_arg: ncpu
        short_arg: n
      - name: JH_RELEASE
        type: select
        required: false
        default: '16.02'
        description: 软件版本
        cli_arg: release
        short_arg: r
      - name: STAR_POST_SWITCH
        type: switch
        required: false
        default: 'off'
        description: 是否启用后处理
        cli_arg: post
        short_arg: post
```

### 参数类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `text` | 文本输入 | `JH_NCPU`, `JH_JOB_NAME` |
| `select` | 下拉选择 | `JH_RELEASE`, `JH_QUEUE` |
| `upload` | 文件路径 | `JH_CAS`, `JH_DAT` |
| `switch` | 开关（on/off） | `STAR_POST_SWITCH` |

### 参数字段

| 字段 | 说明 |
|------|------|
| `name` | 参数名（JH_* 格式） |
| `type` | 参数类型 |
| `required` | 是否必填 |
| `default` | 默认值 |
| `description` | 描述 |
| `validation` | 校验正则表达式 |
| `cli_arg` | 自定义 CLI 长参数名（可选） |
| `short_arg` | 自定义 CLI 短参数（可选） |

## Windows/Linux 磁盘路径映射

在 Windows 客户端提交作业时，Windows 盘符路径（如 `S:/project/file.sim`）需要自动转换为 Linux 集群路径（如 `/apps/project/file.sim`）。该功能通过 `job_submit.yaml` 中的 `windows_disk_mapping` 配置实现。

### 配置方式

```yaml
job_submit_config:
  version: '1.0'
  appform_base_url: https://server/appform
  windows_disk_mapping:
    'S:': '/apps'
    'D:': '/data'
    'E:': '/home/shared'
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
```

### 转换规则

| Windows 路径 | 映射配置 | 转换后 Linux 路径 |
|-------------|---------|------------------|
| `S:/project/file.sim` | `'S:': '/apps'` | `/apps/project/file.sim` |
| `D:/cases/test.cas` | `'D:': '/data'` | `/data/cases/test.cas` |
| `E:/shared/input.k` | `'E:': '/home/shared'` | `/home/shared/input.k` |
| `C:/local/file.txt` | 未配置 | 不转换，保持原路径 |

### 工作原理

1. 仅在 **Windows 系统**上生效（Linux/Mac 下不转换）
2. 仅对 `type: upload` 类型的文件路径参数进行转换
3. 自动检测路径中的盘符（如 `S:`, `D:`），匹配配置后替换盘符为 Linux 路径前缀
4. 反斜杠 `\` 自动转换为正斜杠 `/`
5. 未配置的盘符不作转换，原样提交并输出警告

### 命令行输出

提交作业时，会自动显示当前生效的路径映射：

```
Supported applications: starccm, fluent, nastran

Windows path mapping:
  S: -> /apps
  D: -> /data

Application: starccm (STAR-CCM+)
Parameters:
{
  "JH_CAS": "/apps/project/file.sim",
  "JH_NCPU": "16"
}
```

### 适用范围

路径映射功能在以下两个命令中均生效：

| 命令 | 说明 |
|------|------|
| `job_submit -a starccm -i S:/project/file.sim` | 自动转换为 `/apps/project/file.sim` |
| `appform jobs submit -a starccm -i S:/project/file.sim` | 自动转换为 `/apps/project/file.sim` |

如果通过 `--set` 或 `--params` 直接指定路径，同样会自动转换：

```bash
job_submit -a starccm --set JH_CAS=S:/project/file.sim --set JH_NCPU=8
appform jobs submit -a starccm --params '{"JH_CAS":"S:/project/file.sim","JH_NCPU":"8"}'
```

## 配置文件路径

配置文件按以下优先级查找：

1. `--profile-config` CLI 全局参数
2. `APPFORM_JOB_PROFILE_CONFIG` 环境变量
3. `~/.appform/config.json` 中的 `job_profile_config` 字段
4. 自动检测：
   - 当前目录 `job_submit.yaml`
   - `~/.appform/job_submit.yaml`
   - `/apps/software/script/job_submit.yaml`

### 指定配置文件路径

```bash
# CLI 全局参数
appform --profile-config /path/to/job_submit.yaml jobs apps

# 环境变量
export APPFORM_JOB_PROFILE_CONFIG=/path/to/job_submit.yaml

# 保存到配置文件（永久生效）
appform config set --job-profile-config /path/to/job_submit.yaml
```

## Python SDK 使用

```python
from appform_sdk import JobProfileManager, AppformClient

# 加载配置
pm = JobProfileManager("/path/to/job_submit.yaml")

# 列出所有应用
apps = pm.list_apps()
for app in apps:
    print(f"{app['app_id']}: {app['name']}")

# 获取应用参数定义
profile = pm.get_profile("starccm")
for p in profile.get_required_params():
    print(f"必填: {p.name} - {p.description}")
for p in profile.get_optional_params():
    print(f"可选: {p.name} (默认: {p.default}) - {p.description}")

# 构建提交参数（自动填充默认值）
params = pm.build_submit_params("starccm", {"JH_CAS": "/path/to/file.sim", "JH_NCPU": "16"})
print(params)
# {'JH_CAS': '/path/to/file.sim', 'JH_NCPU': '16', 'JH_RELEASE': '16.02', 'JH_NCPU2': '5'}

# 提交作业
client = AppformClient(base_url="...", token="...")
result = pm.submit_job(client, "starccm", {"JH_CAS": "/path/to/file.sim"})
```

### 参数校验

```python
profile = pm.get_profile("starccm")

# 校验参数
errors = profile.validate_params({"JH_CAS": "/path/to/file.txt"})
# ["Parameter JH_CAS='/path/to/file.txt' does not match pattern '^.*\.(sim)$'"]

errors = profile.validate_params({"JH_CAS": "/path/to/file.sim"})
# []  空列表 = 校验通过
```

## 工具命令

SDK 提供三个命令行工具用于作业提交，参数格式一致：

| 命令 | 说明 | 适用场景 |
|------|------|---------|
| `job_submit` | 独立作业提交工具 | 兼容原有 `python job_submit.py`，集群环境自动认证 |
| `appform jobs submit` | SDK CLI 子命令 | 使用 SDK 配置认证（AccessKey/Token） |
| `appform jobs submit-raw` | 原始 JSON 提交 | 不依赖配置文件 |

### job_submit 命令

独立的作业提交工具，完全兼容原有 `python job_submit.py` 的命令行参数格式，并支持本地文件自动上传。

```bash
# 列出支持的应用
job_submit -l

# 查看应用参数帮助
job_submit -a starccm -h
job_submit -a lsdyna2 -h

# 提交作业（远程映射路径下的文件，无需上传）
job_submit -a starccm -i /apps/project/file.sim -n 8
job_submit -a starccm -i /apps/project/file.sim -n 16 -r 20.02.007
job_submit -a lsdyna2 -i /data/project/input.k -n 16

# 提交作业（本地文件自动上传）
job_submit -a starccm -i /local/file.sim -n 8

# 指定上传目录
job_submit -a starccm -i /local/file.sim -n 8 --upload-path /projects/job_data

# 上传多个文件和目录
job_submit -a fluent -i /local/case.cas /local/data.dat /local/mesh_dir/ -n 32

# 开关参数
job_submit -a starccm -i /path/to/file.sim -post

# 提交后等待作业完成（默认每10分钟查询一次）
job_submit -a starccm -i /path/to/file.sim -n 8 --wait

# 提交后等待作业完成（自定义每5分钟查询一次）
job_submit -a starccm -i /path/to/file.sim -n 8 --wait 5

# 使用用户名密码认证
job_submit -a starccm -i /path/to/file.sim -n 8 -u username -p password
```

**文件上传功能：**

当 `type: upload` 参数指定的文件不在远程映射路径下时，自动上传后提交。

| 功能 | 说明 |
|------|------|
| 自动检测 | 通过 `windows_disk_mapping` 目标路径判断文件是否已在远程 |
| 上传路径 | `--upload-path PATH` 指定，默认为 `$HOME/<YYYYMMDD_HHMMSS>/` |
| 多文件 | 同一参数支持多个文件/目录：`-i file1.sim file2.dat` |
| 传输方式 | 跟随 `APPFORM_DEFAULT_METHOD` 配置（http/sftp） |
| $HOME 解析 | HTTP 由服务端解析；SFTP 通过 SSH `echo ~` 获取远端家目录 |

```
配置:  S: -> /apps,  D: -> /data

/app/project/file.sim     -> 已在远程，不上传
/data/cases/test.cas      -> 已在远程，不上传
/home/user/local.sim      -> 本地文件，自动上传
/tmp/scratch/file.dat     -> 本地文件，自动上传
```

**认证方式**（按优先级）：

| 优先级 | 方式 | 条件 |
|--------|------|------|
| 1 | `-u/-p` 密码认证 | 命令行传了用户名密码 |
| 2 | AccessKey 配置 | `~/.appform/config.json` 或环境变量中的 AccessKey |
| 3 | Token 配置 | `~/.appform/config.json` 或环境变量中的 Token |
| 4 | AES Token 自动检测 | 集群环境（已废弃，将在未来版本移除） |

### appform jobs submit 命令

```bash
# 列出应用
appform jobs submit -l
appform jobs apps

# 查看参数
appform jobs params starccm
appform jobs submit -a starccm --help

# 提交作业（自定义参数）
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run
appform jobs submit -a starccm -i /path/to/file.sim -n 8 -r 20.02.007

# 提交作业（--set 方式）
appform jobs submit -a starccm --set JH_CAS=/path/to/file.sim --set JH_NCPU=8

# 提交作业（JSON 方式）
appform jobs submit -a starccm --params '{"JH_CAS":"/path/to/file.sim","JH_NCPU":"8"}'

# 混合使用
appform jobs submit -a starccm -i /path/to/file.sim --set JH_NCPU=8 -r 20.02.007 -post

# 预览参数（不提交）
appform jobs submit -a starccm -i /path/to/file.sim -n 16 --dry-run
```

### appform jobs submit-raw 命令

不使用配置文件，直接传入 JSON 参数：

```bash
appform jobs submit-raw --app-id fluent --params '{"JH_CAS":"/path/to/file.cas","JH_NCPU":"8"}'
```

## 从 XML 导出配置文件

使用 `xml2table` 工具可以从门户导出的应用包中自动生成 SDK 兼容的 YAML 配置文件：

```bash
# 从应用目录扫描生成 YAML
python -m appform_sdk.xml2table -a -r -d . -o yaml

# 指定输出目录和文件名
python -m appform_sdk.xml2table -a -r -d . -o yaml -O ./output -n job_submit

# 同时生成多种格式
python -m appform_sdk.xml2table -a -r -d . -o yaml,excel,csv

# 仅处理单个文件
python -m appform_sdk.xml2table -f app/view.xml -o yaml
```

生成的 YAML 文件可直接用于 `job_submit` 或 `appform jobs submit`。

详见 [XML 表单解析工具](xml2table.md)。

## 与 job_submit.py 对照

| 原有方式 | SDK 方式 | 说明 |
|----------|---------|------|
| `python job_submit.py -l` | `job_submit -l` | 列出应用 |
| `python job_submit.py -a starccm -h` | `job_submit -a starccm -h` | 查看帮助 |
| `python job_submit.py -a starccm -i file.sim -ncpu 8` | `job_submit -a starccm -i file.sim -n 8` | 提交作业 |
| `python job_submit.py -a starccm -i file.sim -post` | `job_submit -a starccm -i file.sim -post` | 开关参数 |
| `python job_submit.py -u U -p P -a starccm ...` | `job_submit -u U -p P -a starccm ...` | 带认证 |
| — | `appform jobs submit -a starccm -i file.sim -n 8` | SDK CLI 方式 |
| — | `appform jobs submit -a starccm --set JH_CAS=file` | --set 方式 |
