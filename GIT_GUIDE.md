# Git 版本管理指南

## 仓库信息

- **项目**：邮件智能助手
- **仓库位置**：`D:\ai-mail-assistant`
- **当前版本**：v1.0.0
- **主分支**：master

## 常用Git命令

### 查看状态

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline --graph --all

# 查看标签
git tag -l

# 查看某个标签的详细信息
git show v1.0.0
```

### 日常提交

```bash
# 查看修改的文件
git status

# 添加所有修改
git add .

# 添加指定文件
git add src/ui/main_window.py

# 提交修改
git commit -m "fix: 修复XXX问题"

# 查看最近的提交
git log --oneline -5
```

### 分支管理

```bash
# 查看所有分支
git branch -a

# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout master

# 合并分支
git checkout master
git merge feature/new-feature

# 删除已合并的分支
git branch -d feature/new-feature
```

### 版本标签

```bash
# 创建带注释的标签
git tag -a v1.0.1 -m "版本说明"

# 创建轻量标签
git tag v1.0.1-beta

# 推送标签到远程（如果需要）
git push origin v1.0.1

# 删除本地标签
git tag -d v1.0.1-beta
```

### 回退操作

```bash
# 撤销工作区修改
git checkout -- <file>

# 撤销暂存区
git reset HEAD <file>

# 回退到上一个版本
git reset --hard HEAD^

# 回退到指定版本
git reset --hard <commit-id>

# 查看所有操作记录（用于恢复）
git reflog
```

## 版本号规范

使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**：重大版本更新（不兼容的API修改）
- **MINOR**：次版本更新（向后兼容的功能新增）
- **PATCH**：修订版本（向后兼容的问题修复）

示例：
- v1.0.0：首个正式版本
- v1.0.1：修复Bug #23
- v1.1.0：新增Phase 9功能

## 提交信息规范

使用约定式提交格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- `feat`：新功能
- `fix`：修复Bug
- `docs`：文档更新
- `style`：代码格式（不影响功能）
- `refactor`：重构（既不是新功能也不是修复Bug）
- `test`：测试相关
- `chore`：构建过程或辅助工具的变动

### 示例

```bash
# 新功能
git commit -m "feat(phase9): 添加移动端支持"

# Bug修复
git commit -m "fix(ui): 修复部门列表显示问题"

# 文档更新
git commit -m "docs: 更新安装说明"

# 多行提交信息
git commit -m "feat(phase9): 添加移动端支持" -m "- 实现响应式布局" -m "- 优化移动端交互"
```

## 工作流程

### 功能开发流程

1. 创建功能分支
```bash
git checkout -b feature/phase9-mobile
```

2. 开发并提交
```bash
git add .
git commit -m "feat(phase9): 实现移动端布局"
```

3. 合并到主分支
```bash
git checkout master
git merge feature/phase9-mobile
```

4. 创建版本标签
```bash
git tag -a v1.1.0 -m "Phase 9: 移动端支持"
```

5. 清理分支
```bash
git branch -d feature/phase9-mobile
```

### Bug修复流程

1. 创建修复分支
```bash
git checkout -b fix/bug-23
```

2. 修复并提交
```bash
git add .
git commit -m "fix: 修复Bug #23"
```

3. 合并到主分支
```bash
git checkout master
git merge fix/bug-23
```

4. 创建补丁版本
```bash
git tag -a v1.0.1 -m "修复Bug #23"
```

## 最佳实践

1. **频繁提交**：每完成一个小功能就提交
2. **清晰的提交信息**：让其他人能理解这次提交的目的
3. **使用分支**：不要在master分支上直接开发
4. **及时打标签**：每次发布都要打标签
5. **定期清理**：删除不需要的分支

## 查看统计

```bash
# 查看文件统计
git ls-files | wc -l

# 查看代码行数
git ls-files | xargs wc -l

# 查看贡献者
git shortlog -sn

# 查看某个作者的提交
git log --author="Developer" --oneline
```

## 备份建议

定期备份整个仓库：

```bash
# 创建裸仓库备份
git clone --bare D:\ai-mail-assistant D:\backups\ai-mail-assistant-backup.git

# 或直接复制整个目录
xcopy D:\ai-mail-assistant D:\backups\ai-mail-assistant-backup /E /I /H
```

---

**当前仓库状态**：
- 分支：master
- 最新提交：d8ca996
- 最新标签：v1.0.0
- 文件数量：107个
- 代码行数：26,283行
