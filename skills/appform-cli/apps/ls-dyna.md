# LS-DYNA

显式动力学有限元分析软件。

## 适用场景

- 碰撞与冲击模拟
- 爆炸仿真
- 成形仿真
- 跌落分析
- 安全性分析

## 参数速查

> 以 `appform jobs form ls-dyna` 或 `appform jobs params ls-dyna` 查询结果为准。
> 应用 ID 可能为 `lsdyna`、`ls-dyna`、`lsdyna2` 等，以 `appform apps list | grep -i dyna` 查询为准。

| 参数 | CLI 参数 | 说明 | 必填 | 默认值 |
|------|---------|------|------|--------|
| `JH_CAS` | `-i` | 输入文件路径（`.k`/`.key`/`.dyn`） | 是 | — |
| `JH_NCPU` | `-n` | 节点数 | 否 | `1` |
| `JH_RELEASE` | `-r` | 软件版本 | 否 | — |
| `JH_NODE_GROUP` | — | 节点组 | 否 | — |

## appform CLI 提交示例

```bash
# 确认应用 ID
appform apps list | grep -i dyna

# 查询参数
appform jobs form lsdyna2              # 6.6+（以实际 app_id 为准）

# 提交
appform jobs submit -a lsdyna2 -i /path/input.k -n 16

# --set 方式
appform jobs submit -a lsdyna2 \
  --set JH_CAS=/path/input.k \
  --set JH_NCPU=16
```

## jsub 提交示例（集群内）

```bash
job_submit -a lsdyna2 -i /path/input.k -n 16
```

## 后处理脚本（可选）

```bash
# post_lsdyna.sh 示例
#!/bin/bash
RESULT_DIR=$JH_SUB_CWD
# 提取能量曲线、生成动画
```
