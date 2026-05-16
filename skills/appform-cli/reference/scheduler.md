# 调度命令参考

集群节点上可直接使用的调度命令（jsub/jjobs/jctrl 等），无需通过 appform API。
完整参数参考 → [scheduler-manual.md](scheduler-manual.md)（28 个命令）

---

## 命令速查

| 命令 | 功能 | 等效 appform 命令 |
|------|------|-------------------|
| `jsub` | 提交作业 | `appform jobs submit` |
| `jjobs` | 查看作业 | `appform jobs list/get` |
| `jctrl stop` | 挂起作业 | `appform jobs stop` |
| `jctrl kill` | 终止作业 | `appform jobs kill` |
| `jctrl resume` | 恢复作业 | `appform jobs resume` |
| `jctrl requeue` | 重排队 | `appform jobs requeue` |
| `jctrl peek` | 查看输出 | `appform jobs output` |
| `jhist` | 作业历史 | `appform jobs history` |
| `jqueues` | 队列信息 | — |
| `jhosts` | 节点信息 | — |
| `japps` | 应用信息 | `appform apps list` |

---

## jsub — 提交作业

### 基本提交

```bash
jsub -J job_name -q queue_name -n 8 my_command
jsub -m host1 -q short my_command                        # 指定节点
jsub -R "select[mem>1000]" -n 4 my_command                # 资源需求
jsub -x -m host1 my_command                               # 独占节点
jsub -app starccm -n 16 my_command                        # 指定应用
```

### 脚本提交模式（推荐，参数可批量复用）

```bash
#!/bin/sh
#JSUB -J job1
#JSUB -q queue_name
#JSUB -n 8
#JSUB -R "span[ptile=2]"
my_command arg1 arg2
```

```bash
jsub my_job.sh            # 方式 1：直接传文件
jsub < my_job.sh          # 方式 2：标准输入
```

命令行选项会覆盖脚本中指定的选项。

### 数组作业

```bash
jsub -J job[1-20] -i input%J_%I -o output%J_%I.log myjob
jjobs -A                              # 查看数组作业统计
jctrl stop 6[15-20]                   # 挂起指定范围的子作业
```

### 交互式作业

| 类型 | 选项 | 说明 |
|------|------|------|
| 普通交互式 | `-I` | 后端执行，实时呈现到提交端 |
| X11 交互式 | `-IX` | 带 X11 转发 |
| 服务模式 | `-Is` | 提交端关闭后作业保持后台运行 |

```bash
jsub -Is bash             # 服务模式交互式
jattach 13                # 重新连接到作业 13
```

### 资源需求（`-R` 详细说明）

`-R` 支持三个关键字，可组合使用：`-R "select[...] rusage[...] span[...]"`

| 关键字 | 作用 | 示例 |
|--------|------|------|
| `select` | 节点选择条件 | `select[mem>1024]`、`select[type==LINUX64]`、`select[gpu_node]` |
| `rusage` | 资源预留 | `rusage[mem=500]`、`rusage[mem=800/slot]`、`rusage[mem=500&&swap=200]` |
| `span` | 分布控制 | `span[hosts=1]`（单节点）、`span[ptile=2]`（每节点 2 slot） |

**rusage 预留方式：**

| 写法 | 含义 |
|------|------|
| `mem=800` | 默认按 slot 预留（等同 `mem=800/slot`） |
| `mem=800/slot` | 预留值 × 节点分配的 slot 数 |
| `mem=800/host` | 每节点固定预留，不乘以 slot 数 |

**组合示例：**

```bash
# 选择 LINUX64 节点 + 预留 500MB 内存 + 单节点运行
jsub -n 4 -R "select[type==LINUX64] rusage[mem=500] span[hosts=1]" my_job

# 选择内存充足节点 + 预留资源 + 每节点 2 slots
jsub -n 8 -R "select[mem>1024] rusage[mem=800] span[ptile=2]" my_job

# 复合条件：NTX64 且 mem>50，或 LINUX64 且 mem>100
jsub -R "select[((type==NTX64 && mem>50) || (type==LINUX64 && mem>100))]" my_job
```

> 完整说明 → [jsub_R_resource_requirements.md](jsub_R_resource_requirements.md)

### 其他选项

