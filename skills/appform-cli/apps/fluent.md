# Fluent (ANSYS Fluent)

计算流体力学 (CFD) 仿真软件。

## 适用场景

- 湍流模拟
- 传热与辐射
- 化学反应与燃烧
- 多相流
- 动网格

## 参数速查

> 以 `appform jobs form fluent` 或 `appform jobs params fluent` 查询结果为准。

| 参数 | CLI 参数 | 说明 | 必填 | 默认值 |
|------|---------|------|------|--------|
| `JH_CAS` | `-i` | 算例文件路径（`.cas`/`.cas.gz`） | 是 | — |
| `JH_DAT` | — | 数据文件路径（`.dat`/`.dat.gz`，可选） | 否 | — |
| `JH_NCPU` | `-n` | 节点数 | 否 | `1` |
| `JH_RELEASE` | `-r` | 软件版本 | 否 | — |
| `JH_NODE_GROUP` | — | 节点组 | 否 | — |

## appform CLI 提交示例

```bash
# 查询参数
appform jobs form fluent               # 6.6+
appform jobs params fluent             # 6.3 及以下

# 预览
appform jobs submit -a fluent -i /path/case.cas -n 32 --dry-run

# 提交
appform jobs submit -a fluent -i /path/case.cas -n 32

# 带数据文件
appform jobs submit -a fluent \
  --set JH_CAS=/path/case.cas \
  --set JH_DAT=/path/data.dat \
  --set JH_NCPU=32

# 指定版本
appform jobs submit -a fluent -i /path/case.cas -n 16 -r 2024R1
```

## jsub 提交示例（集群内）

```bash
# 通过 job_submit 工具
job_submit -a fluent -i /path/case.cas -n 32

# 带数据文件
job_submit -a fluent -i /path/case.cas /path/data.dat -n 32
```

## 后处理脚本（可选）

```bash
# post_fluent.sh 示例
#!/bin/bash
RESULT_DIR=$JH_SUB_CWD
# 提取收敛数据、生成报告
```
