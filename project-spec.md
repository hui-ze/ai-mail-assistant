# Foxmail 邮件智能摘要和待办提取工具 - 项目规范文档

> 版本：1.0  
> 日期：2026-03-23  
> 状态：草稿（待审核）

---

## 1. 项目概述

### 1.1 项目目标

开发一款 Windows 桌面应用程序，通过 IMAP 协议读取 Foxmail（及支持 IMAP 的主流邮箱）邮件，集成 AI 能力自动生成邮件摘要并提取待办事项，帮助用户高效管理邮件和处理任务。

### 1.2 核心价值

- **节省时间**：AI 自动摘要，30秒了解一封邮件的核心内容
- **不漏待办**：自动从邮件中提取任务和截止日期
- **隐私优先**：支持本地模型运行，数据不离开本机
- **零门槛**：类似 Foxmail 的使用体验，无需复杂配置

### 1.3 目标用户

- 日常邮件处理量大的职场人士
- 需要从邮件中追踪任务和项目的管理者
- 对 AI 工具感兴趣、愿意尝试新方式提升效率的用户

---

## 2. 技术选型

### 2.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **桌面框架** | PyQt5 | Python 原生 GUI 开发，生态成熟 |
| **邮件协议** | Python imaplib / IMAPClient | 标准 IMAP 协议支持 |
| **本地 AI** | Ollama + Qwen2.5 | 完全离线的本地模型推理 |
| **云端 AI** | 文心一言 / 通义千问 / DeepSeek API | 高质量云端大模型（付费） |
| **数据存储** | SQLite | 本地轻量数据库，保护隐私 |
| **打包分发** | PyInstaller | 一键打包为 Windows EXE |
| **日历同步** | win32com / caldav | Windows 系统日历集成 |

### 2.2 为什么选择 PyQt5

1. **开发效率高**：你已有 Python 基础代码，可直接复用
2. **AI 集成最简**：OpenAI、百度、阿里等 SDK 均为 Python 原生
3. **IMAP 库成熟**：`imapclient`、`email` 模块稳定可靠
4. **打包便捷**：PyInstaller 一条命令即可打包 EXE
5. **周期短**：预计 2-3 周完成 MVP

### 2.3 项目结构

```
D:\ai-mail-assistant\
├── src/
│   ├── main.py                 # 应用入口
│   ├── ui/
│   │   ├── main_window.py      # 主窗口（三栏布局）
│   │   ├── email_list_panel.py # 邮件列表面板
│   │   ├── summary_panel.py   # 摘要详情面板
│   │   ├── todo_panel.py      # 待办事项面板
│   │   └── settings_dialog.py # 设置对话框
│   ├── core/
│   │   ├── imap_client.py      # IMAP 客户端封装
│   │   ├── email_parser.py     # 邮件解析器
│   │   ├── ai_bridge.py       # AI 统一接口
│   │   ├── ollama_processor.py # 本地 Ollama 处理
│   │   ├── cloud_ai_processor.py # 云端 API 处理
│   │   ├── prompt_engine.py   # 提示词引擎
│   │   └── calendar_sync.py   # 日历同步
│   ├── data/
│   │   ├── database.py         # SQLite 数据库操作
│   │   ├── email_repo.py       # 邮件仓储
│   │   ├── summary_repo.py    # 摘要仓储
│   │   └── todo_repo.py       # 待办仓储
│   └── utils/
│       ├── config_manager.py   # 配置管理
│       └── logger.py           # 日志工具
├── assets/
│   └── icons/                  # 应用图标
├── tests/
│   ├── test_imap_client.py
│   ├── test_ai_processor.py
│   └── test_todo_repo.py
├── docs/
│   └── user-guide.md           # 用户使用手册
├── requirements.txt
├── config.py                    # 现有配置文件（待整合）
├── README.md
└── project-spec.md            # 本文档
```

---

## 3. 功能规范

### 3.1 核心功能列表

#### F1：邮箱配置与管理
- 用户首次使用时引导配置邮箱
- 支持 QQ 邮箱、网易邮箱、企业邮箱、Gmail 等主流 IMAP 邮箱
- 使用**授权码**而非密码，安全可靠
- 支持多邮箱账号切换
- 配置信息加密存储在本地 SQLite

#### F2：邮件获取与浏览
- 通过 IMAP 协议连接邮件服务器
- **指定时间段获取**：用户设置起始和结束时间，获取该范围内的所有邮件
- **指定文件夹获取**：支持收件箱、自定义文件夹
- 邮件列表展示：发件人、主题、摘要预览、时间
- 支持按发件人、主题搜索邮件
- 显示邮件已读/未读状态

