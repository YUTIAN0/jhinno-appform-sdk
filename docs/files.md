# 文件管理

FilesAPI 提供文件和目录的操作功能。

## 传输方式

所有文件操作命令支持两种传输方式：

- **`http`**（默认）— 通过 Appform API 网关，需要 API 认证
- **`sftp`** — 通过 SFTP 直连服务器，不经过 API 网关（需要安装 paramiko）

### 安装 SFTP 支持

```bash
pip install jhinno-appform-sdk[sftp]
```

### 指定传输方式

**CLI 方式：**

```bash
# 单个命令指定
appform files ls / --method sftp
appform files put ./file.txt /home/user/ --method sftp

# files 命令级别设置（影响所有子命令）
appform files --method sftp ls /
appform files --method sftp put ./file.txt /home/user/

# 通过配置文件持久化默认方式
appform config set --default-method sftp
```

**Python API 方式：**

```python
# 单个方法指定
client.files.list(path="/", transfer_method="sftp")
client.files.upload(file_path="./file.txt", remote_path="/home/user/", transfer_method="sftp")

# 所有支持 transfer_method 的方法：
# list, list_all, mkdir, copy, move, delete, upload, download,
# upload_directory, download_directory
```

### SFTP 认证配置

```bash
# SFTP 主机默认从 base_url 提取
appform config set --sftp-host mycluster.example.com
appform config set --sftp-port 22
appform config set --sftp-username admin
appform config set --sftp-key-file ~/.ssh/id_rsa

# 环境变量
export APPFORM_SFTP_HOST=mycluster.example.com
export APPFORM_SFTP_KEY_FILE=~/.ssh/id_rsa
```

---

## Python API

### 文件列表

```python
# 列出根目录
files = client.files.list(path="/")

# 列出指定目录（分页）
files = client.files.list(path="/home/user", page=1, page_size=100)

# 列出所有文件（自动翻页）
all_files = client.files.list_all(path="/home/user")
```

### 目录操作

```python
# 创建目录
client.files.mkdir(path="/home/user/new_folder", force=True)

# 获取根目录信息
root = client.files.get_root_dir()
```

### 文件操作

```python
# 重命名
client.files.rename(old_path="/home/user/old.txt", new_name="new.txt")

# 复制
client.files.copy(src_path="/home/user/file.txt", dest_dir="/home/user/backup/")

# 移动
client.files.move(src_path="/home/user/file.txt", dest_dir="/home/user/backup/")

# 删除
client.files.delete(path="/home/user/file.txt")
```

### 上传下载

```python
# 上传文件
client.files.upload(file_path="/local/path/file.txt", remote_path="/home/user/")

# 上传整个目录
results = client.files.upload_directory(local_dir="/local/folder", remote_dir="/home/user/remote_folder")

# 下载文件到本地
client.files.download(remote_path="/home/user/file.txt", local_path="/local/path/file.txt")

# 下载整个目录
results = client.files.download_directory(remote_dir="/home/user/folder", local_dir="/local/save_dir")
```

### 压缩解压

```python
# 压缩
client.files.compress(source_dir="/home/user/folder", target_path="/home/user/archive.tar.gz")

# 解压
client.files.uncompress(archive_path="/home/user/archive.tar.gz", dest_dir="/home/user/extracted/")
```

### 文件密级（6.5+）

```python
# 获取可用密级
levels = client.files.get_confidentiality_levels()

# 设置文件密级
client.files.set_confidentiality(path="/home/user/file.txt", level="secret")
```

## CLI 使用（Linux-like 命令）

文件命令参考 Linux 文件操作风格：第一个参数为源，第二个参数为目的。
远程路径以 `/` 开头，本地路径为相对路径或以 `./` 开头。

### ls — 列出远程目录

```bash
# 列出根目录
appform files ls /

# 列出指定目录
appform files ls /home/user

# 列出所有文件（自动翻页）
appform files ls --all /home/user

# 使用 SFTP（无需 API）
appform files ls / --method sftp
```

### mkdir — 创建远程目录

```bash
# 创建目录
appform files mkdir /home/user/new_folder

# 使用 SFTP
appform files mkdir /home/user/new_folder --method sftp
```

