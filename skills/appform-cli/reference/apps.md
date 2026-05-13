# 应用参数参考

提交作业前必须查询参数，不同环境参数可能不同。

---

## 查询参数

### appform CLI

```bash
# 6.6+（推荐，参数与服务端同步）
appform jobs form <app_id>
appform -o json jobs form <app_id>

# 6.3 及以下
appform jobs params <app_id>
```

### 调度命令（集群内）

参数由 `job_submit.yaml` 配置文件定义，见各应用文档。

---

## 应用类型

| TYPE | 用途 | 提交方式 |
|------|------|---------|
| `batch` | 计算应用 | `appform jobs submit -a <app_id>` 或 `jsub -app <app_id>` |
| `desktop` | 交互应用 | `appform sessions start --app-id <app_id>` |

列出所有应用：`appform apps list`

---

## 各应用文档

- [StarCCM+](../apps/starccm.md) — CFD 仿真
- [Fluent](../apps/fluent.md) — CFD 仿真
- [LS-DYNA](../apps/ls-dyna.md) — 碰撞/冲击

> 以上文档中的参数值为参考，实际值以 `appform jobs form/params` 查询结果为准。
