# XML 表单解析工具

`xml2table` 工具可以从门户导出的应用包中解析 XML 表单配置，生成 Excel、CSV、Markdown、SDK YAML 等格式。

## 功能特性

- 从 `view.xml` 中提取应用参数定义（字段名、类型、默认值、校验规则等）
- 从 `script/dynamic_*.sh` 中提取动态选项值
- 支持多种输出格式：
  - **YAML** — 生成 SDK 兼容的 `job_submit.yaml`，可直接用于 `job_submit` 或 `appform jobs submit`
  - **Excel** (.xlsx) — 带格式的表格（需 `pandas` + `openpyxl`）
  - **CSV** (.csv) — 通用表格（需 `pandas`）
  - **Markdown** (.md) — 文档格式（无额外依赖）

## 依赖项

| 格式 | 依赖 | 安装命令 |
|------|------|---------|
| YAML | `PyYAML` | `pip install PyYAML` |
| Excel | `pandas` + `openpyxl` | `pip install pandas openpyxl` |
| CSV | `pandas` | `pip install pandas` |
| Markdown | 无 | — |

核心 XML 解析仅使用标准库，不安装任何额外依赖即可运行。

## 使用方式

### CLI 命令

```bash
# 扫描当前目录，生成所有支持格式
python -m appform_sdk.xml2table -a -r -d .

# 只生成 YAML（SDK 配置文件）
python -m appform_sdk.xml2table -a -r -d . -o yaml

# 指定输出目录和文件名
python -m appform_sdk.xml2table -a -r -d . -o yaml -O ./output -n job_submit

# 同时生成多种格式
python -m appform_sdk.xml2table -a -r -d . -o yaml,excel,csv

# 处理单个文件
python -m appform_sdk.xml2table -f app/view.xml -o yaml

# 查看当前环境可用格式
python -m appform_sdk.xml2table --help
```

### CLI 参数

| 参数 | 说明 |
|------|------|
| `-f, --file` | 指定单个 XML 文件路径 |
| `-a, --all` | 处理目录下所有 XML 文件 |
| `-r, --recursive` | 递归查找子目录 |
| `-d, --directory` | 查找目录（默认：当前目录） |
| `-p, --pattern` | 文件匹配模式（默认：view.xml） |
| `-o, --output` | 输出格式，逗号分隔（默认：全部可用格式） |
| `-O, --output-dir` | 输出目录（默认：当前目录） |
| `-n, --filename` | 输出文件名（不含扩展名，默认：all_apps_form_table） |

### Python API

```python
from appform_sdk.xml2table import (
    export,
    check_available_formats,
    parse_xml_to_table,
    find_xml_files,
    collect_xml_data,
    create_sdk_yaml,
)

# 检查当前环境支持的格式
formats = check_available_formats()
print(formats)
# {'yaml': True, 'excel': True, 'csv': True, 'markdown': True}

# 一行代码导出
export(
    xml_source="./apps_dir",
    output_formats=["yaml", "excel"],
    output_dir="./output",
    output_filename="job_submit",
)

# 或分步操作
xml_files = find_xml_files("./apps_dir")
all_data, source_files = collect_xml_data(xml_files)
create_sdk_yaml(all_data, "./output/job_submit.yaml")
```

### 检查环境依赖

```python
from appform_sdk.xml2table import check_available_formats

formats = check_available_formats()
for fmt, available in formats.items():
    status = "OK" if available else "NOT INSTALLED"
    print(f"  {fmt}: {status}")
```

## 输出 YAML 格式说明

生成的 YAML 文件结构与 `job_submit.yaml` 完全一致，可直接被 SDK 的 `JobProfileManager` 加载：

```yaml
job_submit_config:
  version: '1.0'
  description: Appform job submission configuration (auto-generated from XML)
  applications:
    starccm:
      name: starccm
      description: starccm application
      parameters:
      - name: JH_CAS
        type: upload
        required: true
        description: SIM 文件
        validation: ^.*\.(sim)$
        cli_arg: input
        short_arg: i
      - name: JH_NCPU
        type: text
        required: false
        description: 节点数
        default: '1'
        cli_arg: ncpu
        short_arg: n
      - name: JH_RELEASE
        type: select
        required: false
        description: 版本号
        default: '16.02'
        cli_arg: release
        short_arg: r
      - name: STAR_POST_SWITCH
        type: switch
        required: false
        description: 后处理支持
        default: 'off'
        cli_arg: post
        short_arg: post
```

常用的 `JH_*` 参数会自动匹配 `cli_arg` 和 `short_arg`（如 `JH_CAS` → `input`/`-i`），其他参数自动派生 CLI 参数名。

## 工作流程

```
门户导出应用包
    │
    ▼
xml2table 扫描 view.xml
    │
    ├─→ Excel/CSV/Markdown  （文档/表格）
    │
    └─→ job_submit.yaml     （SDK 配置文件）
              │
              ▼
    job_submit -a starccm -i file.sim -n 8
    或
    appform jobs submit -a starccm -i file.sim -n 8
```
