# StarCCM+ (STAR-CCM+)

计算流体力学 (CFD) 仿真软件。

## 适用场景

- 外流空气动力学
- 内流（管道、阀门）
- 传热分析
- 多相流

## 参数速查

> 以 `appform jobs form starccm` 或 `appform jobs params starccm` 查询结果为准。

| 参数 | CLI 参数 | 说明 | 必填 | 默认值 |
|------|---------|------|------|--------|
| `JH_CAS` | `-i` | 算例文件路径（`.sim`） | 是 | — |
| `JH_NCPU` | `-n` | 节点数 | 否 | `1` |
| `JH_RELEASE` | `-r` | 软件版本 | 否 | `16.02` |
| `JH_NODE_GROUP` | — | 节点组 | 否 | — |
| `STAR_POST_SWITCH` | `-post` | 启用后处理（on/off） | 否 | `off` |

## appform CLI 提交示例

```bash
# 查询参数
appform jobs form starccm              # 6.6+
appform jobs params starccm            # 6.3 及以下

# 预览
appform jobs submit -a starccm -i /path/test.sim -n 16 --dry-run

# 提交
appform jobs submit -a starccm -i /path/test.sim -n 16 -r 16.02

# 带后处理
appform jobs submit -a starccm -i /path/test.sim -n 32 -r 20.02.007 -post

# --set 方式
appform jobs submit -a starccm \
  --set JH_CAS=/path/test.sim \
  --set JH_NCPU=16 \
  --set JH_RELEASE=20.02.007
```

## jsub 提交示例（集群内）

```bash
# 方式 1：通过 job_submit 工具
job_submit -a starccm -i /path/test.sim -n 16 -r 20.02.007

# 方式 2：直接用 jsub（需手动指定应用参数）
# 通常通过 job_submit 或 appform CLI 提交，不直接用 jsub
```

## 后处理脚本（可选）

```bash
# 通过 post-exec 自动触发
jsub -Ep post_starccm.sh -a starccm -i /path/test.sim -n 16

# post_starccm.sh 示例
#!/bin/bash
RESULT_DIR=$JH_SUB_CWD
# 提取关键结果、生成报告
```
