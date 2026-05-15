# MPI 作业提交

MPI（Message Passing Interface）并行作业的提交方法。涵盖 Intel MPI、MPICH、OpenMPI 三种常见实现。

## 适用场景

- 大规模并行计算（CFD、分子动力学、天气预报等）
- 多节点分布式内存并行
- 需要进程间通信的计算任务

## 通用提交流程

MPI 作业通过 `jsub` 提交，核心参数：

| 参数 | 说明 |
|------|------|
| `-n <N>` | 总进程数 |
| `-R "select[type==LINUX64] span[ptile=N]"` | 节点类型 + 每节点进程数（**必须指定节点类型，否则可能分配到 view 节点**） |
| `-m <node>` | 指定节点（可选，不指定由调度器自动分配） |
| `-app <app_id>` | 指定应用（如果集群配置了 MPI 应用） |

> **必须指定节点类型**：集群可能混合 Linux 计算节点和 Windows 视图节点，不指定 `-R "select[type==LINUX64]"` 可能被分配到错误节点导致 MPI 失败。具体类型名以 `jhosts` 输出为准。

**节点数 = 总进程数 / 每节点进程数**，例如 `-n 16 -R "select[type==LINUX64] span[ptile=4]"` → 4 个 Linux 节点，每节点 4 进程。

> 提交参数详细参考 [reference/scheduler-manual.md](../reference/scheduler-manual.md)

---

## 节点列表文件（hostfile）

MPI 启动器需要知道在哪些节点上启动进程。景行调度系统通过环境变量 `JH_HOSTS` 自动提供分配的节点信息。

### JH_HOSTS 格式

`JH_HOSTS` 的格式为：`节点名1 slot数1 节点名2 slot数2 ...`

每个节点名后跟该节点分配的 slot 数，空格分隔。**1 slot = 1 CPU 核心**，因此 slot 数即为该节点分配给作业的核数。

| 场景 | JH_HOSTS 值 | 含义 |
|------|-------------|------|
| 串行作业，1 节点 1 核 | `host1 1` | host1 分配 1 核 |
| 并行作业，2 节点各 4 核 | `host1 4 host2 4` | 每节点分配 4 核，共 8 核 |
| 并行作业，3 节点不均匀 | `host1 4 host2 4 host3 2` | host1/host2 各 4 核，host3 2 核 |

### 从 JH_HOSTS 生成 hostfile

**Intel MPI / MPICH**：hostfile 一行表示一个核心（一个 MPI 进程），将每个节点名按 slot 数展开。

**OpenMPI**：hostfile 一行表示一个节点及其 slot 数，格式为 `hostname slots=N`。

#### Intel MPI / MPICH 格式

```bash
#!/bin/bash
#JSUB -J mpi_job
#JSUB -n 16
#JSUB -R "select[type==LINUX64] span[ptile=4]"

module purge
module load intelmpi/2021.11

# 从 JH_HOSTS 生成 hostfile
# JH_HOSTS: "host1 4 host2 4 host3 4 host4 4"
# 展开为每行一个节点名，每个节点重复 slot 数次
HOSTFILE="hostfile_${JH_JOBID}"
echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2){host=$i;slots=$(i+1);for(j=1;j<=slots;j++) print host}}' > "$HOSTFILE"
```

生成的 hostfile 内容（`host1 4 host2 4 host3 4 host4 4`）：

```
host1
host1
host1
host1
host2
host2
host2
host2
host3
host3
host3
host3
host4
host4
host4
host4
```

共 16 行 = 16 个核心 = 16 个 MPI 进程。

然后用 hostfile 启动 MPI：

```bash
# Intel MPI / MPICH
# 从 JH_HOSTS 计算总进程数（所有 slot 之和）
NP=$(echo "$JH_HOSTS" | awk '{s=0; for(i=2;i<=NF;i+=2) s+=$i; print s}')

mpirun -n "$NP" -machinefile "$HOSTFILE" ./my_program input.dat
```

#### OpenMPI 格式

```bash
HOSTFILE="hostfile_${JH_JOBID}"
echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2) printf "%s slots=%s\n", $i, $(i+1)}' > "$HOSTFILE"
```

生成的 hostfile 内容（`host1 4 host2 4 host3 4 host4 4`）：

```
host1 slots=4
host2 slots=4
host3 slots=4
host4 slots=4
```

```bash
# 从 JH_HOSTS 计算总进程数
NP=$(echo "$JH_HOSTS" | awk '{s=0; for(i=2;i<=NF;i+=2) s+=$i; print s}')

mpirun -np "$NP" --hostfile "$HOSTFILE" ./my_program input.dat
```

---

## 软件环境加载

