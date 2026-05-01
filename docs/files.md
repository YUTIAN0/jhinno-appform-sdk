# 文件管理

FilesAPI 提供文件和目录的操作功能。

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
```

### mkdir — 创建远程目录

```bash
# 创建目录
appform files mkdir /home/user/new_folder
```

### cp — 复制远程文件

```bash
# 复制文件
appform files cp /home/user/file.txt /home/user/backup/
```

### mv — 移动/重命名远程文件

```bash
# 重命名
appform files mv /home/user/old.txt /home/user/new.txt

# 移动到其他目录
appform files mv /home/user/file.txt /home/user/backup/
```

### rm — 删除远程文件

```bash
# 删除文件
appform files rm /home/user/file.txt
```

### put — 上传文件到远程

```bash
# 上传文件（自动创建远程目录）
appform files put ./local_file.txt /home/user/

# 上传整个目录
appform files put ./local_folder /home/user/remote_folder

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

# 下载整个目录
appform files get /home/user/folder ./local_backup/

# 指定下载读取块大小
appform files get /home/user/large_file.tar.gz ./ --chunk-size 500M
```

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