#### F3：邮件处理模式（混合模式）
- **后台自动检查**：应用每 15 分钟（可配置）自动检查新邮件
- **用户确认后处理**：新邮件到达后，显示通知，用户点击"生成摘要"后才调用 AI
- **手动触发**：用户可随时点击"刷新"手动检查并处理邮件

#### F4：AI 摘要生成
- 将邮件正文、主题、发件人信息发送给 AI
- **提示词设计**：
  ```
  请为以下邮件生成一段简洁的中文摘要（50-100字），
  并提取其中需要收件人完成的待办事项（用列表形式）。
  
  邮件信息：
  - 主题：{subject}
  - 发件人：{sender}
  - 时间：{date}
  - 正文：{body}
  
  请按以下格式输出：
  【摘要】
  {摘要内容}
  
  【待办事项】
  1. {待办1}
  2. {待办2}
  ...
  ```
- 支持中英文邮件处理

#### F5：待办事项管理
- 从邮件 AI 分析结果中提取待办事项
- 在**待办面板**中集中展示所有待办
- 支持的操作：
  - 添加/编辑/删除待办
  - 标记完成（打勾）
  - 设置截止日期
  - 设置优先级（高/中/低）
- **日历同步**：可将待办同步到 Windows 系统日历

#### F6：AI 模型支持

| 版本 | 模型 | 说明 |
|------|------|------|
| **免费版** | Ollama + Qwen2.5-1.5B/3B | 完全离线，零成本，隐私保护最佳 |
| **付费版** | 文心一言 / 通义千问 / DeepSeek | 更高质量的摘要和待办提取 |

- 用户可在设置中切换 AI 模型
- 自动检测 Ollama 是否已安装并运行

#### F7：商业模式
- **免费版限制**：
  - 每天最多处理 20 封邮件
  - 仅支持本地 Ollama 模型
- **付费版（计划）**：
  - 无邮件处理上限
  - 支持云端大模型
  - 优先使用最新模型

---

## 4. 用户界面规范

### 4.1 UI 设计风格

**风格名称**：友好亲和（Friendly & Approachable）

| 特征 | 说明 |
|------|------|
| **主色调** | 柔和紫色渐变（#667eea → #764ba2） |
| **边角** | 圆角设计（border-radius: 12-16px） |
| **卡片** | 白色卡片 + 轻微阴影 |
| **字体** | 微软雅黑 / Segoe UI |
| **间距** | 宽松留白，视觉舒适 |
| **交互** | 柔和的悬停效果，渐进式引导 |

### 4.2 三栏布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  Foxmail 邮件智能助手                              [设置] [帮助] │
├──────────────┬─────────────────────────┬────────────────────────┤
│              │                         │                        │
│  📥 收件箱    │   [选中邮件的摘要详情]     │   ✅ 我的待办           │
│  [搜索] [刷新] │                         │   [全部] [未完成] [已完成]│
│              │   发件人：张三             │                        │
│  ○ 邮件1      │   时间：2026-03-23      │   ┌────────────────┐  │
│    项目进度汇报│                          │   │📅 提交测试报告   │  │
│    张三 10:30 │   【AI摘要】             │   │截止：周一 14:00  │  │
│              │   本周项目整体进展顺利...  │   │[同步日历]        │  │
│  ● 邮件2      │                          │   └────────────────┘  │
│    会议邀请   │   【待办事项】            │                        │
│    系统 09:15 │   ☐ 完成核心模块代码     │   ┌────────────────┐  │
│              │   ☑ 准备会议材料         │   │✓ 代码Review完成  │  │
│  ○ 邮件3      │                          │   └────────────────┘  │
│    账单通知   │                          │                        │
│    支付宝 昨天 │   [重新摘要]            │   ────────────────── │
│              │                         │   🆓 免费版 · 本地模型  │
├──────────────┴─────────────────────────┴───升级到付费版 →────────┤
│  状态：已连接 · 15分钟后检查新邮件                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 界面组件说明

#### 左侧面板：邮件列表
- 顶部：文件夹选择（收件箱/自定义文件夹）
- 功能按钮：搜索框、刷新按钮
- 邮件项：发件人、主题、摘要预览、时间戳、待办数量标签、AI摘要标签
- 未读邮件高亮显示

#### 中间面板：摘要详情
- 邮件头信息（发件人、收件人、时间）
- AI 生成的摘要（紫色背景卡片）
- 待办事项列表（可勾选完成）
- 操作按钮：重新摘要、标记已读、回复邮件

#### 右侧面板：待办管理
- 筛选标签：全部 / 未完成 / 已完成
- 待办卡片：任务内容、来源邮件、截止日期
- 一键同步到日历按钮
- 底部：版本信息和升级引导

#### 设置对话框
- 邮箱账号管理（添加/删除/切换）
- AI 模型选择（免费版/付费版切换）
- 同步频率设置
- 本地模型路径配置（Ollama）
- 云端 API Key 配置

