# Foxmail 邮件智能助手 - Phase 6 设计文档

**用户画像与待办归属优化**

---

## 📌 概述

### 目标
1. 让用户描述自己的部门、角色，提升 AI 待办归属判断准确性
2. 为未来的部门协作功能（Phase 7）奠定基础

### 背景
当前系统提取待办时，无法判断待办事项是否真正属于当前用户。用户可能在邮件中被抄送，但待办事项属于其他收件人。

### 解决方案
- 引入用户画像（本地存储）
- AI 结合用户画像 + 邮件上下文综合判断待办归属
- 提供可选的首次引导流程

---

## 📊 数据模型

### 新增表：`user_profile`

```sql
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- 单用户，只有一条记录
    name VARCHAR(100),                       -- 用户姓名
    department VARCHAR(100),                 -- 部门名称
    role VARCHAR(100),                       -- 角色职位
    work_description TEXT,                   -- 工作描述（关键词）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化空记录
INSERT INTO user_profile (id) VALUES (1);
```

### 修改表：`todos`

```sql
-- 新增字段
ALTER TABLE todos ADD COLUMN assignee VARCHAR(100);   -- 待办归属人
ALTER TABLE todos ADD COLUMN assign_type VARCHAR(20); -- 归属类型
ALTER TABLE todos ADD COLUMN confidence REAL;         -- AI 置信度
ALTER TABLE todos ADD COLUMN assign_reason TEXT;      -- 判断理由

-- assign_type 取值：
-- 'self'   : 属于当前用户
-- 'other'  : 属于其他人（assignee 字段记录归属人）
-- 'team'   : 团队共同任务
-- 'unknown': 无法判断
```

---

## 🤖 AI 待办归属判断

### 判断流程

```
邮件到达
    ↓
提取待办事项（现有功能）
    ↓
【新增】归属判断模块
    ↓
┌─────────────────────────────────────┐
│ 1. 检查收件人列表                     │
│    - 用户邮箱是否在 To 字段           │
│    - 用户邮箱是否在 Cc 字段           │
│                                      │
│ 2. 分析邮件内容                       │
│    - 是否包含用户姓名                 │
│    - 是否包含用户职位称呼             │
│                                      │
│ 3. 结合用户画像                       │
│    - 待办内容是否与工作职责相关       │
│    - 部门信息是否匹配                 │
│                                      │
│ 4. AI 综合判断                        │
│    - 归属类型 + 置信度                │
└─────────────────────────────────────┘
    ↓
存储待办 + 归属信息
```

### AI Prompt 模板

```python
PROMPT_TODO_ASSIGNMENT = """
你是一个待办事项分析助手。请判断以下待办事项的归属。

【用户信息】
- 姓名：{user_name}
- 部门：{department}
- 职位：{role}
- 工作描述：{work_description}
- 邮箱：{user_email}

【邮件信息】
- 发件人：{sender}
- 收件人：{recipients}
- 抄送人：{cc}
- 邮件主题：{subject}
- 待办内容：{todo_content}

请判断这个待办事项是否属于该用户，考虑以下因素：
1. 用户是否在邮件的直接收件人列表中
2. 用户是否被抄送
3. 邮件内容是否提到了用户的名字或职位
4. 待办内容是否与用户的工作职责相关

返回 JSON（仅返回 JSON，不要其他内容）：
{{
    "assignee": "归属人姓名（如果属于用户则填用户姓名，如果属于其他人则填其他人姓名，未知则填'未知'）",
    "assign_type": "self/other/team/unknown",
    "confidence": 0.0-1.0,
    "reason": "简短的判断理由（一句话）"
}}
"""
```

### 归属类型说明

| 类型 | 含义 | 示例 |
|------|------|------|
| `self` | 明确属于当前用户 | "张三，请你在周五前提交周报" |
| `other` | 属于其他人 | "@李四，麻烦确认一下这个方案" |
| `team` | 团队共同任务 | "部门所有人参加周五例会" |
| `unknown` | 无法判断 | 泛泛而谈的任务，没有明确责任人 |

---

