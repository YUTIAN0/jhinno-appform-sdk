# 景行资源管理与调度软件 命令行手册

> 版本范围：V6.0 ~ V6.6 | 共 28 个命令

## 目录

[1. japps](#japps)
[2. jattach V6.1+](#jattach)
[3. jbinds V6.3+](#jbinds)
[4. jchkpnt V6.5+](#jchkpnt)
[5. jcluster](#jcluster)
[6. jcode](#jcode)
[7. jconfig](#jconfig)
[8. jctrl](#jctrl)
[9. jdepinfo V6.4+](#jdepinfo)
[10. jectrl V6.4+](#jectrl)
[11. jexec](#jexec)
[12. jgetmsg](#jgetmsg)
[13. jhinfo](#jhinfo)
[14. jhist](#jhist)
[15. jhostgroup](#jhostgroup)
[16. jhosts](#jhosts)
[17. jhpasswd V6.6+](#jhpasswd)
[18. jjobs](#jjobs)
[19. jlimits](#jlimits)
[20. jmod](#jmod)
[21. jports](#jports)
[22. jputmsg](#jputmsg)
[23. jqueues](#jqueues)
[24. jrestart V6.5+](#jrestart)
[25. jsub](#jsub)
[26. jusergroup](#jusergroup)
[27. jusers](#jusers)
[28. jversion](#jversion)

---


## 1. japps

**功能**：主要用于显示有关应用程序的信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-w`**：以宽格式显示应用信息。
- **`-l`**：以长格式显示应用的详细信息。
- **`-bind`**：显示应用级的用户和节点绑定信息。

---


## 2. jattach V6.1+

**功能**：连接服务模式的交互式作业。


**选项**：

- **`-h`** V6.1+：打印命令使用方法。
- **`-V`** V6.1+：打印景行资源管理与调度软件发行版本信息。 - jobId：连接指定ID的作业。


**示例**：

> $ jsub -Is bash
> <<Starting on host1>>
> 当前端jsub -Is命令终止，后端作业不退出继续运行，jjobs查询作业状态为RUN时，可通过使用命令jattach加作业ID号，attach作业到终端继续接受交互式操作。
> $ jattach 13

---


## 3. jbinds V6.3+

**功能**：查询节点及GPU绑定信息。


**选项**：

- **`-h`** V6.3+：打印命令使用方法。
- **`-V`** V6.3+：打印景行资源管理与调度软件发行版本信息。
- **`-app`** V6.3+：显示应用级的节点及GPU绑定信息。
- **`-t`** `host|gpu` V6.6+：host参数只显示节点绑定信息，gpu参数只显示GPU绑定信息。 - **命令示例** $ jbinds jhadmin=host1 host2 host3:GPU0,GPU1 $ jbinds -t host jhadmin=host1 host2 $ jbinds -t gpu jhadmin=host3:GPU0,GPU1

---


## 4. jchkpnt V6.5+

**功能**：设置作业检查点。


**选项**：

- **`-h`** V6.5+：打印命令使用方法。
- **`-V`** V6.5+：打印景行资源管理与调度软件发行版本信息。
- **`-k`** V6.5+：checkpoint成功后结束作业。
- **`-d`** V6.5+：指定checkpoint数据保存目录

---


## 5. jcluster

**功能**：显示集群名称及集群主节点名称。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。 - init：初始化集群master节点 - join：初始化非master集群并加入集群 - clean：清除已初始化的集群节点

---


## 6. jcode

**功能**：显示错误码的释义信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-all`**：显示所有错误码和相应的错误码释义。
- **`-e`** `code [code ...]`：显示作业错误码和相应的错误码释义。
- **`-r`** `code [code ...]`：显示gui图形作业错误码和相应的错误码释义。
- **`-p`** `code [code ...]`：显示作业挂起原因错误码和相应的错误码释义。
- **`-zh`** V6.1+：显示挂起原因的中文释义。 - 注意： 设置 export LANG=zh_CN 环境变量后，再使用jcode命令可查看中文错误码释义。


**示例**：

> \# export LANG=zh_CN
> \# jcode -e 10036
> 10036: 许可证失败
> \# jcode -r 2001 2002 2006 2009
> 2001: Gui作业失败次数达到上限
> 2002: Gui作业信息读取错误
> 2006: Gui 作业因初始化失败而退出
> 2009: Gui 作业申请会话失败

---


## 7. jconfig

**功能**：jconfig是用于管理unischeduler配置文件的工具，仅支持root和集群主管理员用户使用此命令修改或更新调度参数配置。

**用法**：

```bash
jconfig
  set：修改配置项（jconfig set命令只支持修改MASTER_CANDIDATES、REDIS_PORT和PRIVATE_PORT配置）。
  jconfig命令仅支持对下列配置文件进行修改或更新：
  通过jconfig list jhds.conf命令查看配置文件中的可修改或可更新的配置项：
  \# jconfig list jhds.conf
  \# jconfig update jhds.conf max_connections=10
  [jhds.conf]
  max_connections=5 => max_connections=10
```


**示例**：

> 将host1 host2 host3通过以下命令设置为候选主节点，并根据提示信息执行相关命令使其生效：
> \# jconfig set MASTER_CANDIDATES='host1 host2 host3'
> to make the configuration effective, please run the following:
> jadmin schedreconfig
> jadmin jhdsreconfig
> 将redis服务端口通过以下命令设置为9322，并根据提示信息执行相关命令使其生效：
> \# jconfig set REDIS_PORT=9322
> unischeduler stop all
> unischeduler start
> 将scheduler.conf文件中CLUSTER_NAME的值更新为jhadmin user1（增加管理员user1，jhadmin是主管理员）：
> \# jconfig update scheduler.conf CLUSTER_NAME='jhadmin user1'
> to make the configuration effective, please run the following:
> jadmin schedreconfig

---


## 8. jctrl

**功能**：主要用于作业控制，比如kill作业或者停止一个作业等。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。 - 子命令stop（挂起作业）： 概要： jctrl stop [-h] [-m host_name] [-q queue_name] [-u user_name | -u all] [-J job_name] [-app application_name] jobId | jobId[index_list] | 0 [jobId | jobId[index_list] | 0 ...] 选项：
- **`-h`**：打印命令使用方法。
- **`-m`** `host_name`：仅挂起分派到指定主机或主机组的作业。
- **`-q`** `queue_name`：仅挂起指定队列中的作业。
- **`-u`** `user_name | -u all`：仅暂停指定用户或用户组拥有的作业，如果指定了关键字 all，表示暂停所有用户的作业。
- **`-J`** `job_name`：仅挂起具有指定作业名称的作业。
- **`-app`** `application_name`：仅暂停指定应用程序中的作业。 - 子命令resume（恢复挂起的作业）： 概要： jctrl resume [-h] [-m host_name] [-q queue_name] [-u user_name | -u all] [-J job_name] [-app application_name] jobId | jobId[index_list] | 0 [jobId | jobId[index_list] | 0 ...] 选项：
- **`-h`**：打印命令使用方法。
- **`-m`** `host_name`：恢复指定节点或者节点组上已被挂起的作业。
- **`-q`** `queue_name`：恢复指定队列中已被挂起的作业。
- **`-u`** `user_name | -u all`：恢复指定用户或者所有用户已被挂起的作业。
- **`-J`** `job_name`：恢复已被挂起的指定作业名称的作业。
- **`-app`** `application_name`：只恢复指定应用程序中的作业。 - 子命令kill（发送特定信号停止一个作业）： 概要： jctrl kill [-h] [-m host_name] [-q queue_name] [-u user_name | -u all] [-J job_name] [-f] [-app application_name] jobId | jobId[index_list] | 0 [jobId | jobId[index_list] | 0 ...] 选项：
- **`-h`**：打印命令使用方法。
- **`-m`** `host_name`：停止指定节点上的作业。
- **`-q`** `queue_name`：停止指定队列上的作业。
- **`-u`** `user_name | -u all`：停止指定用户提交的作业，若指定参数为all，表示终止所有用户未完成的作业。
- **`-J`** `job_name`：停止指定作业名称的作业。
- **`-f`**：强制从非调度程序系统中终止作业，而无需等待作业在操作系统中终止。
- **`-app`** `application_name`：停止指定应用程序中的作业。 - 子命令bot（将等待状态的单个或多个作业移动到队列尾部）： 概要： jctrl bot [-h] [-c] [-p position] jobId | jobId[index] [jobId | jobId[index] ...] 选项：
- **`-h`**：打印命令使用方法。
- **`-c`**：可选，指定操作是集群级别。
- **`-p`** `position`：可选，可以指定 position 参数以指示将作业放置在用户或集群中的哪个位置，position 是一个正整数，表示作业从用户或集群的末尾开始的目标位置。

- 子命令start（强制作业执行）：
 概要：
 jctrl start [-h] [-f] -m host_name jobId [jobId ...]
 选项：
 - **`-h`**：打印命令使用方法。
 - **`-m`** `host_name`：指定作业强制运行的节点。对于并行作业，可指定节点列表（节点数不少于作业请求的最小进程数）。
 - **`-f`**：忽略节点资源负载条件限制，使被强制执行的作业能够运行完成（仅管理员/root）。
 说明：
 - 强制作业执行一般只能由管理员或root用户进行
 - 被强制执行后，作业的资源需求条件、依赖关系、抢占式调度、fairshare调度和作业限制均被忽略
 - 强制运行的作业不能被抢占

- 子命令requeue（作业重排队）：
 概要：
 jctrl requeue [-h] [-a] [-m host_name] [-q queue_name] [-u user_name | -u all] [-J job_name] [-app application_name] jobId | jobId[index_list] | 0 [jobId | jobId[index_list] | 0 ...]
 选项：
 - **`-h`**：打印命令使用方法。
 - **`-a`**：对所有作业生效。
 - **`-m`** `host_name`：仅重排派发到指定节点的作业。
 - **`-q`** `queue_name`：仅重排指定队列中的作业。
 - **`-u`** `user_name | -u all`：仅重排指定用户或所有用户的作业。
 - **`-J`** `job_name`：仅重排具有指定作业名称的作业。
 - **`-app`** `application_name`：仅重排指定应用程序中的作业。
 说明：
 - 可对所有状态的作业进行重排队（PEND/PSUSP/RUN/USUSP/SSUSP/DONE/EXIT）
 - 作业被重排后置为PEND状态，放置在同优先级作业之后
 - 普通用户只能重排自己的作业；管理员/root可重排任意用户的作业

- 子命令peek（查看作业输出）：
 概要：
 jctrl peek [-h] [-f] [-t [task id]] jobId | jobId[index]
 选项：
 - **`-h`**：打印命令使用方法。
 - **`-f`**：实时打印显示运行作业的执行输出到屏幕上。
 - **`-t`** `[task id]`：查询指定的任务输出。
 说明：
 - 只有作业的所有者可以查看自己的作业输出
 - 默认使用随机分配的TCP/IP端口，可通过private_port自定义端口范围（1024-65535）

- 子命令clean（手动清理作业缓存）：
 概要：
 jctrl clean [-h] [-u user_name | -u all] jobId | jobId[index_list] | 0 [jobId | jobId[index_list] | 0 ...]
 选项：
 - **`-h`**：打印命令使用方法。
 - **`-u`** `user_name | -u all`：清理指定用户或所有用户已完成的作业缓存。
 说明：
 - 用于清除节点内存中已完成作业的信息，及时释放占用资源
 - 支持批量清理
 - 数组作业必须在所有子作业全部完成后才能被清理


**示例**：

> 同时对多个PEND状态的作业进行置底排序，-p 2表示将等待作业置底排序到第2位。
> [user1@host1 apps]$ jctrl bot -p 2 241 243 242
> [user1@host1 apps]$ jjobs
> 237 user1 RUN normal host1 host2 sleep 1000 Mar 30 15:40 -
> 238 user1 RUN normal host1 host2 sleep 1000 Mar 30 15:40 -
> 239 user1 PEND normal host1 sleep 1000 Mar 30 15:40 1
> 241 user1 PEND normal host1 sleep 1000 Mar 30 15:40 2
> 243 user1 PEND normal host1 sleep 1000 Mar 30 15:40 3
> 242 user1 PEND normal host1 sleep 1000 Mar 30 15:40 4
> 240 user1 PEND normal host1 sleep 1000 Mar 30 15:40 5
> - 子命令top（将等待状态的单个或多个作业移动到队列顶部）：
> jctrl top [-h] [-c] [-p position] jobId | jobId[index] [jobId | jobId[index] ...]
> - -h：打印命令使用方法。

---


## 9. jdepinfo V6.4+

**功能**：显示指定作业的父作业或子作业


**选项**：

- **`-h`** V6.4+：打印命令使用方法。
- **`-V`** V6.4+：打印景行资源管理与调度软件发行版本信息。
- **`-r`** `level` V6.4+：递归显示依赖的父作业。
- **`-l`** V6.4+：显示导致当前作业挂起的父作业的详细信息。
- **`-p`** V6.4+：显示导致当前作业挂起的父作业。 - 子命令child： 概要： usage: jdepinfo child [-h] [-r level] [-l] [jobID | jobID[index]] 选项：
- **`-h`** V6.4+：打印命令使用方法。
- **`-r`** `level` V6.4+：递归显示子作业。
- **`-l`** V6.4+：显示子作业信息，不截断字段


**示例**：

> 显示指定作业的父作业。
> $jdepinfo 3
> 3 1 DONE sleep 10000 1
> 3 2 DONE sleep 5 1
> 显示导致指定作业挂起的父作业的详细信息。
> $jdepinfo -p -l 4
> The dependency condition of job<4> is not satisfied: exit(1) && ended(2)
> 4 1 DONE sleep 10000 1
> 递归显示指定作业的子作业，不截断字段
> $ jdepinfo child -r 1 -l 1
> 1 4 PEND hostname 1
> 1 3 DONE hostname 1

---


## 10. jectrl V6.4+

**功能**：管理弹性作业


**选项**：

- **`-h`** V6.4+：打印命令使用方法。
- **`-V`** V6.4+：打印景行资源管理与调度软件发行版本信息。 - 子命令jectrl apply：提交或修改功能资源定义 usage: jectrl apply [-h] [-f manifest file] [-name [ name ]]
- **`-h`** V6.4+：打印命令使用方法。
- **`-f`** V6.4+：指定功能资源定义文件。
- **`-name`** V6.4+：指定service名称，替换manifest file 中配置的service 名。 - 子命令jectrl get： 查询功能资源对象数据 usage: jectrl get [-h] [-w | -l] [-spec] resource-type > [resource-name [resource-name ...]]
- **`-h`** V6.4+：打印命令使用方法。
- **`-w`** V6.4+：以宽格式形式显示详细信息
- **`-l`** V6.4+：以长格式显示详细信息
- **`-spec`** V6.4+：打印功能资源的规格定义 - resource-type：指定功能资源类型 - resource-name：指定功能资源名称 - 子命令jectrl stop： 停止deployment功能资源对象 usage: jectrl stop [-h] resource-type resource-name [resource-name ...]
- **`-h`** V6.4+：打印命令使用方法。 - resource-type：指定功能资源类型 - resource-name：指定功能资源名称 - 子命令jectrl start： 启动被停止的deployment功能资源对象 usage: jectrl start [-h] resource-type resource-name [resource-name ...]
- **`-h`** V6.4+：打印命令使用方法。 - resource-type：指定功能资源类型 - resource-name：指定功能资源名称 - 子命令jectrl scale： 为deployment功能资源对象设置一个新实例数 usage: jectrl scale [-h] -instances instances resource-type > resource-name [resource-name ...]
- **`-h`** V6.4+：打印命令使用方法。 - resource-type：指定功能资源类型 - resource-name：指定功能资源名称 - instances：指定新的实例数 - 子命令jectrl delete： 删除功能资源对象 usage: jectrl delete [-h] resource-type resource-name > [resource-name ...]
- **`-h`** V6.4+：打印命令使用方法。 - resource-type：指定功能资源类型 - resource-name：指定功能资源名称

---


## 11. jexec

**功能**：远程执行任务。


**选项**：

- **`-t`**：指定执行结果的超时时间。
- **`-m`**：指定执行节点。
- **`-e`**：指定节点的筛选条件。
- **`-a`**：异步执行命令
- **`-l`**：指定 log 级别。
- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。 - args...：传递特定命令的参数。

---


## 12. jgetmsg

**功能**：获取通过jputmsg添加到作业的信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-i`** `index`：设置指定的信息索引。 - job_ID | "job_ID[index]"：指定特定的作业或者作业数组。


**示例**：

> 获取信息索引为1的101号作业的信息。
> $jgetmsg -i 1 101

---


## 13. jhinfo

**功能**：显示系统中所有可用的资源信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。

---


## 14. jhist

**功能**：显示集群中当前用户的作业历史信息，默认显示当前用户的所有等待、运行和被挂起的作业信息。

**用法**：

```bash
jhist
  jhist [-h] [-V] [-a] [-d] [-e] [-p] [-r] [-s] [-w | -l]
  [-S time0,time1] [-t] [-f logfile_name | -n 0] [-J job_name]
  [-Jd job_desc] [-P project_name] [-q queue_name]
  [-app application_name] [-u user_name|all]
  [jobId | jobId[index_list] [jobId | jobId[index_list] ...]]
```


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-a`**：显示所有未完成和已完成的作业历史信息。
- **`-d`**：仅显示已完成或退出作业信息。
- **`-e`**：仅显示未正常完成的作业历史信息。
- **`-p`**：仅显示等待状态的作业历史信息。
- **`-r`**：仅显示运行状态的作业历史信息。
- **`-s`**：仅显示已被挂起的作业历史信息。
- **`-w`**：以宽格式形式显示信息。
- **`-l`**：以长格式形式显示更为详细的信息。
- **`-S`** `time0,time1`：仅显示有关在指定时间间隔内提交的作业的信息。
- **`-t`**：显示指定的DJM容器作业事件信息。
- **`-f`** `logfile_name`：搜索指定路径下的日志文件。
- **`-n`** `0`：搜索所有事件日志。
- **`-J`** `job_name`：仅显示特定的作业历史信息。
- **`-Jd`** `job_desc`：仅显示指定作业描述的作业历史信息。
- **`-P`** `project_name`：仅显示指定项目的作业历史信息。
- **`-q`** `queue_name`：仅显示指定队列的作业历史信息。
- **`-app`** `application_name`：仅显示有关提交给指定应用程序的作业的信息。
- **`-u`** `user_name|all`：显示指定用户提交的作业信息，如果指定关键字all，则显示所有用户提交的作业信息。


**示例**：

> 显示用户user1的所有作业的详细历史信息。
> $jhist -a -l -u user1
> 显示指定时间间隔内提交的作业信息。
> $jhist -S "2025-04-27,2025-04-27"
> 注：指定的时间格式为"YYYY-MM-DD HH:MM:SS"，支持时间格式缺省时分秒。当缺省时分秒时，time0时间的时分秒填充为00:00:00，time1时间的时分秒填充为23:59:59。

---


## 15. jhostgroup

**功能**：显示集群中定义的节点组信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-r`**：递归展开节点组信息，在展开列表中只显示节点名，不包含节点子组名称，且重复的节点名称只列出一次。
- **`-w`**：以宽格式形式显示节点组信息。 - group_name：显示指定节点组的信息。

---


## 16. jhosts

**功能**：显示节点资源及负载信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-w`**：以宽格式形式显示详细信息。
- **`-l`**：以长格式形式显示详细信息。
- **`-R`** `res_req`：显示满足特定资源需求的节点信息。
- **`-s`** `[res_name [res_name ...]]`：查询节点上的共享资源信息，不能与其他参数一起使用。 - 子命令jhosts stat： - jhosts stat：显示节点负载信息。
- **`-h`**：打印命令使用方法。
- **`-l`**：以长格式形式显示详细信息。
- **`-w`**：以宽格式形式显示详细信息。
- **`-n`**：不换行显示主机信息。 - 子命令jhosts attrib： - jhosts attrib：显示主机及其静态资源信息。
- **`-h`**：打印命令使用方法。
- **`-l`**：以长格式形式显示详细信息。
- **`-w`**：以宽格式形式显示详细信息。 - 子命令jhosts remove： - jhosts remove：从集群中删除处于宕机状态的主机信息。
- **`-h`**：打印命令使用方法。


**示例**：

> 显示节点host1的状态和作业资源信息。
> $jhosts -l host1
> 显示集群中内存大于600MB的节点信息。
> $jhosts -R "select[mem>600]"

---


## 17. jhpasswd V6.6+

**功能**：注册用户账号密码。


**选项**：

- **`-h`** V6.6+：打印命令使用方法。
- **`-V`** V6.6+：打印景行资源管理与调度软件发行版本信息。
- **`-s`** V6.6+：上传jhspwd.dat的内容到redis
- **`-u`** V6.6+：增加用户密码信息
- **`-d`** V6.6+：删除用户密码信息

---


## 18. jjobs

**功能**：显示作业信息。

**用法**：

```bash
jjobs
  jjobs [-h] [-V] [-w | -l] [-a] [-d] [-p] [-s] [-r] [-A] [-m host_name]
  [-q queue_name] [-app application_name] [-u user_name | -u all]
  [-P project_name] [-o "field_name[:[-][output_width]] ...
  [delimiter='character']"] [-J name_spec] [-Jd desc_spec] [-env]
  [-t] [-regexp]
  [jobId [jobId ...]]
```


**选项**：

- **`-h`**：显示此帮助信息。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-w`**：以宽格式显示作业的详细信息。
- **`-l`**：以长格式显示作业的详细信息。
- **`-a`**：显示一定时间范围内所有状态的作业信息。
- **`-d`**：显示一定时间范围内已经结束的作业信息。
- **`-p`**：显示作业状态为pend的作业信息，并显示pend的原因。
- **`-s`**：显示作业状态为suspend的作业信息，并显示suspend的原因。
- **`-r`**：显示作业状态为run的作业信息。
- **`-A`**：显示作业数组信息。
- **`-m`** `host_name`：显示已经派发到指定节点上的作业信息。
- **`-q`** `queue_name`：显示指定队列上运行作业信息。
- **`-app`** `application_name`：只显示指定应用程序中的作业。
- **`-u`** `user_name | -u all`：只显示指定用户/用户组提交的作业，关键字'all'指定所有用户。
- **`-P`** `project_name`：显示指定项目的作业信息。
- **`-o`**：显示自定义输出格式的作业信息。
- **`-J`** `name_spec`：显示指定作业名称的作业或者作业数组的信息。
- **`-Jd`** `desc_spec`：指定作业的描述信息。
- **`-env`**：显示指定作业提交环境中的环境变量。
- **`-t`**：显示指定djm作业的任务信息。
- **`-task`** V6.4+：显示指定服务作业的任务信息。
- **`-regexp`**：在筛选条件中使用正则表达式。


**示例**：

> 显示用户user1的等待作业信息和作业的PENDING REASONS。
> $jjobs -p -u user1
> 显示节点host1上所有正在运行的作业信息。
> $jjobs -r -m host1
> 显示在队列short上且项目名称为my_project的所有用户的作业信息。
> $jjobs -q short -P my_project -u all
> 显示指定的作业详细信息。
> $jjobs -l job_id
> 按照指定格式输出作业信息（jobid宽度为4，stat宽度为10，并右对齐，分隔符为分号）。
> jjobs -o "jobid:4 stat:-10 from_host delimiter=';'"

---


## 19. jlimits

**功能**：主要用于显示集群中用户的cpu和作业的限制信息以及最小限制信息。

**用法**：

```bash
jlimits
  jlimits [-h] [-V] [-s | -c | -n] [-u user_name|user_group|all]
  [-m host_name|host_group|all] [-q queue_name|all]
  [-app application_name|all] [-w]
```


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-s`**：显示没有指定队列、应用和节点配置的用户或用户组详细的作业限制信息。
- **`-c`**：显示用户的作业限制配置信息。
- **`-n`** V6.3+：显示用户在指定队列和应用中的资源限制值，用户提交作业前可以清晰地了解当前因资源限制的可用资源数量。
- **`-u`** `user_name|user_group|all`：显示集群中用户和用户组的相关CPU和作业限制信息。
- **`-m`** `host_name|host_group|all`：显示集群中主机的相关CPU和作业限制信息。
- **`-q`** `queue_name|all`：显示集群中队列的相关CPU和作业限制信息。
- **`-app`** `application_name|all`：显示集群中应用的相关CPU和作业限制信息。
- **`-w`**：宽格式显示CPU和作业限制信息，不截取字段。


**示例**：

> 显示集群中user1用户的相关CPU和作业限制信息。
> $jlimits -u user1
> 显示集群中所有用户的相关CPU和作业限制信息。
> $jlimits -u all
> 显示集群中主机名称是host2相关的CPU和作业限制信息。
> $jlimits -m host2
> 显示集群中所有主机的相关CPU和作业限制信息。
> $jlimits -m all
> 显示集群中队列名称是queue1相关的CPU和作业限制信息。
> $jlimits -q queue1
> 显示集群中所有队列的相关CPU和作业限制信息。
> $jlimits -q all
> 显示集群中应用名称是app1相关的CPU和作业限制信息。
> $jlimits -app app1
> 显示集群中所有应用的相关CPU和作业限制信息。

---


## 20. jmod

**功能**：修改作业提交时指定的选项参数值。

**用法**：

```bash
jmod
  jmod [-h] [-V] [-L login_shell | -Ln] [-R res_req | -Rn]
  [-q queue_name | -qn]
  [-m host_name[+[pref_level]] | host_group[+[pref_level]]... | -mn]
  [-n min_processors[,max_processors] | -nn] [-J job_name | -Jn]
  [-Jd job_desc | -Jdn]
  [-gpgpu num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize] [mig=gsize]]
  [-nnode num nselect[core(num) mem(size) gpgpu(num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize])]]
  [-nnoden] [-app application_name | -appn]
```


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-L`** `login_shell`：使用指定的登录shell修改执行环境。
- **`-Ln`**：取消作业级登录shell命令的设置。
- **`-R`** `res_req`：修改作业指定的资源要求。
- **`-Rn`**：取消作业级资源需求命令的设置。
- **`-q`** `queue_name`：修改作业指定的执行队列。
- **`-qn`**：取消作业指定的执行队列。
- **`-m`** `"host_name[+[pref_level]] | host_group[+[pref_level]]..."`：修改作业指定的执行主机。
- **`-mn`**：取消作业指定的执行主机。
- **`-n`** `min_processors[,max_processors]`：修改作业指定的最小和最大处理器数。
- **`-nn`**：取消作业指定的最小和最大处理器数。
- **`-J`** `job_name`：修改作业名称或修改作业数组。
- **`-Jn`** `job_name` V6.4+：取消修改作业名称或修改作业数组。
- **`-Jd`** `job_desc`：修改作业描述信息。
- **`-Jdn`**：删除作业描述信息。
- **`-gpgpu`** `"num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize] [mig=gsize]"`：修改 GPU 请求。
- **`-gpgpun`**：取消GPU请求。
- **`-nnode`** `"num nselect[core(num) mem(size) gpgpu(num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize])]"` V6.5+：修改作业指定NUMA Node请求。
- **`-nnoden`** V6.5+：取消作业指定NUMA Node请求。
- **`-app`** `application_name`：修改作业指定的执行应用程序。
- **`-appn`**：取消工作指定的执行申请。
- **`-hosts`** `"num [hselect=hselect_string]"`：修改host num请求。
- **`-hostsn`**：取消作业指定的host num请求。
- **`-port`** `num`：修改端口请求。
- **`-portn`**：取消端口请求。
- **`-mf`** `file`：修改作业指定的机器文件。
- **`-mfn`**：取消作业指定的机器文件。
- **`-aps`** `priority`：修改作业aps优先级。
- **`-apsn`**：取消作业指定的优先级。
- **`-M`** `mem_limit`：修改内存限制，单位为MB。
- **`-Mn`**：取消作业的内存限制。
- **`-W`** `run_limit`：修改作业的运行时间限制，单位为分钟。runtime的格式是hours:minutes，-hours:minutes或者+hours:minutes。
- **`-Wn`**：取消作业指定的运行时间限制。
- **`-ux`** V6.5+：修改作业为用户独占节点的作业。
- **`-uxn`** V6.5+：取消作业指定的用户独占节点功能。
- **`-P`** `project_name`：修改作业的项目名称。
- **`-loadgpu`** V6.3+：挂载GPU。
- **`-unloadgpu`** V6.3+：卸载GPU，组合使用-force参数将终止GPU进程。
- **`-w`** `'status(job_ID | "job_name")...'` V6.4+：修改作业运行依赖的条件。其中status为支持的作业状态：done, ended, exit, started, post_done，post_err，可以使用&&、||、!逻辑符连接依赖多个条件。在windows系统中依赖条件需要用双引号括起，在linux的csh中，依赖条件需要用单引号括起’!’需要改写为’\\’。
- **`-wn`** V6.4+：取消作业的依赖条件。


**示例**：

> 修改指定作业的提交队列 test1。
> $jmod -q test1 jobID
> 取消指定作业的提交队列。
> $jmod -qn jobID
> 给指定作业的运行时间限制，增加50分钟的运行时间。
> $jmod -W +50 jobID
> $jmod -W +00:50 jobID
> 给指定作业的运行时间限制，减少2小时的运行时间。
> $jmod -W -120 jobID
> $jmod -W -02:00 jobID
> 修改指定作业的作业名称
> $ jmod -J "hello1" 18
> $ jjobs 18
> 18 jhadmin RUN normal host1 host2 hello1 May 15 14:58 -
> 取消指定作业的作业名称

---


## 21. jports

**功能**：显示端口资源信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-l`**：以长格式显示作业和分配的端口资源信息。

---


## 22. jputmsg

**功能**：用于给指定的作业添加信息或者文件。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-i`** `index`：指定需要添加的信息或者文件的索引。
- **`-d`** `"description"`：指定需要添加的描述信息。 - jobId | "jobId[idxList]"：指定特定的作业或者作业数组。


**示例**：

> 给作业号为101的作业添加描述信息为“string”，并指定作业索引为1。
> $jputmsg -i 1 -d "string" 101

---


## 23. jqueues

**功能**：显示集群中队列的相关信息。默认显示集群中所有队列的以下信息：队列名称、队列优先级、队列状态、作业槽信息和作业状态信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-w`**：以宽格式形式显示队列信息。
- **`-l`**：以长格式形式显示队列的详细信息。
- **`-m`** `host_name`：显示指定节点或节点组上能够运行作业的队列信息。
- **`-u`** `user_name`：显示指定用户或用户组所属的队列信息。 - queue_name：显示指定队列信息。


**示例**：

> 显示节点host1及用户user1所属的队列信息。
> $jqueues -m host1 -u user1

---


## 24. jrestart V6.5+

**功能**：作业从检查点恢复。


**选项**：

- **`-h`** V6.5+：打印命令使用方法。
- **`-V`** V6.5+：打印景行资源管理与调度软件发行版本信息。
- **`-d`** V6.5+：指定使用的checkpoint数据目录

---


## 25. jsub

**功能**：提交作业

**用法**：

```bash
jsub
  jsub [-h] [-V] [-x] [-ux] [-H] [-I] [-IX] [-Is] [-djm] [-pjm]
  [-L login_shell] [-P project_name] [-R res_req] [-q queue_name]
  [-app application_name]
  [-m "host_name[+[pref_level]] | host_group[+[pref_level]]..."]
  [-n min_processors[,max_processors]] [-J job_name] [-Jd job_desc]
  [-i in_file] [-o out_file] [-e err_file]
  [-E pre_exec_command[argument...]]
  [-Ep post_exec_command[argument...]]
  [-cwd current_working_directory]
  [-gpgpu "num [type=...] [vendor=...] [gmem=...] [sm=...] [mig=...]"]
  [-nnode "num nselect[core(N) mem(S) gpgpu(N ...)]"]
  [-hosts "num [hselect=hselect_string]"]
  [-port num] [-f [host:]local_file operator [remote_file]]
  [-w 'status(job_ID | "job_name")...']
  [-b "YYYY-MM-DD HH:MM"] [-t "YYYY-MM-DD HH:MM"]
  [-M mem_limit] [-W run_limit] [-We limit]
  [-mf file] [-aps priority] [-r] [-rn]
  [job_command [argument...]]
```


**选项**：

- **`-h`**：显示此帮助信息。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-x`**：以独占整个节点模式运行作业。作业独占执行节点，该节点上不允许运行其他任何用户的作业。与 `-ux` 的区别：`-x` 是整个节点独占，其他用户和当前用户的其他作业均不可在该节点运行；`-ux` 是用户独占，仅当前用户独占该节点，其他用户的作业不受影响。
- **`-ux`** V6.5+：以用户独占节点模式运行作业。同一用户的其他作业不可在该节点运行，但其他用户的作业可以共享该节点。与 `-x` 配合使用时，`-x` 优先级更高。
- **`-H`**：提交一个暂时不执行的作业（PSUSP 状态）。作业提交后不会被调度，需使用 `jctrl start jobId` 手动释放后才会进入正常调度流程。适用于需要预先提交但延迟执行的场景。
- **`-I`**：提交一个交互式作业。
- **`-IX`**：提交一个带X11转发功能的交互式作业。
- **`-Is`** V6.1+：提交一个服务模式的交互式作业。
- **`-djm`** V6.3+：提交一个分布式作业。
- **`-pjm`** V6.4+：提交一个并行作业。
- **`-L`** `login_shell`：指定shell登录并执行作业，支持的 shells 有：sh、bash、csh 和 tcsh。默认支持在登录 shell 执行作业前自动加载执行端用户的 profile 环境变量。使用场景：当作业脚本依赖特定 shell 特性（如 bash 数组、csh 别名等）时，通过 `-L` 指定对应的 shell 执行。
- **`-P`** `project name`：指定提交作业的项目名称。
- **`-R`** `res_req`：指定提交作业特定的资源需求信息。资源需求由一个或多个资源需求字符串组成，调度器据此选择合适的执行节点并预留资源。支持三个关键字，可组合使用（空格分隔）：

  **select — 资源选择条件**：指定选择执行节点的条件，只有满足条件的节点才会被考虑。格式：`select[condition]`。支持的资源属性：

  | 属性 | 类型 | 说明 | 示例 |
  |------|------|------|------|
  | `type` | 字符串 | 节点操作系统类型 | `type==LINUX64`、`type==NTX64` |
  | `mem` | 数值(MB) | 节点可用内存 | `mem>800` |
  | `swap` | 数值(MB) | 节点可用交换区 | `swap>500` |
  | `tmp` | 数值(MB) | 节点可用临时存储 | `tmp>300` |
  | `ncpus` | 整数 | 节点CPU核数 | `ncpus>=4` |
  | `ndisks` | 整数 | 节点磁盘数 | `ndisks>0` |
  | 自定义Boolean资源 | 字符串 | 管理员自定义的节点资源标签 | `ai_cs`、`gpu_node` |

  运算符：`==`（等于）、`!=`（不等于）、`>`（大于）、`<`（小于）、`>=`（大于等于）、`<=`（小于等于）、`&&`（与）、`||`（或）。

  **rusage — 资源预留**：指定作业在执行节点上需要预留的资源数量。格式：`rusage[resource=value ...]`。支持的资源：`mem`（内存，MB）、`swap`（交换区，MB）、`tmp`（临时存储，MB）、`dummy`（虚拟资源）。预留方式：

  - `mem=800/slot` — 按 slot 预留，预留值 × 节点分配的 slot 数
  - `mem=800/host` — 按 host 预留，每节点固定预留指定值
  - `mem=800` — 默认按 slot 预留（等同于 `/slot`）
  - 共享资源预留是作业级别的，不乘以 slot 数

  支持 `&&`（同时满足）和 `||`（满足其一）组合多个资源条件。

  **span — 资源分布控制**：控制作业的 slots 在节点上的分布方式。格式：`span[option=value]`。

  - `span[hosts=1]` — 所有 slots 必须在同一台节点上（单节点运行），仅支持值 `1`
  - `span[ptile=N]` — 每个节点分配 N 个 slots 给该作业

  **组合使用**：三个关键字可同时使用，空格分隔，调度器同时满足所有条件。例：`-n 4 -R "select[type==LINUX64] rusage[mem=500] span[hosts=1]"`
- **`-q`** `queue_name`：指定提交作业的队列。
- **`-app`** `application_name`：提交作业到指定的应用程序。
- **`-m`** `"host_name[+[pref_level]] | host_group[+[pref_level]]..."`：指定作业可选择的执行节点或者节点组。支持以下用法：

  **节点优先权重**：在节点或节点组后使用 `+N` 添加优先权重，数值越大优先级越高。

  ```bash
  # hostC 权重最高，其次是 hostB，最后是 hostA
  jsub -m "hostA hostB+1 hostC+2" my_job
  ```

  **排除节点**：使用 `~` 前缀排除指定节点或节点组。若用户有一个大型集群，希望暂时排除一些节点，此方式简单有效。

  ```bash
  # 从所有节点中排除 host2 和 hostB
  jsub -m "~host2 ~hostB" my_job

  # 从 hostgroupA 中排除 host2
  jsub -m "hostgroupA ~host2" my_job

  # 从所有节点中排除 hostgroupA 和 hostgroupB 中的节点
  jsub -m "~hostgroupA ~hostgroupB" my_job

  # 将 hostgroupA 加 hostB 作为一个节点集，从中排除 host2 和 hostgroupB 中的节点，并给 hostB 权重 +10
  jsub -m "hostgroupA ~host2 ~hostgroupB hostB+10" my_job
  ```

  **或关系多节点集合**：使用 `||` 分隔多个节点集合，作业运行在其中一个集合的节点上。调度器按指定顺序依次尝试，第一个能选出满足条件节点的集合被选中。

  ```bash
  # 先在 hostgroupA 或 host1 中选择，不满足则在 hostgroupB 或 host2 中选择
  jsub -m "hostgroupA host1 || hostgroupB host2" my_job
  ```

  或关系中每个节点集的指定方式与普通方式一致，可指定节点、节点组、优先级、排除节点。或关系中每个节点集可打标签，并通过共享资源动态调整优先级：

  ```bash
  jsub -m "hostset=(hostgroupA host1):tag1||(hostgroupB host2):tag2 pref=max[share_res]" my_job
  ```

  其中 `hostset` 为节点集合关键字，`tag1`/`tag2` 是给节点集打的标签，`pref` 指明依据共享资源 `share_res` 的值来动态判断优先级（`max` 或 `min`）。共享资源的值为以逗号分隔的 key=value 字符串（如 `tag1=10.2,tag2=5.7`）。
- **`-n`** `min_processors[,max_processors]`：指定处理器的最小和最大数量。调度器会为作业分配 `min_processors` 到 `max_processors` 之间的处理器数量（slot 数）。只指定 `-n N` 时，等同于 `-n N,N`，即固定请求 N 个处理器。

  ```bash
  # 固定请求 4 个处理器
  jsub -n 4 my_job

  # 请求 2 到 8 个处理器
  jsub -n 2,8 my_job
  ```
- **`-J`** `job_name`：指定提交的作业名称。
- **`-Jd`** `job_desc`：指定作业的描述信息。
- **`-i`** `in_file`：从指定文件获取作业的标准输入，可指定环境变量和路径替换变量。
- **`-o`** `out_file`：从指定文件获取作业的标准输出，可指定环境变量和路径替换变量。默认情况下作业结束时调度会添加总结信息，设置环境变量 `JH_JOB_NO_SUMMARY_OUT=Y` 可禁用此行为。
- **`-e`** `err_file`：从指定文件获取作业的标准错误输出，可指定环境变量和路径替换变量。

  **路径替换变量**（在 `-i`/`-o`/`-e`/`-cwd` 路径中使用）：

  | 变量 | 替换为 | 示例 |
  |------|--------|------|
  | `%J` | 作业的 JOBID | `-o output_%J.log` → `output_123.log` |
  | `%I` | 数组作业子作业的索引值 | `-o output_%J_%I.log` → `output_123_5.log` |

  **环境变量**：路径中可使用 `$HOME`、`$PWD` 等 shell 环境变量，以及提交时设置的自定义环境变量。

  ```bash
  # 使用 JOBID 作为输出文件名的一部分
  jsub -o job_%J_output.log my_job

  # 数组作业：每个子作业有独立的输入和输出文件
  jsub -J arr[1-10] -i input%J_%I -o output%J_%I.log my_job

  # 使用环境变量指定路径
  jsub -o $HOME/logs/job_%J.log my_job

  # 使用自定义环境变量
  export out=/data/output
  jsub -o $out/result_%J.log my_job
  ```
- **`-E`** `pre_exec_command[argument...]`：作业执行前需要运行 pre-exec 命令。pre-exec 在作业被派发到执行节点后、作业命令执行前运行。常用于环境初始化、目录创建、文件准备等场景。pre-exec 失败时作业会进入 EXIT 状态。
- **`-Ep`** `post_exec_command[argument...]`：作业执行结束后需要运行 post-exec 命令。post-exec 在作业命令执行完毕后运行，无论作业命令是否成功都会执行。常用于清理临时文件、收集结果、发送通知等场景。
- **`-cwd`** `current_working_directory`：指定作业的工作目录，可指定环境变量。默认情况下作业在提交节点的当前路径执行，使用 `-cwd` 可指定其他路径。如果 `-cwd` 指定的目录不存在，调度会自动创建；如果目录没有权限，作业会进入 PEND 状态。注意：需确保 `-cwd` 指定的每一层目录，执行用户都有读、写、执行权限。

  ```bash
  # 在指定目录下执行作业
  jsub -cwd /data/workspace my_job

  # 使用环境变量指定工作目录
  jsub -cwd $HOME/projects my_job
  ```
- **`-gpgpu`** `"num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize] [sm=num] [mig=gsize]"`：为作业指定GPU卡或MIG的类型、数量以及需要预留的GPU显存。各子参数含义如下：

  | 子参数 | 含义 | 示例 |
  |--------|------|------|
  | `num` | 请求的GPU卡数量（必须） | `2` 表示请求2张GPU卡 |
  | `type` | 指定GPU型号，多个型号用逗号分隔 | `type=NVIDIAA100-PCIE-80GB,NVIDIAA30` |
  | `vendor` | 指定GPU厂商 | `vendor=nvidia` |
  | `gmem` | 每张GPU需要预留的显存大小，单位MB | `gmem=2000` 表示每卡预留2000MB显存 |
  | `sm` | 指定GPU的SM（流处理器）数量 | `sm=10` |
  | `mig` | 指定请求的MIG（多实例GPU）规格大小 | `mig=7` 表示请求1g.7gb规格的MIG实例 |

  当未打开GPU_BIND开关时，表示选择满足指定GPU请求的节点执行作业，不执行GPU绑定，`jjobs -l`不打印GPU绑定信息；打开GPU_BIND开关后，作业执行GPU绑定，`jjobs -l`打印GPU绑定信息。

  ```bash
  # 请求1张GPU卡
  jsub -gpgpu 1 my_job

  # 请求2张NVIDIA A100 GPU卡，每卡预留4000MB显存
  jsub -gpgpu "2 type=NVIDIAA100-PCIE-80GB gmem=4000" my_job

  # 请求1张GPU卡，指定厂商和型号
  jsub -gpgpu "1 type=NVIDIAA30 vendor=nvidia gmem=2000" my_job

  # 请求MIG实例
  jsub -gpgpu "1 mig=7" my_job
  ```
- **`-nnode`** `"num nselect[core(num) mem(size) gpgpu(num [type=type1,type2...] [vendor=vendorname] [gmem=gmemsize])]"` V6.5+：为NUMA作业指定NUMA Node请求。通过指定NUMA节点数量和每个节点的资源需求，使作业在指定的NUMA拓扑下运行，优化内存访问局部性和性能。各参数含义如下：

  | 参数 | 含义 | 示例 |
  |------|------|------|
  | `num` | 请求的NUMA节点数量（必须） | `2` 表示请求2个NUMA节点 |
  | `nselect` | NUMA节点选择条件（关键字） | — |
  | `core(num)` | 每个NUMA节点分配的CPU核数 | `core(8)` 每节点8核 |
  | `mem(size)` | 每个NUMA节点预留的内存大小，单位MB | `mem(4096)` 每节点4096MB |
  | `gpgpu(...)` | 每个NUMA节点的GPU请求，参数与 `-gpgpu` 相同 | `gpgpu(1 type=NVIDIAA30 gmem=2000)` |

  ```bash
  # 请求2个NUMA节点，每节点8核、4096MB内存
  jsub -nnode "2 nselect[core(8) mem(4096)]" my_job

  # 请求2个NUMA节点，每节点4核、2048MB内存、1张GPU卡
  jsub -nnode "2 nselect[core(4) mem(2048) gpgpu(1)]" my_job

  # 请求2个NUMA节点，每节点指定GPU型号和显存
  jsub -nnode "2 nselect[core(8) mem(4096) gpgpu(1 type=NVIDIAA100-PCIE-80GB gmem=4000)]" my_job
  ```

  注意：`-nnode` 是 V6.5 新增选项，与 `-gpgpu` 可同时使用。使用 `-nnoden` 可取消已设置的NUMA Node请求。
- **`-r`**：指定作业可以重新运行。
- **`-rn`**：指定作业忽略重新运行队列上的配置。
- **`-M`** `mem_limit`：指定内存限制，以MB为单位。
- **`-W`** `run_limit`：指定作业的运行时间限制，以分钟为单位。
- **`-We`** `limit`：指定作业的预估运行时间，以分钟为单位。
- **`-hosts`** `"num [hselect=hselect_string]"`：指定 hosts number 和 hselect_string，用于 host 分配资源。`hselect_string` 由 `num@hostgroup` 或 `host` 组成，用逗号隔开。`num` 表示请求的节点数量。可用于精确控制作业在特定节点组上分配资源。

  ```bash
  # 请求 2 个节点，从 hostgroupA 中分配
  jsub -hosts "2 hselect=hostgroupA" my_job

  # 请求 3 个节点，分别从不同节点组分配
  jsub -hosts "3 hselect=2@groupA,1@groupB" my_job

  # 请求指定节点
  jsub -hosts "2 hselect=host1,host2" my_job
  ```
- **`-port`** `num`：指定作业需要分配的端口数量。分配的端口号可通过环境变量 `JH_JOB_PORTS` 获取，作业脚本中可直接使用。适用于需要网络端口的服务型作业。
- **`-mf`** `file`：为作业指定使用机器配置文件。
- **`-b`** `"YYYY-MM-DD HH:MM"` V6.4+：指定作业开始时间。作业在指定时间之前不会被调度执行。如果 `-b` 指定的时间早于当前时间，作业会立即进入正常调度流程。
- **`-t`** `"YYYY-MM-DD HH:MM"` V6.4+：指定作业终止时间。到达指定时间后，作业会被系统自动终止。如果 `-t` 指定的时间早于当前时间，则作业无法提交。`-b` 指定的开始时间不能晚于 `-t` 指定的终止时间。

  ```bash
  # 作业在指定时间后开始调度
  jsub -b "2025-05-18 14:40" sleep 10000

  # 作业在指定时间窗口内运行
  jsub -b "2025-05-18 14:40" -t "2025-05-18 18:00" sleep 10000

  # 等效输出
  # Job will be scheduled by Thu May 18 14:40:00 CST 2025
  # Job will be terminated by Thu May 18 18:00:00 CST 2025
  ```
- **`-aps`** `priority`：指定作业优先级。
- **`-f`** `[host:]local_file operator [remote_file]`：将本地文件或目录从I/O节点传输到作业执行节点的缓存目录。支持的操作符及其含义：

  | 操作符 | 含义 | 说明 |
  |--------|------|------|
  | `>` | 上传（提交节点 → 执行节点） | 将本地文件传输到执行节点的缓存目录 |
  | `<` | 下载（执行节点 → 提交节点） | 将执行节点缓存目录中的文件传回本地 |
  | `<>` | 双向同步（提交节点 ↔ 执行节点） | 本地和远程文件双向同步 |
  | `><` | 双向同步（执行节点 ↔ 提交节点） | 与 `<>` 相同，方向相反 |

  文件传输路径说明：
  - 本地路径：提交节点上的文件路径
  - 远程路径：执行节点上的缓存目录路径（由配置项 `STAGE_TOP_DIR_LINUX` 指定，默认为 `/tmp/stagein`）
  - 缓存目录格式：`$JH_STAGE_DIR/.${JOB_ID}.${JOB_INDEX}.stage/`
  - 可通过环境变量 `$JH_STAGE_DIR` 访问缓存目录

  ```bash
  # 将本地文件传输到执行节点
  jsub -f '/data/config.conf > config.conf' my_job

  # 将执行节点的文件传回本地
  jsub -f '/tmp/ < result.txt' my_job

  # 双向同步文件
  jsub -f '/data/input.dat <> input.dat' my_job

  # 传输多个文件
  jsub -f '/data/file1.txt > file1.txt' -f '/data/file2.txt > file2.txt' my_job

  # 传输整个目录
  jsub -f '/data/scripts/ > scripts/' my_job

  # 在作业中使用传输的文件
  jsub -f '/data/config.conf > config.conf' 'cat $JH_STAGE_DIR/config.conf'
  ```

  注意事项：
  - 文件传输在作业开始执行前完成
  - 传输失败会导致作业提交失败（错误码 10076）
  - 支持传输单个文件或整个目录
  - 路径中可使用环境变量
- **`-w`** `’status(job_ID | "job_name")...’` V6.4+：指定作业运行依赖的条件。作业将等待依赖条件满足后才开始调度执行。支持的状态和用法如下：

  **支持的依赖状态**：

  | 状态 | 含义 |
  |------|------|
  | `done(job)` | 依赖作业正常完成（退出码为0） |
  | `ended(job)` | 依赖作业已结束（无论是否正常） |
  | `exit(job)` | 依赖作业异常退出（退出码非0） |
  | `started(job)` | 依赖作业已开始运行 |
  | `post_done(job)` | 依赖作业的 post_exec 正常完成 |
  | `post_err(job)` | 依赖作业的 post_exec 异常退出 |

  **逻辑运算符**：

  | 运算符 | 含义 |
  |--------|------|
  | `&&` | 与（所有条件同时满足） |
  | `\|\|` | 或（满足其一即可） |
  | `!` | 非（取反） |

  **退出码过滤**：`exit(job, >=N)` 或 `exit(job, =N)` 可指定退出码条件。

  **默认状态**：只指定 `job_ID` 或 `"job_name"` 不带状态关键字时，默认为 `done` 状态依赖。

  **Shell 转义注意事项**：
  - Linux bash/zsh 中依赖条件用**单引号**括起，`!` 需要改写为 `\’`
  - Windows 系统中依赖条件用**双引号**括起
  - csh 中 `!` 需要改写为 `\\`

  ```bash
  # 作业 31 完成后再运行（默认 done 状态）
  jsub -w ‘31’ hostname

  # 作业 28 已启动 且 作业 26 异常退出（退出码>=130）且（作业 29 已结束 或 作业 30 正常完成）
  jsub -w ‘started(28) && exit(26,>=130) && (ended(29) || done(30))’ sleep 5

  # 依赖作业名称
  jsub -w ‘done("train_job")’ my_analysis

  # 依赖多个作业都完成
  jsub -w ‘done(10) && done(11) && done(12)’ my_job

  # 依赖任一作业完成即开始
  jsub -w ‘done(10) || done(11)’ my_job

  # 依赖作业异常退出
  jsub -w ‘exit(5)’ my_recovery_job

  # 依赖作业 post_exec 正常完成
  jsub -w ‘post_done(8)’ my_job
  ```


**示例**：

> 提交一个作业到指定节点host1，并指定作业运行队列为short。
> $jsub -m host1 -q short my_job

> 提交一个作业并指定运行节点，其中 host1 是最适合运行作业的节点，其次是 host2，最后是 host3，”+”增加的数值越高，其节点的优先级就越高。
> $jsub -m “host1+2 host2+1 host3” my_job

> 提交一个作业并指定特定的资源需求，如果 type==NTX64 节点内存大于50MB，作业将派发到 type==NTX64，如果 type==LINUX64 节点内存大于 100MB，作业将派发到 type==LINUX64，若这两个条件都不满足，作业将不被派发。
> $jsub -R “select[((type==NTX64&& mem > 50)||(type==LINUX64&& mem > 100))]” my_job

> 提交一个作业并指定资源预留数量mem为50MB，swap为100MB。
> $jsub -R “rusage[mem=50&&swap=100]” my_job

> 提交一个作业并指定运行作业最少需要 4 个 CPU 数，并且只能在一个节点上运行该作业。
> $jsub -n 4 -R “span[hosts=1]” my_job

> 提交一个作业并指定运行作业最少需要 4 个 CPU 数，并且每个节点只能为该作业提供 2 个 CPU。
> $jsub -n 4 -R “span[ptile=2]” my_job

> 提交一个作业并指定运行作业需要的 CPU 最大数和最小数。
> $jsub -n 2,4 my_job

> 提交一个禁止调度到 host1 上运行的作业。
> $jsub -m ~host1 my_job

> 请求 1 张 NVIDIA A100 GPU 卡，每卡预留 4000MB 显存。
> $jsub -gpgpu “1 type=NVIDIAA100-PCIE-80GB gmem=4000” my_job

> 请求 2 个节点，从 hostgroupA 中分配。
> $jsub -hosts “2 hselect=hostgroupA” my_job

> 使用输出文件路径变量，每个数组子作业有独立的输出文件。
> $jsub -J job[1-10] -o output_%J_%I.log my_job

> 将本地文件传输到执行节点缓存目录，作业中使用传输的文件。
> $jsub -f '/data/config.conf > config.conf' 'cat $JH_STAGE_DIR/config.conf'

> 依赖作业 10 和 11 都完成后才开始执行。
> $jsub -w 'done(10) && done(11)' my_job

> 提交一个暂时不执行的作业，后续手动释放。
> $jsub -H sleep 1000
> $jctrl start <jobid>

> 指定作业在指定时间窗口内运行。
> $jsub -b “2025-05-18 14:40” -t “2025-05-18 18:00” sleep 10000

> 使用 machine file 提交作业，指定节点资源分配。
> $jsub -mf /apps/mf01 sleep 1000

> 组合使用：选择 LINUX64 节点、预留资源、单节点运行、请求 GPU。
> $jsub -n 4 -gpgpu “1 type=NVIDIAA30 gmem=2000” -R “select[type==LINUX64] rusage[mem=2000/slot] span[hosts=1]” my_job

**脚本提交模式**：

通过脚本提交模式提交作业，方便用户管理作业提交参数和相关配置。将提交参数写入脚本，可以批量重复使用，避免每次指定大量参数。命令行选项会覆盖脚本中指定的选项。

脚本格式：第一行必须指定 shell 类型，后续使用 `#JSUB` 或 `#BSUB` 指定作业提交选项：

```bash
#!/bin/sh
#JSUB -J job_name
#JSUB -P project_name
#JSUB -q queue_name
#JSUB -n min_processors[,max_processors]
#JSUB -R res_req
#JSUB -m host_name
job_command arg1 arg2
```

脚本提交支持的 `#JSUB` 选项：`-x`、`-P`、`-R`、`-q`、`-m`、`-n`、`-J`、`-i`、`-o`、`-e`、`-E`、`-Ep`、`-cwd`、`-app`、`-hosts`、`-gpgpu`、`-r`、`-rn`

**注意事项**：

- 只支持 Linux shell 脚本，不支持在 Windows 平台上执行
- 提交命令只支持 `#JSUB` 或 `#BSUB`
- 脚本内容最大长度为 4096 字节，否则提交失败
- 脚本中以 `#JSUB` 或 `#BSUB` 开头的行均为作业命令行选项，非 `#` 开头的行为作业命令或环境变量设置
- 重复选项：第二次及以后指定的选项不生效（默认第一次生效）

**两种提交方式**：

方式一 — 直接传脚本文件（`jjobs` 查询 Command 字段为脚本文件名，需确保执行端存在该脚本）：

```bash
$ jsub my_job.sh
```

方式二 — 通过标准输入（`jjobs` 查询 Command 字段为脚本所有行的拼接）：

```bash
$ jsub < my_job.sh
```

**示例**：

脚本 `my_job.sh`：

```bash
#!/bin/sh
#JSUB -J job1
#JSUB -P project1
sleep 1000
```

等效于命令行：

```bash
$ jsub -J job1 -P project1 sleep 1000
```

命令行覆盖脚本选项：

```bash
$ jsub -J joba < /tmp/my_job.sh
Repeated argument <-J job1> in script, ignored
```

此时作业名称为 `joba`（命令行 `-J` 覆盖了脚本中的 `-J job1`）。

**内置环境变量**：

作业提交后，系统会在作业执行环境中自动设置以下环境变量，作业脚本可直接使用：

| 环境变量 | 说明 |
|---|---|
| `JH_JOBID` | 系统分配的作业号 |
| `JH_HOSTS` | 执行作业的节点及 slot 分配信息，格式为 `节点名1 slot数1 节点名2 slot数2 ...`，每个节点名后跟该节点分配的 slot 数。串行作业仅一个节点，如 `host1 1`；并行作业含多个节点，如 `host1 4 host2 4 host3 2` |
| `JH_QUEUE` | 作业所在队列的名称 |
| `JH_JOBNAME` | 作业名称 |
| `JH_SUB_HOST` | 作业的提交节点 |
| `JH_JOB_PROJECT` | 作业指定的项目名称 |
| `JH_JOB_STARTER` | 队列定义的 Job Starter 值（如已配置） |
| `JH_JOBPID` | 作业的进程号（仅在 JOB_CONTROLS 中可见） |
| `JH_SUB_CWD` | 作业提交时的工作路径 |
| `JH_ARRAY_JOBINDEX` V6.2+ | 数组作业子作业的 index |
| `JH_ARRAY_JOBID` V6.2+ | 数组作业的 ID，与 JH_JOBID 相同 |
| `JH_EXEC_USER` | 作业的执行用户 |
| `JH_GPU_MEM` | 作业分配的 GPU 内存大小 |
| `JH_CPU_RANK` V6.3+ | 作业分配的 CPU 绑定信息 |
| `JH_GPU_RANK` V6.3+ | 作业分配的 GPU 绑定信息 |
| `JH_JOB_PORTS` V6.3+ | 作业分配的端口资源 |
| `JH_JOB_OUTFILE` | 作业指定的输出文件路径 |

此外，用户可在提交作业前通过 `export` 设置以下环境变量来控制作业行为：

| 环境变量 | 说明 |
|---|---|
| `JH_JOB_KILL_INTERVAL` | 设置 jkill 发送信号的间隔时间（秒），默认为 10s |
| `JH_JOB_NO_SUMMARY_OUT` | 设为 `Y` 时，作业结束后不在输出文件中添加系统总结信息 |
| `JH_USE_JOB_FILE_TMPL` | 设为 `Y` 时，使用用户自定义的作业文件模板 |
| `JH_JJOBS_FORMAT` | 定义 `jjobs` 命令的默认输出格式 |
| `JHS_EXIT_ON_INITIAL_FAIL` | 设为 `y` 时，作业调度一次后仍为 PEND 状态则直接退出 |

**数组作业**：

使用 `-J job[start-end]` 提交作业数组，允许一系列作业共享相同的可执行文件和资源需求，作为一个单元控制、监控和管理。

- 索引必须使用方括号 `[]` 括起来，为正整数，最小 index 为 1，默认最大 index 为 5000（可通过 `params.conf` 中 `MAX_JOB_ARRAY_SIZE` 配置，最大支持 99999）
- `%I` 替换为当前作业的数组索引值，`%J` 替换为作业数组的 JOBID
- `jjobs` 默认合并显示 PEND 状态的数组作业，派发或控制操作后拆分显示；`jjobs -A` 显示数组作业统计信息
- 数组作业控制：使用 `jctrl stop/resume/kill/requeue`，可指定 `jobId[index]` 或 `jobId[start-end]`
- 不支持提交交互式数组作业

示例：

```bash
$ jsub -J job[1-20] -i input%J_%I -o output%J_%I.log myjob
$ jjobs -A                          # 查看数组作业统计
$ jjobs 5[1]                        # 查看指定子作业
$ jctrl stop 6[15-20]               # 挂起指定范围的子作业
```

**交互式作业**：

| 类型 | 选项 | 说明 |
|---|---|---|
| 普通交互式 | `-I` | 后端执行但实时呈现到提交端，支持人机交互 |
| X11 交互式 | `-IX` | 带 X11 转发，可将远端节点图形应用投射到提交端 |
| 服务模式 | `-Is` V6.1+ | 提交端关闭后作业保持后台运行，可使用 `jattach` 重新连接 |

交互式作业控制：支持 stop / resume / top / bot / start / kill。

**常用组合键**（交互式作业执行过程中）：

| 组合键 | 功能 | Linux 客户端 |
|---|---|---|
| Ctrl + C | 终止前台进程，发送 SIGINT | 可终止前台进程，对 bash 控制无效 |
| Ctrl + Z | 挂起前台进程，发送 SIGTSTP | 挂起前台进程，对 bash 控制无效 |
| Ctrl + D | EOF，相当于输入 exit | 对 bash 控制起作用，相当于输入 exit |
| Ctrl + q | 退出服务模式交互式 | 仅 Is 作业适用，退出当前交互并返回本地 shell |

**交互式作业使用限制**：

- 不支持 peek 和 requeue
- 不能使用 rerunable 调度和抢占调度
- 不能和 `jsub -i` 选项一起使用
- 当 `-I` 和 `-o` 一起使用时，不打印屏幕输出，输出写入 `-o` 文件
- 不支持提交交互式数组作业

**作业子进程控制**：

作业执行过程中会将所有子进程纳入调度管理，作业结束时自动清理全部子进程（包括 nohup 等后台进程），避免进程残留。可通过 `jjobs -l` 查看作业的子进程信息（PGIDS/PIDS）。

**作业自动重排队**：

当作业因临时错误（NFS 陈旧句柄、磁盘已满、网络连接问题等）以指定退出码退出时，系统可自动将作业重排到队列重新执行。

- 在 `queues.conf` 中设置 `REQUEUE_EXIT_VALUES=30 40 50`（多个退出码用空格分隔）
- 作业以指定退出码退出后，自动重排到队列，不会被派发到同一节点
- 受 `MAX_JOB_REQUEUE` 限制最大重排次数

---

## 26. jusergroup

**功能**：显示集群中定义的用户组相关信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。
- **`-l`**：以长格式形式显示用户组具体信息。若配置了公平共享调度策略，还能显示每个用户的分配份额。
- **`-r`**：递归展开用户组信息，在展开列表中只显示用户名，不包含子组名称，且重复的用户名只列出一次。 - group_name：仅显示指定用户组的信息。

---


## 27. jusers

**功能**：显示集群中用户和用户组作业相关信息，默认情况输出当前用户作业相关信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。


**示例**：

> 显示指定用户user1的作业信息。
> $jusers user1
> 显示集群所有用户和用户组作业的相关信息。
> $jusers all

---


## 28. jversion

**功能**：显示集群中景行资源管理与调度软件发行版本信息。


**选项**：

- **`-h`**：打印命令使用方法。
- **`-V`**：打印景行资源管理与调度软件发行版本信息。

---
