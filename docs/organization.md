# 组织管理

OrganizationAPI 提供部门和用户的管理功能。

## 部门管理

```python
# 获取部门树
departments = client.organization.get_departments()

# 创建部门
client.organization.create_department(
    dep_name="engineering",
    dep_chname="工程部",
    parent_dep="company",
    description="Engineering department",
)

# 修改部门
client.organization.update_department(
    dep_name="engineering",
    dep_chname="工程技术部",
)

# 删除部门
client.organization.delete_department("engineering")
```

## 用户管理

```python
# 获取用户列表
users = client.organization.get_users(page=1, page_size=20)

# 按部门过滤
users = client.organization.get_users(dep="engineering")

# 按用户名过滤
users = client.organization.get_users(username="your_username")

# 创建用户
client.organization.create_user(
    username="newuser",
    chusername="新用户",
    password="your_password",
    dep="engineering",
    phone="13800138000",
    mail="newuser@example.com",
)

# 修改用户
client.organization.update_user(
    username="newuser",
    chusername="新用户名",
    phone="13900139000",
)

# 重置密码
client.organization.reset_password(
    username="newuser",
    new_password="your_new_password",
)

# 删除用户
client.organization.delete_user("newuser")
```

## CLI 使用

### 部门管理

```bash
# 列出部门（树形）
appform departments list

# 创建部门（--parent 为必选参数）
appform departments create --name engineering --display-name 工程部 --parent company
appform departments create --name dev --display-name 开发部 --parent engineering --description 开发团队

# 更新部门（--name 必选，其余可选）
appform departments update --name engineering --display-name 工程技术部
appform departments update --name dev --parent company

# 删除部门
appform departments delete --name engineering
```

### 用户管理

```bash
# 列出用户
appform users list

# 分页列出
appform users list --page 1 --page-size 50

# 按部门过滤
appform users list --dep engineering

# 按关键字过滤（支持账号、中文名、电话、邮箱、部门名）
appform users list --filter-username admin

# 创建用户
appform users create --user newuser --display-name 新用户 --new-password your_password --dep engineering
appform users create --user newuser --display-name 新用户 --new-password your_password --dep engineering --mail newuser@example.com --phone 13800138000

# 修改用户（--user 必选，其余可选）
appform users update --user newuser --display-name 新用户名
appform users update --user newuser --display-name 新用户名 --dep company --mail newuser@example.com

# 删除用户
appform users delete --user newuser

# 重置密码
appform users reset-password --user newuser --new-password your_new_password
```
