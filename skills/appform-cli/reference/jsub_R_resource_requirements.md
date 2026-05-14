# jsub -R 资源需求参数说明

## 概述

`jsub -R res_req` 用于指定提交作业时的资源需求信息。资源需求由一个或多个**资源需求字符串**组成，用于告诉调度器该作业需要什么样的计算资源，调度器据此选择合适的执行节点。

资源需求字符串的通用格式为：

```
keyword[expression]
```

支持三个关键字：`select`、`rusage`、`span`，可组合使用。

---

## 1. select — 资源选择条件

### 作用

指定作业**选择执行节点**的条件。只有满足条件的节点才会被考虑用于运行该作业。不满足条件的节点直接跳过，作业不会被派发到这些节点上。

### 语法

```
select[condition]
```

### 支持的资源属性

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `type` | 字符串 | 节点操作系统类型 | `type==LINUX64`、`type==NTX64` |
| `mem` | 数值(MB) | 节点可用内存 | `mem>800` |
| `swap` | 数值(MB) | 节点可用交换区 | `swap>500` |
| `tmp` | 数值(MB) | 节点可用临时存储 | `tmp>300` |
| `ncpus` | 整数 | 节点CPU核数 | `ncpus>=4` |
| `ndisks` | 整数 | 节点磁盘数 | `ndisks>0` |
| 自定义Boolean资源 | 字符串 | 管理员自定义的节点资源标签 | `ai_cs`、`gpu_node` |

### 运算符

| 运算符 | 含义 |
|--------|------|
| `==` | 等于 |
| `!=` | 不等于 |
| `>` | 大于 |
| `<` | 小于 |
| `>=` | 大于等于 |
| `<=` | 小于等于 |
| `&&` | 与（同时满足） |
| `\|\|` | 或（满足其一即可） |

### 示例

```bash
# 选择操作系统为 LINUX64 的节点
jsub -R "select[type==LINUX64]" my_job

# 选择内存大于 800MB 的节点
jsub -R "select[mem>800]" my_job

# 复合条件：type==NTX64 且 mem>50，或 type==LINUX64 且 mem>100
jsub -R "select[((type==NTX64 && mem>50) || (type==LINUX64 && mem>100))]" my_job

# 选择满足自定义 Boolean 资源 ai_cs 的节点
jsub -R "select[ai_cs]" my_job

# 选择内存>800 或 交换区>500 或 临时存储>300 的节点
jsub -R "select[mem>800 || swap>500 || tmp>300]" my_job
```

---

## 2. rusage — 资源预留

### 作用

指定作业在执行节点上需要**预留的资源数量**。调度器会在目标节点上为作业锁定这些资源，确保作业运行时有足够的资源可用。

### 语法

```
rusage[resource=value ...]
```

### 支持的预留资源

| 资源 | 单位 | 说明 |
|------|------|------|
| `mem` | MB | 内存预留 |
| `swap` | MB | 交换区预留 |
| `tmp` | MB | 临时存储预留 |
| `dummy` | - | 虚拟资源（用于特殊调度场景） |

### 预留方式

rusage 中的资源分为**共享资源**和**非共享资源**两种：

#### 非共享资源（默认）

非共享资源支持两种预留方式，通过后缀指定：

| 写法 | 含义 | 预留计算 |
|------|------|----------|
| `mem=800/slot` | 按 slot 预留 | 预留值 × 节点分配的 slot 数 |
| `mem=800/host` | 按 host 预留 | 固定预留指定值，不乘以 slot 数 |
| `mem=800` | 默认按 slot 预留 | 等同于 `mem=800/slot` |

**按 slot 预留示例：**
```bash
jsub -n 2 -R "rusage[mem=800/slot]" my_job
# 如果一个节点分配了 2 个 slots → 预留 2×800 = 1600MB
# 如果分配了 2 个节点各 1 个 slot → 每节点预留 800MB
```

**按 host 预留示例：**
```bash
jsub -n 2 -R "rusage[mem=800/host]" my_job
# 无论节点分配多少 slots → 每节点固定预留 800MB
```

#### 共享资源

共享资源预留是**作业级别**的，在 rusage 中指定多少就从该共享资源值中预留多少，不乘以 slot 数。

### 组合条件

rusage 支持 `&&`（与）和 `||`（或）组合多个资源条件：

```bash
# 同时预留 mem 500MB 和 swap 200MB，或同时预留 swap 200MB 和 tmp 200MB
jsub -R "rusage[mem=500&&swap=200 || swap=200&&tmp=200]" my_job

# 预留 mem 800MB 或 swap 5000MB 或 tmp 300MB（满足其一即可）
jsub -R "rusage[mem=800 || swap=5000 || tmp=300]" my_job
```

### 示例

```bash
# 预留 500MB 内存
jsub -R "rusage[mem=500]" my_job

# 预留 500MB 内存和 200MB 交换区（同时满足）
jsub -R "rusage[mem=500&&swap=200]" my_job

# 按 slot 预留：2 个 slot，每个预留 800MB 内存
jsub -n 2 -R "rusage[mem=800/slot]" my_job

# 按 host 预留：每节点固定预留 800MB 内存
jsub -n 2 -R "rusage[mem=800/host]" my_job

# 使用虚拟资源（用于特殊调度控制）
jsub -R "rusage[dummy=1]" my_job
```