集群使用 **Environment Modules** 管理软件环境。提交 MPI 作业前必须加载对应的 MPI 模块。

### 基本用法

```bash
# 查看可用的 MPI 模块
module avail mpi

# 清理已有环境变量，避免模块冲突（脚本中推荐在 module load 前执行）
module purge

# 加载模块
module load intelmpi/2021.11
module load openmpi/4.1.5
module load mpich/4.1.2

# 查看已加载模块
module list

# 卸载模块
module unload intelmpi

# 切换模块（自动卸载旧版本再加载新版本）
module switch intelmpi/2021.11 intelmpi/2024.0
```

### 常见 MPI 模块名

| MPI 实现 | 典型模块名 |
|----------|-----------|
| Intel MPI | `intelmpi`, `intel-mpi`, `impi` |
| MPICH | `mpich`, `mpich/4.1.2` |
| OpenMPI | `openmpi`, `openmpi/4.1.5` |

> 具体模块名以 `module avail mpi` 输出为准，不同集群命名可能不同。

---

## Intel MPI

### 脚本提交（推荐）

```bash
#!/bin/bash
#JSUB -J intel_mpi_job
#JSUB -n 32
#JSUB -R "select[type==LINUX64] span[ptile=8]"
#JSUB -o output.log
#JSUB -e error.log

module purge
module load intelmpi/2021.11

# I_MPI 绑定策略优化性能
export I_MPI_PIN=1
export I_MPI_PIN_DOMAIN=auto

# 生成 hostfile（一行 = 一核 = 一个 MPI 进程）
# JH_HOSTS: "host1 8 host2 8 host3 8 host4 8" → 32 行
HOSTFILE="hostfile_${JH_JOBID}"
echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2){host=$i;slots=$(i+1);for(j=1;j<=slots;j++) print host}}' > "$HOSTFILE"

# 从 JH_HOSTS 计算总进程数（所有 slot 之和）
NP=$(echo "$JH_HOSTS" | awk '{s=0; for(i=2;i<=NF;i+=2) s+=$i; print s}')

mpirun -n "$NP" -machinefile "$HOSTFILE" ./my_program input.dat
```

```bash
chmod +x run_intel_mpi.sh
jsub ./run_intel_mpi.sh
```

### 命令行提交

```bash
# 4 节点，每节点 8 进程，共 32 进程
jsub -J mpi_job -n 32 -R "select[type==LINUX64] span[ptile=8]" \
  bash -c "module purge && module load intelmpi/2021.11 && mpirun -n 32 ./my_program input.dat"
```

### 常用环境变量

| 变量 | 说明 | 推荐值 |
|------|------|--------|
| `I_MPI_PIN` | 进程绑定 | `1`（启用） |
| `I_MPI_PIN_DOMAIN` | 绑定域 | `auto` |
| `I_MPI_FABRICS` | 通信 fabric | `shm:ofi`（节点内共享内存+节点间网络） |
| `I_MPI_DEBUG` | 调试级别 | `0`（生产）/ `5`（调试） |

---

## MPICH

### 脚本提交（推荐）

```bash
#!/bin/bash
#JSUB -J mpich_job
#JSUB -n 32
#JSUB -R "select[type==LINUX64] span[ptile=8]"
#JSUB -o output.log
#JSUB -e error.log

module purge
module load mpich/4.1.2

# 生成 hostfile（一行 = 一核 = 一个 MPI 进程）
# JH_HOSTS: "host1 8 host2 8 host3 8 host4 8" → 32 行
HOSTFILE="hostfile_${JH_JOBID}"
echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2){host=$i;slots=$(i+1);for(j=1;j<=slots;j++) print host}}' > "$HOSTFILE"

# 从 JH_HOSTS 计算总进程数
NP=$(echo "$JH_HOSTS" | awk '{s=0; for(i=2;i<=NF;i+=2) s+=$i; print s}')

# MPICH 使用 hydra 进程管理器
mpiexec -n "$NP" -machinefile "$HOSTFILE" -binding domain ./my_program input.dat
```

```bash
chmod +x run_mpich.sh
jsub ./run_mpich.sh
```

### 命令行提交

```bash
jsub -J mpich_job -n 32 -R "select[type==LINUX64] span[ptile=8]" \
  bash -c "module purge && module load mpich/4.1.2 && mpiexec -n 32 ./my_program input.dat"
```

### 常用环境变量

| 变量 | 说明 | 推荐值 |
|------|------|--------|
| `HYDRA_BINDING` | 进程绑定策略 | `auto` |
| `UCX_NET_DEVICES` | UCX 网络设备 | 按集群配置 |

---

## OpenMPI

### 脚本提交（推荐）