### cp — 复制远程文件

```bash
# 复制文件
appform files cp /home/user/file.txt /home/user/backup/

# 使用 SFTP
appform files cp /home/user/file.txt /home/user/backup/ --method sftp
```

### mv — 移动/重命名远程文件

```bash
# 重命名
appform files mv /home/user/old.txt /home/user/new.txt

# 移动到其他目录
appform files mv /home/user/file.txt /home/user/backup/

# 使用 SFTP
appform files mv /home/user/old.txt /home/user/new.txt --method sftp
```

### rm — 删除远程文件

```bash
# 删除文件
appform files rm /home/user/file.txt

# 使用 SFTP
appform files rm /home/user/file.txt --method sftp
```

### put — 上传文件到远程

```bash
# 上传文件（自动创建远程目录）
appform files put ./local_file.txt /home/user/

# 上传整个目录
appform files put ./local_folder /home/user/remote_folder

# 使用 SFTP 上传
appform files put ./local_file.txt /home/user/ --method sftp

# 使用默认远程路径（配置文件中设置 default_remote_path）
appform files put ./local_file.txt

# 强制覆盖远程已存在的文件（跳过确认提示）
appform files put ./local_file.txt /home/user/ -f

# 指定上传读取块大小（支持 256K、100M、1G 等格式）
appform files put ./large_file.tar.gz /home/user/ --chunk-size 500M
```

### get — 从远程下载文件

```bash
# 下载文件到当前目录
appform files get /home/user/file.txt

# 下载到指定本地目录
appform files get /home/user/file.txt /tmp/

# 使用 SFTP 下载
appform files get /home/user/file.txt --method sftp

# 下载整个目录
appform files get /home/user/folder ./local_backup/

# 指定下载读取块大小
appform files get /home/user/large_file.tar.gz ./ --chunk-size 500M
```

### cat — 查看远程文本文件内容

```bash
# 查看小文件全部内容（默认）
appform files cat /home/user/file.txt

# 查看前 10 行
appform files cat /home/user/file.txt --head 10

# 查看最后 20 行
appform files cat /home/user/file.txt --tail 20

# 查看行范围（--lines 参数）
appform files cat /home/user/file.txt --lines 10-20    # 第 10-20 行
appform files cat /home/user/file.txt --lines 100-     # 第 100 行到 EOF

# 使用 --start / --end 指定范围
appform files cat /home/user/file.txt --start 100 --end 200

# 输出所有内容（包括大文件）
appform files cat /home/user/large_log.log --all

# 指定编码
appform files cat /home/user/file.txt --encoding gbk

# 大文件默认输出最后 20 行
appform files cat /home/user/large_log.log
```

> **注意**：`cat` 命令仅支持 SFTP 方式。对于小文件（<1MB），默认输出全部内容；对于大文件，默认输出最后 20 行，使用 `--all` 可强制输出全部。

### tailf — 实时跟踪远程文件输出

```bash
# 实时跟踪文件输出（类似 tail -f）
appform files tailf /home/user/output.log

# 指定编码
appform files tailf /home/user/output.log --encoding gbk

# Ctrl+C 停止跟踪
```

> **注意**：`tailf` 命令仅支持 SFTP 方式，通过 SSH exec channel 执行远程 `tail -f`。需要安装 `jhinno-appform-sdk[sftp]`。

### compress / uncompress — 压缩解压

```bash
# 压缩远程目录
appform files compress /home/user/folder /home/user/archive.tar.gz

# 解压远程压缩包
appform files uncompress /home/user/archive.tar.gz /home/user/extracted/
```

### conf — 文件密级

```bash
# 获取可用密级
appform files conf --get-levels

# 设置文件密级
appform files conf --set /home/user/file.txt secret
```

## 默认远程路径

通过配置文件或环境变量设置默认远程路径，这样在使用 `put` 命令时可以省略远程目录参数：

```bash
# 环境变量
export APPFORM_DEFAULT_REMOTE_PATH=/home/user/

# 配置文件 (~/.appform/config.json)
appform config set --default-remote-path /home/user/
```