| 选项 | 说明 |
|------|------|
| `-J` | 作业名称 |
| `-P` | 项目名称 |
| `-q` | 队列 |
| `-m` | 节点/节点组 |
| `-n` | 处理器数 |
| `-R` | 资源需求 |
| `-app` | 应用 |
| `-i` / `-o` / `-e` | 输入/输出/错误文件 |
| `-E` / `-Ep` | pre-exec / post-exec |
| `-cwd` | 工作目录 |
| `-gpgpu` | GPU 请求 |
| `-M` | 内存限制（MB） |
| `-W` | 运行时间限制（分钟） |
| `-b` / `-t` | 开始/终止时间 |
| `-w` | 依赖条件 |
| `-f` | 文件传输 |
| `-r` | 可重新运行 |
| `-x` | 独占节点 |
| `-ux` | 用户独占节点（V6.5+） |

---

## jjobs — 查看作业

```bash
jjobs                      # 当前用户的作业
jjobs -a                   # 所有状态
jjobs -r                   # 运行中
jjobs -p                   # 等待中（含 PEND 原因）
jjobs -d                   # 已结束
jjobs -s                   # 挂起中
jjobs -l 1001              # 作业详情
jjobs -w                   # 宽格式
jjobs -u user1             # 指定用户
jjobs -u all               # 所有用户
jjobs -q queue_name        # 指定队列
jjobs -m host1             # 指定节点
jjobs -app starccm         # 指定应用
jjobs -P project_name      # 指定项目
jjobs -J job_name          # 指定作业名
jjobs -A                   # 数组作业统计
jjobs -env                 # 显示环境变量
jjobs -o "jobid:4 stat:-10"  # 自定义输出格式
```

---

## jctrl — 作业控制

### 挂起 / 恢复 / 终止

```bash
jctrl stop 1001
jctrl resume 1001
jctrl kill 1001
jctrl kill -f 1001                 # 强制终止
```

### 队列排序

```bash
jctrl top 1001                     # 移到队列顶部
jctrl bot 1001                     # 移到队列底部
jctrl bot -p 2 1001                # 移到第 2 位
```

### 强制执行（管理员）

```bash
jctrl start -m host1 1001
jctrl start -f -m host1 1001      # 忽略资源限制
```

### 重排队

```bash
jctrl requeue 1001
jctrl requeue -a                   # 所有作业
jctrl requeue -u user1             # 指定用户
```

### 查看输出

```bash
jctrl peek 1001
jctrl peek -f 1001                 # 实时打印
```

### 清理缓存

```bash
jctrl clean 1001
jctrl clean -u all                 # 清理所有用户
```

---

## jhist — 作业历史

```bash
jhist                      # 当前用户所有未完成作业
jhist -a                   # 所有作业（含已完成）
jhist -a -l                # 详细信息
jhist -S "2026-05-01,2026-05-14"  # 时间范围
jhist -u user1             # 指定用户
jhist -q queue_name        # 指定队列
jhist -J job_name          # 指定作业名
jhist -d                   # 仅已完成
jhist -e                   # 仅异常退出
jhist -p                   # 仅等待中
jhist -r                   # 仅运行中
```

---

## jqueues — 队列信息

```bash
jqueues                    # 所有队列
jqueues -l                 # 详细信息
jqueues -w                 # 宽格式
jqueues -m host1           # 指定节点可用队列
jqueues -u user1           # 指定用户所属队列
jqueues queue_name         # 指定队列
```

---

## jhosts — 节点信息

```bash
jhosts                     # 所有节点
jhosts -l                  # 详细信息
jhosts -w                  # 宽格式
jhosts -R "select[mem>1000]"  # 按资源筛选
jhosts host1               # 指定节点
jhosts stat                # 节点负载
jhosts stat -l             # 负载详情
jhosts attrib              # 静态资源信息
jhosts attrib -l <节点名>  # 指定节点的详细静态资源
```

### jhosts attrib -l 输出说明

`jhosts attrib -l` 显示节点的硬件静态资源信息，用于确认节点类型、CPU 架构、GPU 等。

**Linux 计算节点示例**（`jhosts attrib -l ev-hpc-compute001`）：