---

## 5. 数据规范

### 5.1 数据库设计（SQLite）

#### 表：emails（邮件表）
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR(255) UNIQUE NOT NULL,     -- 邮件唯一标识（服务器UID）
    account_id INTEGER NOT NULL,          -- 所属邮箱账号
    subject TEXT,                          -- 邮件主题
    sender TEXT,                           -- 发件人
    sender_email TEXT,                     -- 发件人邮箱
    recipients TEXT,                        -- 收件人
    date DATETIME,                         -- 邮件日期
    body_text TEXT,                       -- 纯文本正文
    body_html TEXT,                        -- HTML 正文
    folder VARCHAR(100),                  -- 所属文件夹
    is_read BOOLEAN DEFAULT 0,            -- 是否已读
    processed BOOLEAN DEFAULT 0,           -- 是否已 AI 处理
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 表：summaries（摘要表）
```sql
CREATE TABLE summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,            -- 关联邮件 ID
    summary_text TEXT,                     -- AI 生成的摘要
    todos_json TEXT,                      -- 待办事项（JSON 格式）
    model_used VARCHAR(100),              -- 使用的 AI 模型
    tokens_used INTEGER,                   -- 消耗的 Token 数
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);
```

#### 表：todos（待办表）
```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER,                    -- 关联摘要 ID（可为空，手动添加）
    email_id INTEGER,                      -- 来源邮件 ID（可为空）
    content TEXT NOT NULL,                 -- 待办内容
    completed BOOLEAN DEFAULT 0,           -- 是否完成
    priority VARCHAR(20) DEFAULT '中',      -- 优先级：高/中/低
    due_date DATETIME,                     -- 截止日期
    calendar_event_id VARCHAR(255),        -- 日历事件 ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 表：accounts（邮箱账号表）
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_address VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    imap_server VARCHAR(255),
    imap_port INTEGER DEFAULT 993,
    smtp_server VARCHAR(255),
    smtp_port INTEGER DEFAULT 465,
    auth_code_encrypted TEXT,              -- 加密存储的授权码
    default_folder VARCHAR(100) DEFAULT 'INBOX',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 表：settings（设置表）
```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    ai_provider VARCHAR(50) DEFAULT 'ollama',  -- ollama / wenxin / qianwen / deepseek
    ollama_url VARCHAR(255) DEFAULT 'http://localhost:11434',
    ollama_model VARCHAR(100) DEFAULT 'qwen2.5:1.5b',
    cloud_api_key_encrypted TEXT,
    cloud_api_endpoint TEXT,
    sync_interval_minutes INTEGER DEFAULT 15,
    auto_process BOOLEAN DEFAULT 0,
    daily_limit_free INTEGER DEFAULT 20,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 本地存储路径

```
%APPDATA%\ai-mail-assistant\
├── data\
│   └── app.db                  # SQLite 数据库文件
├── logs\
│   └── app.log                 # 应用日志
├── config\
│   └── settings.json           # 配置文件（可选）
└── cache\
    └── ai_cache.json           # AI 结果缓存（避免重复处理）
```

---

## 6. API 接口规范

### 6.1 AI 处理器接口（统一抽象）

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class EmailData:
    """邮件数据结构"""
    subject: str
    sender: str
    sender_email: str
    date: datetime
    body_text: str
    body_html: Optional[str] = None

@dataclass
class SummaryResult:
    """摘要结果数据结构"""
    summary: str
    todos: List[str]
    model_used: str
    tokens_used: int