---

## 3. span — 资源分布控制

### 作用

控制作业的 slots 在节点上的**分布方式**。用于指定作业占用节点的数量或每个节点分配的 slot 数。

### 语法

```
span[option=value]
```

### 支持的选项

| 选项 | 含义 | 说明 |
|------|------|------|
| `hosts` | 限制单节点运行 | 仅支持值 `1`，表示所有 slots 必须在同一台节点上 |
| `ptile` | 每节点 slot 数 | 指定每个节点分配给作业的 slot 数量 |

### 示例

```bash
# 所有 slots 必须在同一台节点上（单节点运行）
# hosts 仅支持值 1，不支持 hosts=2 等其他值
jsub -n 4 -R "span[hosts=1]" my_job

# 每个节点分配 2 个 slots（即使节点有更多空闲 slots）
jsub -n 4 -R "span[ptile=2]" my_job
# 结果：作业在 2 个节点上运行，每节点 2 个 slots

# 每个节点分配 1 个 slot
jsub -n 4 -R "span[ptile=1]" my_job
# 结果：作业在 4 个节点上运行，每节点 1 个 slot
```

**注意**：`span[hosts=N]` 目前仅支持 `N=1`，即限制作业在单节点运行。如需控制多节点分布，请使用 `span[ptile=N]` 间接实现。

---

## 4. 组合使用

三个关键字可以组合使用，用空格分隔。调度器会**同时满足所有条件**。

### 语法格式

```
-R "select[...] rusage[...] span[...]"
```

### 组合示例

```bash
# 选择 LINUX64 节点 + 预留 500MB 内存 + 所有 slots 在同一节点
jsub -n 4 -R "select[type==LINUX64] rusage[mem=500] span[hosts=1]" my_job

# 选择内存>1024MB 的节点 + 预留 800MB 内存和 200MB swap + 每节点 2 slots
jsub -n 8 -R "select[mem>1024] rusage[mem=800&&swap=200] span[ptile=2]" my_job

# 使用自定义资源标签 + 按 slot 预留内存
jsub -n 2 -R "select[gpu_node] rusage[mem=2000/slot]" my_job
```

---

## 5. 完整速查表

| 场景 | 命令示例 |
|------|----------|
| 选择特定 OS 类型 | `-R "select[type==LINUX64]"` |
| 选择内存充足的节点 | `-R "select[mem>800]"` |
| 选择内存>1GB 且 OS 为 LINUX64 | `-R "select[mem>1024 && type==LINUX64]"` |
| 选择特定 Boolean 资源标签 | `-R "select[ai_cs]"` |
| 预留内存 | `-R "rusage[mem=500]"` |
| 预留内存+交换区（同时满足） | `-R "rusage[mem=500&&swap=200]"` |
| 预留内存 或 交换区（满足其一） | `-R "rusage[mem=800||swap=5000]"` |
| 按 slot 预留内存（默认） | `-R "rusage[mem=800/slot]"` |
| 按 host 预留内存 | `-R "rusage[mem=800/host]"` |
| 单节点运行 | `-n 4 -R "span[hosts=1]"` |
| 每节点 2 个 slot | `-n 8 -R "span[ptile=2]"` |
| 每节点 1 个 slot（最大分散） | `-n 4 -R "span[ptile=1]"` |
| 选择 LINUX64 + 预留内存 + 单节点 | `-n 4 -R "select[type==LINUX64] rusage[mem=500] span[hosts=1]"` |
| 选择内存充足节点 + 预留资源 + 每节点2 slot | `-n 8 -R "select[mem>1024] rusage[mem=800] span[ptile=2]"` |
| 复杂条件 | `-R "select[((type==NTX64&&mem>50)\|\|(type==LINUX64&&mem>100))]"` |
| 独占节点 + 预留资源 + 单节点 | `-n 4 -x -R "rusage[mem=4000] span[hosts=1]"` |

---

## 6. 注意事项

1. **select 与 -m 的关系**：`select` 是基于资源属性的条件筛选，`-m` 是基于节点名称的指定。两者可以同时使用，取**交集**。

2. **rusage 默认按 slot 预留**：如果未指定 `/slot` 或 `/host`，非共享资源默认按 slot 预留。

3. **span[hosts] 仅支持 hosts=1**：`span[hosts=1]` 限制作业在单节点运行。不支持 `hosts=2` 等其他值。如需控制多节点分布，请使用 `span[ptile=N]`，其中 `N` 为每节点 slot 数。

4. **span[ptile] 的实际效果**：`span[ptile=N]` 表示每节点最多分配 N 个 slots。配合 `-n` 使用时，实际节点数 = ceil(slot总数 / ptile)。例如 `-n 6 -R "span[ptile=2]"` 会在 3 个节点上运行，每节点 2 个 slots。

5. **队列和应用级资源需求**：队列和应用也可以配置 `RES_REQ`，与作业级资源需求取交集。

6. **自定义资源**：管理员可在 `host.conf` 中定义 Boolean 资源和共享资源，用户在 `select` 和 `rusage` 中引用。

7. **特殊字符转义**：在 shell 中使用 `-R` 参数时，建议用双引号将整个资源需求字符串括起来，避免 shell 解释特殊字符。
