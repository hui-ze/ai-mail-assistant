# Foxmail邮件智能助手 - 长期记忆

## 项目概览
- **项目名**: Foxmail邮件智能助手
- **技术栈**: PyQt5 + SQLite + AI (Ollama/云端API)
- **核心功能**: 邮件摘要、待办提取、日历同步、团队协作
- **当前阶段**: Phase 6+ (核心后端完成，UI层优化中)

## 开发历史

### 2026-03-28 UX架构师审查与改进
- 完成用户体验全面审查，生成详细改进报告
- **已完成改进**:
  - ✅ 实现完整主题系统（支持浅色/深色/跟随系统）- `src/ui/styles.py`
  - ✅ 添加加载状态反馈组件（LoadingOverlay）- `src/ui/components/loading_overlay.py`
  - ✅ 添加Toast轻量提示组件 - `src/ui/components/toast.py`
  - ✅ 增强可访问性支持（所有主要组件添加无障碍属性和快捷键）
  - ✅ 设置页面主题即时预览、Toast反馈替代弹窗
- **新增文件**:
  - `src/ui/styles.py` - 主题管理器和颜色系统
  - `src/ui/components/__init__.py` - UI组件包
  - `src/ui/components/loading_overlay.py` - 加载遮罩组件
  - `src/ui/components/toast.py` - Toast提示组件
- **修改文件**:
  - `main.py` - 集成主题管理器
  - `src/ui/main_window.py` - 添加加载遮罩、无障碍属性、快捷键
  - `src/ui/settings_dialog.py` - 主题即时预览、Toast反馈
- **报告位置**: `brain/f24b199e93534b1db4448bdcf0fe09f3/ux-review-report.md`

### 2026-03-24 Phase 6完成
- 用户画像功能实现（本地存储：姓名、部门、职位、工作描述）
- AI待办归属判断（7条快速规则 + AI辅助）
- 后端全流程测试通过（20/20测试）
- 新增文件: `src/core/todo_assigner.py`, `src/data/user_profile_repo.py`, `src/ui/user_profile_dialog.py`

## 项目结构
```
d:\ai-mail-assistant\
├── src/
│   ├── ui/                    # 用户界面 (PyQt5)
│   │   ├── components/        # 可复用UI组件 (新增)
│   │   │   ├── loading_overlay.py
│   │   │   └── toast.py
│   │   ├── styles.py          # 主题系统 (新增)
│   │   ├── main_window.py
│   │   └── settings_dialog.py
│   ├── core/                  # 核心业务逻辑
│   ├── data/                  # 数据访问层
│   └── utils/                 # 工具函数
├── tests/                     # 测试文件
├── docs/                      # 文档
└── dist/                      # 打包输出
```

## 快捷键
- `Ctrl+A` - AI分析当前邮件
- `Ctrl+T` - 提取待办事项
- `Ctrl+L` - 同步待办到日历
- `Ctrl+,` - 打开设置
- `Ctrl+F` - 搜索邮件
- `Ctrl+N` - 新建邮件
- `F5` - 刷新邮件列表
- `Ctrl+Shift+A` - 添加邮箱账号

## 待办事项
1. ~~实现主题系统~~ ✅
2. ~~添加加载状态反馈组件~~ ✅
3. ~~增强可访问性支持~~ ✅
4. ~~完善设置页面的即时反馈~~ ✅