## 🖼️ UI 设计

### 首次引导对话框

**触发条件**：
- 应用首次启动
- `user_profile` 表中 name 字段为空

**设计要点**：
- 对话框标题：「完善您的信息」
- 可跳过：右下角「跳过」按钮
- 可关闭：右上角关闭按钮
- 轻量级：只收集核心信息

```
┌─────────────────────────────────────────────┐
│     完善您的信息                         [×] │
├─────────────────────────────────────────────┤
│                                             │
│  为了更准确地识别您的待办事项，建议填写：    │
│                                             │
│  您的姓名：[_______________________]         │
│                                             │
│  所属部门：[_______________________]         │
│                                             │
│  职位角色：[_______________________]         │
│                                             │
│  工作描述（选填）：                          │
│  ┌─────────────────────────────────────┐   │
│  │ 例如：负责产品运营、用户增长          │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│         [跳过，稍后设置]    [保存]          │
└─────────────────────────────────────────────┘
```

### 设置页面新增

在现有设置对话框（`settings_dialog.py`）中增加「用户画像」标签页：

**位置**：最后一个标签页

```
设置
├── 通用
├── 同步
├── AI 设置
├── 界面
├── 日历
└── 【新增】用户画像
```

**字段**：
- 姓名（文本框）
- 部门（文本框）
- 职位（文本框）
- 工作描述（多行文本框）

### 待办面板增强

**归属标记显示**：

```
┌─────────────────────────────────────────────┐
│ 📋 待办事项                                  │
├─────────────────────────────────────────────┤
│ ☑ 提交本周周报              [我]  优先级:高  │
│ ☐ 审批采购申请              [我]  优先级:中  │
│ ☐ 准备产品演示材料          [我]  优先级:低  │
│ ☐ 部门团建活动策划          [团队] 优先级:低 │
│ ☐ 确认服务器采购方案        [其他] 优先级:高 │
│    └─ 归属: 张三                            │
│ ☐ 跟进客户需求              [未知] 优先级:中 │
└─────────────────────────────────────────────┘
```

**归属标记样式**：
- `[我]` - 绿色背景
- `[其他]` - 橙色背景，下方显示归属人
- `[团队]` - 蓝色背景
- `[未知]` - 灰色背景

**筛选功能**：
- 待办列表上方增加筛选下拉框
- 选项：「全部」「我的」「团队」「其他」「未分配」

---

## 🔧 技术实现

### 文件结构

```
D:\ai-mail-assistant\
├── src/
│   ├── data/
│   │   └── database.py           # 新增 user_profile 表
│   ├── core/
│   │   ├── ai_service.py         # 修改：调用归属判断
│   │   └── ai_bridge.py          # 新增：归属判断方法
│   └── ui/
│       ├── main_window.py        # 修改：首次引导逻辑
│       ├── settings_dialog.py    # 修改：用户画像标签页
│       └── todo_delegate.py      # 修改：归属标记显示
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-03-24-user-profile-and-todo-assignment-design.md
```

### 核心类设计

#### 1. UserProfileRepo

```python
# src/data/user_profile_repo.py

class UserProfileRepo:
    """用户画像仓储"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        
    def update_profile(self, name: str, department: str, 
                       role: str, work_description: str) -> bool:
        """更新用户画像"""
    
    def is_profile_empty(self) -> bool:
        """检查用户画像是否为空"""
```

#### 2. AI Bridge 扩展

```python
# src/core/ai_bridge.py (新增方法)

class AIBridge:
    # ... 现有方法 ...
    
    def analyze_todo_assignment(self, 
                                 todo_content: str,
                                 email_context: Dict[str, Any],
                                 user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析待办事项归属
        
        Args:
            todo_content: 待办内容
            email_context: 邮件上下文（收件人、抄送人等）
            user_profile: 用户画像
            
        Returns:
            {
                'assignee': str,
                'assign_type': str,
                'confidence': float,
                'reason': str
            }
        """
```

#### 3. 首次引导对话框