class AIProcessor(ABC):
    """AI 处理器抽象接口"""
    
    @abstractmethod
    def generate_summary(self, email: EmailData) -> SummaryResult:
        """生成邮件摘要和提取待办"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查 AI 服务是否可用"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        pass
```

### 6.2 IMAP 客户端接口

```python
class IMAPClient:
    """IMAP 客户端封装"""
    
    def connect(self, server: str, port: int, email: str, auth_code: str) -> bool:
        """建立 IMAP 连接"""
        pass
    
    def disconnect(self) -> None:
        """断开连接"""
        pass
    
    def list_folders(self) -> List[str]:
        """列出所有文件夹"""
        pass
    
    def fetch_emails(
        self, 
        folder: str, 
        since_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[EmailData]:
        """获取邮件"""
        pass
    
    def fetch_email_by_uid(self, uid: str) -> Optional[EmailData]:
        """根据 UID 获取单封邮件"""
        pass
```

---

## 7. 错误处理规范

### 7.1 错误分类与处理

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| **网络错误** | IMAP 连接失败、网络超时 | 显示友好提示，3秒后自动重试，最多3次 |
| **认证错误** | 授权码错误、账号被封 | 提示检查授权码，跳转到设置页面 |
| **AI 服务错误** | Ollama 未启动、API 调用失败 | 切换到备用模型，显示具体错误信息 |
| **数据错误** | 数据库读写失败、邮件解析失败 | 记录日志，提示用户重启应用 |
| **用户取消** | 用户主动取消操作 | 安静退出，不显示错误 |

### 7.2 用户提示规范

- **成功操作**：绿色提示条，3秒后自动消失
- **一般错误**：橙色提示条，可关闭
- **严重错误**：红色弹窗，显示详细信息和解决方案
- **加载中**：显示进度条和预估时间

---

## 8. 安全与隐私规范

### 8.1 数据安全

1. **授权码加密**：使用 Python `cryptography` 库的 Fernet 对称加密
2. **API Key 加密**：同授权码加密方式
3. **本地存储**：所有数据存储在用户本地，不上传服务器
4. **敏感信息**：仅存储必要的邮箱配置，不存储邮件内容原文

### 8.2 隐私保护

1. **本地模型优先**：免费版使用 Ollama 本地模型，邮件不离开本机
2. **最小数据原则**：发送给 AI 的数据仅限邮件必要字段
3. **缓存管理**：定期清理 AI 缓存，用户可手动清除

---

## 9. 性能规范

### 9.1 性能指标

| 指标 | 要求 |
|------|------|
| **冷启动时间** | < 3 秒 |
| **邮件列表加载（100封）** | < 2 秒 |
| **AI 摘要生成（本地模型）** | < 10 秒/封 |
| **AI 摘要生成（云端 API）** | < 5 秒/封 |
| **内存占用（空闲）** | < 150 MB |
| **EXE 打包体积** | < 100 MB |

### 9.2 优化策略

1. **增量同步**：仅拉取新邮件，不重复下载已处理的邮件
2. **缓存机制**：已生成摘要的邮件不重复调用 AI
3. **分页加载**：邮件列表分页加载，每页 50 封
4. **后台线程**：IMAP 和 AI 调用在后台线程执行，不阻塞 UI

---

## 10. 测试规范

### 10.1 单元测试

| 模块 | 测试内容 |
|------|---------|
| imap_client | 连接、断开、获取邮件、错误处理 |
| email_parser | 纯文本提取、HTML 解析、编码处理 |
| ai_processor | Ollama 调用、云端 API 调用、错误处理 |
| todo_repo | CRUD 操作、状态转换 |

### 10.2 集成测试

1. **完整流程测试**：配置邮箱 → 获取邮件 → AI 处理 → 查看摘要 → 管理待办
2. **多邮箱测试**：同时配置 QQ 邮箱和网易邮箱
3. **离线模式测试**：无网络环境下使用本地模型

### 10.3 用户体验测试

1. 新用户首次使用的引导流程
2. 错误场景下的用户提示是否友好
3. 三栏布局在不同分辨率下的显示效果

---

## 11. 开发计划（里程碑）

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| **Phase 0** | 项目结构搭建、依赖安装 | 1 天 |
| **Phase 1** | IMAP 客户端、邮件解析 | 3 天 |
| **Phase 2** | PyQt5 UI 开发（三栏布局） | 5 天 |
| **Phase 3** | Ollama 本地 AI 集成 | 3 天 |
| **Phase 4** | 摘要生成、待办提取功能 | 3 天 |
| **Phase 5** | 设置页面、日历同步 | 2 天 |
| **Phase 6** | 云端 AI API 集成（付费功能） | 3 天 |
| **Phase 7** | 打包测试、Bug 修复 | 2 天 |
| **Phase 8** | 文档编写、发布准备 | 1 天 |
| **总计** | **MVP 完成** | **23 天** |

---

## 12. 附录

### 12.1 术语表

| 术语 | 说明 |
|------|------|
| IMAP | Internet Message Access Protocol，邮件访问协议 |
| 授权码 | 邮箱提供的第三方登录专用密码，非账户密码 |
| Ollama | 本地运行大语言模型的工具 |
| Token | AI 模型的计费单位 |
| 摘要 | Email Summary，邮件的简短概括 |

### 12.2 参考资料

- [PyQt5 官方文档](https://doc.qt.io/qtforpython/)
- [IMAPClient 使用指南](https://imapclient.readthedocs.io/)
- [Ollama 官方文档](https://github.com/ollama/ollama)
- [百度文心一言 API](https://cloud.baidu.com/doc/WENXINWORKSHOP/)
- [阿里通义千问 API](https://help.aliyun.com/document_detail/)

### 12.3 联系方式

如有问题或建议，请通过以下方式联系：
- 项目 GitHub Issues：（待创建）
- 邮箱支持：（待设置）

---

## 13. 变更记录

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-03-23 | 初始版本，完成需求分析和设计规范 | hui-ze |
