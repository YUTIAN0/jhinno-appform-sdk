# appform CLI 命令参考

完整的 appform 命令行命令参考。

---

## 返回数据

`-o` 参数控制输出格式，放在 `appform` 之后、子命令之前：

| `-o` 值 | 输出 |
|---|---|
| `table` (默认) | 格式化表格 |
| `json` | 结构化的 JSON（模板过滤后） |
| `raw` | 接口原始 JSON（与 SDK 返回一致） |
| `text` | 纯文本 |

---

## 提交作业

```bash
# 方式 1：YAML profile 参数
appform jobs submit -a starccm -i /path/test.sim -n 32 -r 16.02

# 方式 2：--set 覆盖任意参数
appform jobs submit -a starccm \
  --set JH_CAS=/path/test.sim \
  --set JH_NCPU=32 \
  --set JH_RELEASE=16.02

# 方式 3：原始 JSON（无 YAML profile 或 6.6+）
appform jobs submit-raw --app-id starccm \
  --params '{"JH_CAS":"/path/test.sim","JH_NCPU":"32"}'

# 预览（不实际提交）
appform jobs submit -a starccm -i /path/test.sim --dry-run
```

---

## 查看作业

```bash
# 列表
appform jobs list
appform jobs list --page 1 --page-size 50
appform jobs list --status RUN          # 按状态过滤
appform jobs list --status PEND         # 等待中
appform jobs list --name cfd            # 按名称过滤
appform jobs list --job-id 1001,1002    # 按 ID 查询

# 按状态查看
appform jobs status RUN

# 详情
appform jobs get 1001

# 输出
appform jobs output 1001

# 历史
appform jobs history 1001
appform jobs history-page --page 1 --page-size 20
```

**状态含义：**

| 状态 | 说明 | 终态 |
|------|------|------|
| `RUN` | 运行中 | 否 |
| `PEND` | 排队等待 | 否 |
| `PSUSP` / `USUSP` / `SSUSP` | 挂起 | 否 |
| `DONE` | 正常完成 | 是 |
| `EXIT` | 异常退出 | 是 |
| `ZOMBI` | 异常 | 是 |

---

## 作业控制

```bash
appform jobs stop 1001          # 挂起（PSUSP），可 resume 恢复
appform jobs kill 1001          # 终止运行中作业，不可恢复
appform jobs suspend 1001       # 挂起（同 stop）
appform jobs resume 1001        # 恢复挂起的作业
appform jobs requeue 1001       # 重排队
appform jobs delete 1001        # 删除记录（仅 6.6+，低版本 405）
```

> **stop vs kill vs delete**：`stop` 挂起可恢复；`kill` 终止不可恢复；`delete` 删除记录（6.6+）。

---

## 作业文件管理

```bash
# 列出
appform jobs files 1001 ls
appform jobs files 1001 ls /path/inside/job

# 上传 / 下载
appform jobs files 1001 put local.txt
appform jobs files 1001 put local.txt /remote/path
appform jobs files 1001 get /remote/file ./local

# 查看内容
appform jobs files 1001 cat /path/to/file --head 20
appform jobs files 1001 cat /path/to/file --lines 10-
appform jobs files 1001 tailf /path/to/output.log   # 实时跟踪

# 重命名 / 移动 / 删除
appform jobs files 1001 mv /old /new
appform jobs files 1001 cp /src /dst
appform jobs files 1001 rm /path/to/file
appform jobs files 1001 mkdir /new/dir

# 计算节点 SSH 操作（需 ~/.appform/compute.yaml）
appform jobs files 1001 custom ls
appform jobs files 1001 custom cat /path/to/log
appform jobs files 1001 custom get /remote ./local
appform jobs files 1001 custom tailf /path/to/output.log

# 传输方式
appform jobs files 1001 ls --method sftp
appform jobs files --method sftp 1001 ls    # 组级别默认
```

---

## 文件操作（全局）

```bash
# 列出远程目录（第一行自动打印解析后的绝对路径）
appform files ls '$HOME'
appform files ls '$HOME' --all
appform files ls '$HOME' --method sftp
appform files ls '$HOME' --method http

# 上传 / 下载
appform files put local.txt /remote/path
appform files put local.txt /remote/path/newname.txt  # 重命名
appform files put local.txt                   # 使用 default_remote_path
appform files put local.txt /remote/path --method http
appform files get /remote/file ./local

# 创建目录 / 复制 / 移动 / 删除
appform files mkdir /new/dir
appform files cp /src /dst
appform files mv /old /new
appform files rm /path/to/file

# 查看内容
appform files cat /path/to/file --tail 10 --encoding utf-8

# 压缩 / 解压
appform files compress /source/dir /path/to/archive.tar.gz
appform files uncompress /path/to/archive.tar.gz /dest/dir

# 家目录
appform files home
appform files home --method sftp

# 密级
appform files conf --get-levels
appform files conf --set /path/to/file 机密
```

**默认远程路径：**

```bash
appform config set --default-remote-path '$HOME/work/'
# 省略远程路径时自动使用该目录；已指定路径时不生效
```

优先级：CLI 参数 > 环境变量 `APPFORM_DEFAULT_REMOTE_PATH` > 配置文件 > 默认 `/`

---

## 交互应用（会话）

```bash
# 启动
appform sessions start --app-id abaqus_cae --start-new
appform sessions start --app-id meta_post --start-new --work-file '$HOME/data/result.dat'

# 查看
appform sessions list
appform sessions list --ids sid1,sid2
appform sessions list --name abaqus_cae

# 连接
appform sessions connect session_id
appform sessions connect-launch session_id     # 自动启动 JHApp 客户端

# 断开 / 关闭
appform sessions disconnect session_id
appform sessions close session_id

# 分享
appform sessions share session_id --usernames user2,user3
```

`sessions start` 启动后若返回 jhappUrl，CLI 会自动尝试启动本地 JHApp 客户端，无客户端时静默降级。

---

## 应用列表

```bash
appform apps list
# TYPE=batch — 计算应用 → jobs submit -a <app_id>
# TYPE=desktop — 交互应用 → sessions start --app-id <app_id>
# 无 TYPE — 管理入口，不用于提交或会话
```

---

## 多环境配置

```bash
appform --env prod jobs list
appform --env dev jobs list

appform config set --environment prod --base-url https://prod.jhinno.com --api-version 6.6
```

优先级：`--env` 参数 > `APPFORM_ENV` 环境变量 > `config.json default_environment` > 根级别配置

---

## SFTP 主机密钥

```bash
appform config set --auto-add-host-key true    # 自动接受（适合自动化）
```

密钥保存在 `~/.appform/known_hosts`。