```
HOST  ev-hpc-compute001
type     model    ndisks ncpus   maxmem  maxswap   maxtmp nsocket ncore nthread ngpus nnodes RESOURCES
LINUX64  AMD64         1    64  385863M       0K  448367M       2    32       1     -      2 -

 NUMA node:    ID   core_id               max_mem     gpu_id
                0   0:0-3,0:16-19,0:32-35    192397M          -
                    0:48-51,0:64-67,0:80-83
                    0:96-99,0:112-115
                1   1:0-3,1:16-19,1:32-35    193465M          -
                    1:48-51,1:64-67,1:80-83
                    1:96-99,1:112-115
```

**Windows 视图节点示例**（`jhosts attrib -l ev-hpc-view11`）：

```
HOST  ev-hpc-view11
type     model    ndisks ncpus   maxmem  maxswap   maxtmp nsocket ncore nthread ngpus nnodes RESOURCES
NTX64    Intel64       5    92 1048239M 1099439M        -       2    23       2     1      - -

  GPU: ID  type                        max_mem  processors  cores  threads  capability  gpu_clock max_power
        0  NVIDIARTX5880AdaGeneration   49140M         110   7040   168960         8.9  2460.0MHz    285.0w
```

**字段说明**：

| 字段 | 说明 |
|------|------|
| `type` | 操作系统类型：`LINUX64`（Linux 计算节点）、`NTX64`（Windows 视图节点） |
| `model` | CPU 架构：`AMD64`、`Intel64` 等 |
| `ncpus` | 总 CPU 核数（= nsocket × ncore × nthread） |
| `maxmem` | 最大可用内存 |
| `nsocket` | CPU 插槽数（物理 CPU 数） |
| `ncore` | 每插槽核心数 |
| `nthread` | 每核心线程数（超线程，1 = 无超线程） |
| `ngpus` | GPU 数量（`-` 表示无 GPU） |
| `nnodes` | NUMA 节点数 |

> **`type` 字段用于 `-R "select[type==LINUX64]"` 参数**，确保作业分配到 Linux 计算节点而非 Windows 视图节点。

---

## jhostgroup — 节点组信息

节点组将配置相同或相近的节点归为一组，提交作业时通过 `-m <节点组>` 指定执行节点组。

```bash
jhostgroup                  # 所有节点组
jhostgroup -w               # 宽格式（显示包含的节点列表）
jhostgroup -r               # 递归展开（只显示节点名，不含子组名，去重）
jhostgroup group_name       # 指定节点组
```

**提交作业时指定节点组**：

```bash
# jsub 方式
jsub -m <节点组名> -n 16 ./my_job.sh

# appform CLI 方式
appform jobs submit -a starccm -i /path/test.sim -n 16 --set JH_NODE_GROUP=<节点组名>
```

---

## 内置环境变量

作业提交后自动设置，可在脚本中直接使用：

| 变量 | 说明 |
|------|------|
| `JH_JOBID` | 作业号 |
| `JH_HOSTS` | 执行节点列表 |
| `JH_QUEUE` | 队列名称 |
| `JH_JOBNAME` | 作业名称 |
| `JH_SUB_HOST` | 提交节点 |
| `JH_SUB_CWD` | 提交时工作路径 |
| `JH_JOB_PROJECT` | 项目名称 |
| `JH_ARRAY_JOBINDEX` | 数组作业子作业索引 |
| `JH_ARRAY_JOBID` | 数组作业 ID |
| `JH_EXEC_USER` | 执行用户 |
| `JH_GPU_MEM` | GPU 内存大小 |
| `JH_CPU_RANK` | CPU 绑定信息 |
| `JH_GPU_RANK` | GPU 绑定信息 |
| `JH_JOB_PORTS` | 端口资源 |
| `JH_JOB_OUTFILE` | 输出文件路径 |

---

## 其他常用命令

| 命令 | 功能 |
|------|------|
| `jmod` | 修改已提交作业的参数 |
| `jdepinfo` | 查看作业依赖关系 |
| `jlimits` | 查看用户/队列资源限制 |
| `jusergroup` | 用户组信息 |
| `jhostgroup` | 节点组信息 |
| `jusers` | 用户作业信息 |
| `jcode` | 错误码查询 |
| `jversion` | 调度系统版本 |
| `jconfig` | 管理调度配置（管理员） |