```bash
#!/bin/bash
#JSUB -J openmpi_job
#JSUB -n 32
#JSUB -R "select[type==LINUX64] span[ptile=8]"
#JSUB -o output.log
#JSUB -e error.log

module purge
module load openmpi/4.1.5

# 生成 hostfile（OpenMPI 原生格式：每行 hostname slots=N）
# JH_HOSTS: "host1 8 host2 8 host3 8 host4 8" → 4 行
HOSTFILE="hostfile_${JH_JOBID}"
echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2) printf "%s slots=%s\n", $i, $(i+1)}' > "$HOSTFILE"

# 也可使用通用格式（每行一个节点名，展开 slot 数次），OpenMPI 同样支持：
# echo "$JH_HOSTS" | awk '{for(i=1;i<=NF;i+=2){host=$i;slots=$(i+1);for(j=1;j<=slots;j++) print host}}' > "$HOSTFILE"

# 从 JH_HOSTS 计算总进程数
NP=$(echo "$JH_HOSTS" | awk '{s=0; for(i=2;i<=NF;i+=2) s+=$i; print s}')

mpirun -np "$NP" \
  --hostfile "$HOSTFILE" \
  -x PATH -x LD_LIBRARY_PATH \
  --bind-to core \
  --report-bindings \
  ./my_program input.dat
```

> **环境变量传递**：OpenMPI 默认不将当前环境变量传递给 MPI 进程。需要用 `-x VAR` 显式传递，或用 `-x`（无参数）传递所有环境变量。`module load` 设置的 `PATH`/`LD_LIBRARY_PATH` 等必须通过 `-x` 传递，否则 MPI 进程找不到命令。

```bash
chmod +x run_openmpi.sh
jsub ./run_openmpi.sh
```

### 命令行提交

```bash
jsub -J openmpi_job -n 32 -R "select[type==LINUX64] span[ptile=8]" \
  bash -c "module purge && module load openmpi/4.1.5 && mpirun -np 32 -x PATH -x LD_LIBRARY_PATH --bind-to core ./my_program input.dat"
```

### 常用环境变量

| 变量 | 说明 | 推荐值 |
|------|------|--------|
| `OMPI_MCA_btl` | 通信组件 | `openib,self,vader` |
| `OMPI_MCA_pml` | PML 选择 | `ucx` 或 `ob1` |
| `OMPI_MCA_hwloc_base_binding_policy` | 绑定策略 | `core` |
| `UCX_NET_DEVICES` | UCX 网络设备 | 按集群配置 |

---

## 三种 MPI 对比

| 特性 | Intel MPI | MPICH | OpenMPI |
|------|-----------|-------|---------|
| 启动命令 | `mpirun` / `mpiexec` | `mpiexec` / `mpirun` | `mpirun` / `mpiexec` |
| 进程管理器 | Intel MPI 自带 | Hydra | ORTE (Open RTE) |
| 默认绑定 | `I_MPI_PIN=1` | 需手动配置 | `--bind-to core` |
| hostfile 格式 | 每行一个节点名（展开 slot 数次） | 每行一个节点名（展开 slot 数次） | 每行 `hostname slots=N`（推荐）或每行一个节点名 |
| hostfile 指定 | `-machinefile` | `-machinefile` | `--hostfile` |
| 网络优化 | `I_MPI_FABRICS` | UCX/MOFI | UCX/BTL |
| 适用场景 | Intel 平台优化 | 通用、教学 | 异构环境 |

---

## 常见问题

### Q: 如何确定每节点进程数？

一般规则：**每节点进程数 ≤ 节点 CPU 核数**。查看节点资源：

```bash
jhosts -l node_name    # 查看节点 ncpus 数
```

### Q: 进程绑定有什么用？

绑定进程到 CPU 核心可减少进程迁移开销，提高缓存命中率。通常建议启用。

### Q: 如何查看作业分配了哪些节点？

```bash
jjobs -l <job_id>              # EXEC_HOST 字段显示执行节点
echo $JH_HOSTS                 # 脚本内获取，格式: "host1 4 host2 4"
echo $JH_HOSTS | awk '{for(i=1;i<=NF;i+=2) print $i}'  # 仅提取节点名
```

### Q: MPI 程序报 "no available NIC" 怎么办？

通常是网络设备配置问题。检查并设置：

```bash
# Intel MPI
export I_MPI_FABRICS=shm:tcp

# OpenMPI
export OMPI_MCA_btl_tcp_if_include=eth0

# 通用（UCX）
export UCX_NET_DEVICES=eth0
```

### Q: module load 报 "command not found" 怎么办？

Modules 初始化脚本可能未在计算节点的 shell 中加载。手动初始化：

```bash
module purge
module load intelmpi/2021.11
```