```python
# src/ui/profile_setup_dialog.py (新增文件)

class ProfileSetupDialog(QDialog):
    """用户画像设置对话框（首次引导）"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.profile_repo = UserProfileRepo(db)
        self._init_ui()
    
    def _init_ui(self):
        # 初始化 UI 组件
        # 姓名、部门、职位、工作描述文本框
        # 跳过、保存按钮
        pass
```

---

## 📝 开发任务清单

### Phase 6.1：数据库层（1 天）
- [ ] 创建 `user_profile` 表
- [ ] 修改 `todos` 表结构（新增字段）
- [ ] 实现 `UserProfileRepo` 类
- [ ] 编写数据库迁移脚本

### Phase 6.2：AI 层（2 天）
- [ ] 实现 `analyze_todo_assignment` 方法
- [ ] 设计并测试 AI Prompt
- [ ] 集成到 `ai_service.py` 流程
- [ ] 处理 AI 返回结果并存储

### Phase 6.3：UI 层（2 天）
- [ ] 实现首次引导对话框
- [ ] 设置页面新增用户画像标签页
- [ ] 待办面板显示归属标记
- [ ] 实现归属筛选功能

### Phase 6.4：测试与优化（1 天）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试（AI 响应时间）
- [ ] 用户体验优化

**预计总工时**：6 人天

---

## 🎯 成功指标

1. **归属准确率**：AI 判断的准确率 ≥ 85%（人工评测）
2. **响应时间**：归属判断增加时间 ≤ 2 秒
3. **用户采用率**：首次引导完成率 ≥ 70%

---

## 📌 Phase 7 预告

**部门协作功能**（后续规划）：
- 部门管理（部门名称 + 密钥）
- Leader 身份验证
- SQLite 网络共享机制
- Leader 查看部门待办

**技术储备**：
- Phase 6 的用户画像可作为 Phase 7 的基础
- 待办归属逻辑可直接复用
- 数据库结构已预留扩展空间

---

## 📚 附录

### A. 数据库迁移脚本

```python
# scripts/migrate_phase6.py

def migrate_phase6(db: Database):
    """Phase 6 数据库迁移"""
    
    # 1. 创建 user_profile 表
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name VARCHAR(100),
            department VARCHAR(100),
            role VARCHAR(100),
            work_description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 初始化空记录
    db.execute('INSERT OR IGNORE INTO user_profile (id) VALUES (1)')
    
    # 3. 修改 todos 表（SQLite 不支持 IF NOT EXISTS，需要检查）
    try:
        db.execute('ALTER TABLE todos ADD COLUMN assignee VARCHAR(100)')
    except:
        pass  # 字段已存在
    
    try:
        db.execute('ALTER TABLE todos ADD COLUMN assign_type VARCHAR(20)')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE todos ADD COLUMN confidence REAL')
    except:
        pass
    
    try:
        db.execute('ALTER TABLE todos ADD COLUMN assign_reason TEXT')
    except:
        pass
    
    db.connection.commit()
```

### B. API 使用示例

```python
# 使用示例

from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo
from src.core.ai_bridge import AIBridge

# 初始化
db = Database()
profile_repo = UserProfileRepo(db)
ai_bridge = AIBridge()

# 更新用户画像
profile_repo.update_profile(
    name="张三",
    department="产品部",
    role="产品经理",
    work_description="负责用户增长、数据分析、产品运营"
)

# 分析待办归属
email_context = {
    'sender': '李四 <lisi@example.com>',
    'recipients': 'zhangsan@example.com',
    'cc': 'wangwu@example.com',
    'subject': '关于下周产品会议',
}

user_profile = profile_repo.get_profile()

result = ai_bridge.analyze_todo_assignment(
    todo_content="准备下周一的产品演示材料",
    email_context=email_context,
    user_profile=user_profile
)

# result:
# {
#     'assignee': '张三',
#     'assign_type': 'self',
#     'confidence': 0.92,
#     'reason': '用户是直接收件人，且待办与工作职责匹配'
# }
```

---

**文档版本**：v1.0  
**创建日期**：2026-03-24  
**作者**：WorkBuddy AI Assistant
