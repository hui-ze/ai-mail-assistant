# 邮件智能助手

基于AI技术的邮件管理工具，帮助用户高效管理邮箱、提取待办事项、生成邮件摘要。

## 功能特性

### 核心功能 (Phase 0-5)
- ✅ 多邮箱管理：支持QQ邮箱、163邮箱、Gmail、Outlook
- ✅ AI智能摘要：自动生成邮件摘要
- ✅ 待办提取：智能识别邮件中的待办事项
- ✅ 日历同步：将待办事项同步到本地日历
- ✅ 用户画像：个性化AI分析

### 协作功能 (Phase 7-8)
- ✅ 部门管理：创建和管理部门团队
- ✅ 成员管理：添加团队成员信息
- ✅ 待办同步：团队成员间待办共享
- ✅ 待办分配：分配任务给团队成员
- ✅ 智能提醒：自动提醒待办事项

### UI优化
- ✅ 窗口自适应屏幕
- ✅ 三栏可调整宽度
- ✅ 深色/浅色主题切换

## 技术栈

- **UI框架**：PyQt5
- **数据库**：SQLite
- **AI服务**：
  - 本地：Ollama (qwen3:8b)
  - 云端：DeepSeek、通义千问、文心一言
- **邮件协议**：IMAP/SMTP
- **日历集成**：Windows Calendar (COM)

## 项目结构

```
ai-mail-assistant/
├── main.py                 # 主程序入口
├── src/
│   ├── core/               # 核心业务逻辑
│   │   ├── ai_service.py   # AI服务
│   │   ├── ai_bridge.py    # AI桥接层
│   │   ├── calendar_sync.py# 日历同步
│   │   └── todo_assigner.py# 待办归属判断
│   ├── data/               # 数据访问层
│   │   ├── database.py     # 数据库管理
│   │   ├── department_repo.py
│   │   └── team_member_repo.py
│   ├── ui/                 # UI界面
│   │   ├── main_window.py  # 主窗口
│   │   ├── settings_dialog.py
│   │   ├── welcome_wizard.py
│   │   └── ai_manager.py   # AI配置界面
│   └── utils/              # 工具类
├── assets/                 # 资源文件
│   └── icons/              # 应用图标
├── tests/                  # 测试文件
├── docs/                   # 文档
├── requirements.txt        # Python依赖
└── foxmail_assistant.spec  # PyInstaller配置
```

## 安装使用

### 开发环境

1. 克隆项目
```bash
git clone <repository-url>
cd ai-mail-assistant
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python main.py
```

### 打包发布

```bash
# 安装PyInstaller
pip install pyinstaller

# 打包应用
python -m PyInstaller foxmail_assistant.spec --clean --noconfirm
```

输出位置：`dist/邮件智能助手/`

## 配置说明

### 邮箱配置
需要获取邮箱授权码（非登录密码）：
- **QQ邮箱**：设置 → 账户 → POP3/IMAP/SMTP服务
- **163邮箱**：设置 → POP3/SMTP/IMAP
- **Gmail**：账户设置 → 安全性 → 应用专用密码

### AI服务配置

**本地AI（Ollama）**：
```bash
# 安装Ollama
# 访问 https://ollama.ai

# 下载模型
ollama pull qwen3:8b
```

**云端API**：
- DeepSeek: https://platform.deepseek.com
- 通义千问: https://dashscope.aliyuncs.com
- 文心一言: https://console.bce.baidu.com/qianfan

## 数据存储

- 数据库：`~/.mail-assistant/data.db`
- 日志文件：`~/.mail-assistant/logs/`
- 配置文件：`~/.mail-assistant/config/`

## 开发历程

- **Phase 0-5**：基础功能开发（邮件管理、AI摘要、待办提取）
- **Phase 6**：用户画像功能
- **Phase 7**：部门协作功能
- **Phase 8**：待办分配与提醒
- **v1.0.0**：正式发布（2026-03-29）

## 版本历史

### v1.0.0 (2026-03-29)
- ✅ 完成所有核心功能
- ✅ 修复Bug #20-22
- ✅ UI优化完成
- ✅ 打包发布

## 许可证

本项目仅供个人学习和研究使用。

## 贡献指南

欢迎提交Issue和Pull Request。

## 联系方式

如有问题或建议，请提交Issue。
