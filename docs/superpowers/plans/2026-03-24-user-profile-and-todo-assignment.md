# 用户画像与待办归属优化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现用户画像功能和 AI 待办归属判断，提升待办识别准确性

**Architecture:** 本地存储用户画像（SQLite），AI Bridge 新增归属分析方法，AIService 集成归属判断流程，UI 提供首次引导和设置页面

**Tech Stack:** Python 3.13, PyQt5, SQLite, Ollama (qwen3:8b)

---

## 文件结构

### 新增文件
```
D:\ai-mail-assistant\
├── src\
│   └── data\
│       └── user_profile_repo.py          # 用户画像仓储类
├── src\
│   └── ui\
│       └── profile_setup_dialog.py       # 首次引导对话框
└── scripts\
    └── migrate_phase6.py                 # 数据库迁移脚本
```

### 修改文件
```
D:\ai-mail-assistant\
├── src\
│   ├── data\
│   │   └── database.py                   # 新增 user_profile 表
│   ├── core\
│   │   ├── ai_bridge.py                  # 新增 analyze_todo_assignment 方法
│   │   └── ai_service.py                 # 集成归属判断
│   └── ui\
│       ├── main_window.py                # 首次引导检查逻辑
│       ├── settings_dialog.py            # 新增用户画像标签页
│       └── todo_delegate.py              # 显示归属标记
└── tests\
    ├── test_user_profile_repo.py         # 用户画像测试
    ├── test_ai_assignment.py             # 归属判断测试
    └── test_ui_profile.py                # UI 测试
```

---

## Task 1: 数据库层 - 用户画像表

**Files:**
- Modify: `D:\ai-mail-assistant\src\data\database.py:170-184`
- Create: `D:\ai-mail-assistant\scripts\migrate_phase6.py`
- Test: `D:\ai-mail-assistant\tests\test_database_phase6.py`

- [ ] **Step 1: 编写数据库迁移测试**

```python
# tests/test_database_phase6.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database

def test_user_profile_table_exists():
    """测试 user_profile 表是否存在"""
    db = Database(':memory:')
    
    # 检查表是否存在
    result = db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'"
    )
    assert result is not None, "user_profile 表应该存在"

def test_user_profile_initial_record():
    """测试 user_profile 初始记录"""
    db = Database(':memory:')
    
    # 检查初始记录
    result = db.query_one("SELECT * FROM user_profile WHERE id = 1")
    assert result is not None, "应该有一条 id=1 的初始记录"

def test_todos_new_columns():
    """测试 todos 表新增字段"""
    db = Database(':memory:')
    
    # 插入测试数据
    email_id = db.execute(
        "INSERT INTO emails (uid, account_id, subject, sender, sender_email, recipients, date, folder) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("test-uid", 1, "Test", "Sender", "sender@test.com", "test@test.com", "2026-03-24", "INBOX")
    )
    
    # 插入待办
    todo_id = db.execute(
        "INSERT INTO todos (email_id, content, assignee, assign_type, confidence, assign_reason) VALUES (?, ?, ?, ?, ?, ?)",
        (email_id, "Test todo", "张三", "self", 0.95, "用户是直接收件人")
    )
    
    # 查询验证
    result = db.query_one("SELECT * FROM todos WHERE id = ?", (todo_id,))
    assert result['assignee'] == "张三"
    assert result['assign_type'] == "self"
    assert result['confidence'] == 0.95
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_database_phase6.py -v`
Expected: FAIL - user_profile 表不存在

- [ ] **Step 3: 修改 database.py 添加 user_profile 表**

在 `database.py` 的 `_init_db` 方法中，`# 初始化默认设置` 之前添加：

```python
# src/data/database.py (在第 170 行之前添加)

# 用户画像表
cursor.execute('''
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

# 初始化用户画像记录
cursor.execute('INSERT OR IGNORE INTO user_profile (id) VALUES (1)')

# 为 todos 表新增字段
try:
    cursor.execute('ALTER TABLE todos ADD COLUMN assignee VARCHAR(100)')
except:
    pass  # 字段已存在

try:
    cursor.execute('ALTER TABLE todos ADD COLUMN assign_type VARCHAR(20)')
except:
    pass

try:
    cursor.execute('ALTER TABLE todos ADD COLUMN confidence REAL')
except:
    pass

try:
    cursor.execute('ALTER TABLE todos ADD COLUMN assign_reason TEXT')
except:
    pass
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_database_phase6.py -v`
Expected: PASS

- [ ] **Step 5: 提交数据库层变更**

```bash
git add src/data/database.py tests/test_database_phase6.py
git commit -m "feat(database): 添加 user_profile 表和 todos 归属字段"
```

---

## Task 2: 用户画像仓储类

**Files:**
- Create: `D:\ai-mail-assistant\src\data\user_profile_repo.py`
- Test: `D:\ai-mail-assistant\tests\test_user_profile_repo.py`

- [ ] **Step 1: 编写用户画像仓储测试**

```python
# tests/test_user_profile_repo.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo

def test_get_empty_profile():
    """测试获取空用户画像"""
    db = Database(':memory:')
    repo = UserProfileRepo(db)
    
    profile = repo.get_profile()
    assert profile['name'] is None
    assert profile['department'] is None
    assert profile['role'] is None

def test_update_profile():
    """测试更新用户画像"""
    db = Database(':memory:')
    repo = UserProfileRepo(db)
    
    # 更新画像
    success = repo.update_profile(
        name="张三",
        department="产品部",
        role="产品经理",
        work_description="负责用户增长和数据分析"
    )
    assert success is True
    
    # 验证更新
    profile = repo.get_profile()
    assert profile['name'] == "张三"
    assert profile['department'] == "产品部"
    assert profile['role'] == "产品经理"
    assert "用户增长" in profile['work_description']

def test_is_profile_empty():
    """测试检查画像是否为空"""
    db = Database(':memory:')
    repo = UserProfileRepo(db)
    
    # 初始为空
    assert repo.is_profile_empty() is True
    
    # 填写姓名后不为空
    repo.update_profile(name="张三", department="", role="", work_description="")
    assert repo.is_profile_empty() is False

def test_get_user_email():
    """测试获取用户邮箱（从 accounts 表）"""
    db = Database(':memory:')
    repo = UserProfileRepo(db)
    
    # 创建测试账号
    db.execute(
        "INSERT INTO accounts (email_address, display_name, imap_server, imap_port) VALUES (?, ?, ?, ?)",
        ("zhangsan@example.com", "张三", "imap.example.com", 993)
    )
    
    email = repo.get_user_email()
    assert email == "zhangsan@example.com"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_user_profile_repo.py -v`
Expected: FAIL - UserProfileRepo 模块不存在

- [ ] **Step 3: 实现 UserProfileRepo 类**

```python
# src/data/user_profile_repo.py
"""
用户画像仓储模块
管理用户个人信息、部门、角色等数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Any, Optional
from src.data.database import Database


class UserProfileRepo:
    """用户画像仓储类"""
    
    def __init__(self, db: Database):
        """
        初始化用户画像仓储
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def get_profile(self) -> Dict[str, Any]:
        """
        获取用户画像
        
        Returns:
            用户画像字典，包含 name, department, role, work_description
        """
        result = self.db.query_one("SELECT * FROM user_profile WHERE id = 1")
        if result:
            return {
                'name': result['name'],
                'department': result['department'],
                'role': result['role'],
                'work_description': result['work_description'],
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
        return {
            'name': None,
            'department': None,
            'role': None,
            'work_description': None,
            'created_at': None,
            'updated_at': None
        }
    
    def update_profile(self, name: str, department: str, 
                       role: str, work_description: str) -> bool:
        """
        更新用户画像
        
        Args:
            name: 用户姓名
            department: 部门名称
            role: 职位角色
            work_description: 工作描述
            
        Returns:
            是否更新成功
        """
        try:
            self.db.execute(
                """UPDATE user_profile 
                SET name = ?, department = ?, role = ?, work_description = ?, 
                    updated_at = datetime('now')
                WHERE id = 1""",
                (name, department, role, work_description)
            )
            return True
        except Exception as e:
            print(f"更新用户画像失败: {e}")
            return False
    
    def is_profile_empty(self) -> bool:
        """
        检查用户画像是否为空
        
        Returns:
            如果姓名为空则返回 True
        """
        profile = self.get_profile()
        return profile['name'] is None or profile['name'].strip() == ''
    
    def get_user_email(self) -> Optional[str]:
        """
        获取用户邮箱（从 accounts 表）
        
        Returns:
            第一个账号的邮箱地址，如果没有则返回 None
        """
        result = self.db.query_one(
            "SELECT email_address FROM accounts WHERE is_active = 1 LIMIT 1"
        )
        if result:
            return result['email_address']
        return None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_user_profile_repo.py -v`
Expected: PASS

- [ ] **Step 5: 提交用户画像仓储**

```bash
git add src/data/user_profile_repo.py tests/test_user_profile_repo.py
git commit -m "feat(data): 实现用户画像仓储类"
```

---

## Task 3: AI Bridge - 待办归属判断

**Files:**
- Modify: `D:\ai-mail-assistant\src\core\ai_bridge.py`
- Test: `D:\ai-mail-assistant\tests\test_ai_assignment.py`

- [ ] **Step 1: 编写归属判断测试**

```python
# tests/test_ai_assignment.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ai_bridge import AIBridge
from src.data.database import Database

def test_analyze_todo_assignment_self():
    """测试待办归属判断 - 属于自己"""
    db = Database(':memory:')
    bridge = AIBridge(db)
    
    user_profile = {
        'name': '张三',
        'department': '产品部',
        'role': '产品经理',
        'work_description': '负责用户增长、数据分析'
    }
    
    email_context = {
        'sender': '李四 <lisi@example.com>',
        'recipients': 'zhangsan@example.com',
        'cc': '',
        'subject': '关于下周产品会议'
    }
    
    # 注意：这个测试需要 Ollama 服务运行
    # 在 CI 环境中可能需要 mock
    result = bridge.analyze_todo_assignment(
        todo_content="准备下周一的产品演示材料",
        email_context=email_context,
        user_profile=user_profile
    )
    
    assert result['assign_type'] in ['self', 'team']
    assert result['confidence'] >= 0.0 and result['confidence'] <= 1.0
    assert 'reason' in result

def test_analyze_todo_assignment_other():
    """测试待办归属判断 - 属于他人"""
    db = Database(':memory:')
    bridge = AIBridge(db)
    
    user_profile = {
        'name': '张三',
        'department': '产品部',
        'role': '产品经理',
        'work_description': '负责用户增长、数据分析'
    }
    
    email_context = {
        'sender': '王五 <wangwu@example.com>',
        'recipients': 'lisi@example.com',
        'cc': 'zhangsan@example.com',
        'subject': '技术方案确认'
    }
    
    result = bridge.analyze_todo_assignment(
        todo_content="@李四 请确认服务器采购方案",
        email_context=email_context,
        user_profile=user_profile
    )
    
    # 用户只是抄送，且任务明确指向李四
    assert result['assign_type'] in ['other', 'unknown']
    assert 'assignee' in result

def test_assignment_result_format():
    """测试归属判断结果格式"""
    db = Database(':memory:')
    bridge = AIBridge(db)
    
    user_profile = {'name': '张三', 'department': '', 'role': '', 'work_description': ''}
    email_context = {'sender': '', 'recipients': '', 'cc': '', 'subject': ''}
    
    result = bridge.analyze_todo_assignment(
        todo_content="测试任务",
        email_context=email_context,
        user_profile=user_profile
    )
    
    # 验证返回格式
    assert 'assignee' in result
    assert 'assign_type' in result
    assert 'confidence' in result
    assert 'reason' in result
    assert result['assign_type'] in ['self', 'other', 'team', 'unknown']
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_ai_assignment.py -v`
Expected: FAIL - analyze_todo_assignment 方法不存在

- [ ] **Step 3: 在 ai_bridge.py 中添加归属判断方法**

在 `AIBridge` 类中添加以下方法：

```python
# src/core/ai_bridge.py (在类的末尾添加)

def analyze_todo_assignment(self, 
                            todo_content: str,
                            email_context: Dict[str, Any],
                            user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析待办事项归属
    
    Args:
        todo_content: 待办内容
        email_context: 邮件上下文，包含 sender, recipients, cc, subject
        user_profile: 用户画像，包含 name, department, role, work_description
        
    Returns:
        {
            'assignee': str,
            'assign_type': 'self' | 'other' | 'team' | 'unknown',
            'confidence': float,
            'reason': str
        }
    """
    prompt = f"""
你是一个待办事项分析助手。请判断以下待办事项的归属。

【用户信息】
- 姓名：{user_profile.get('name', '未知')}
- 部门：{user_profile.get('department', '未知')}
- 职位：{user_profile.get('role', '未知')}
- 工作描述：{user_profile.get('work_description', '无')}

【邮件信息】
- 发件人：{email_context.get('sender', '')}
- 收件人：{email_context.get('recipients', '')}
- 抄送人：{email_context.get('cc', '')}
- 邮件主题：{email_context.get('subject', '')}
- 待办内容：{todo_content}

请判断这个待办事项是否属于该用户，考虑以下因素：
1. 用户是否在邮件的直接收件人列表中（To）
2. 用户是否被抄送（Cc）
3. 邮件内容是否提到了用户的名字或职位
4. 待办内容是否与用户的工作职责相关

返回 JSON（仅返回 JSON，不要其他内容，不要 markdown 代码块）：
{{
    "assignee": "归属人姓名（如果属于用户则填用户姓名，如果属于其他人则填其他人姓名，未知则填'未知'）",
    "assign_type": "self/other/team/unknown",
    "confidence": 0.0-1.0,
    "reason": "简短的判断理由（一句话）"
}}
"""
    
    try:
        # 调用 AI 生成
        response = self._call_ollama(prompt)
        
        # 解析 JSON
        import json
        # 清理可能的 markdown 代码块标记
        if '```' in response:
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]
        
        result = json.loads(response.strip())
        
        # 验证返回格式
        if 'assign_type' not in result:
            result['assign_type'] = 'unknown'
        if 'assignee' not in result:
            result['assignee'] = '未知'
        if 'confidence' not in result:
            result['confidence'] = 0.5
        if 'reason' not in result:
            result['reason'] = 'AI 未返回判断理由'
        
        # 验证 assign_type 取值
        if result['assign_type'] not in ['self', 'other', 'team', 'unknown']:
            result['assign_type'] = 'unknown'
        
        # 验证 confidence 范围
        try:
            result['confidence'] = float(result['confidence'])
            if result['confidence'] < 0:
                result['confidence'] = 0.0
            elif result['confidence'] > 1:
                result['confidence'] = 1.0
        except:
            result['confidence'] = 0.5
        
        return result
        
    except Exception as e:
        self.logger.error(f"归属判断失败: {e}")
        return {
            'assignee': '未知',
            'assign_type': 'unknown',
            'confidence': 0.0,
            'reason': f'AI 分析失败: {str(e)}'
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_ai_assignment.py -v`
Expected: PASS (需要 Ollama 服务运行)

- [ ] **Step 5: 提交 AI 归属判断**

```bash
git add src/core/ai_bridge.py tests/test_ai_assignment.py
git commit -m "feat(ai): 实现待办归属判断功能"
```

---

## Task 4: AI Service 集成归属判断

**Files:**
- Modify: `D:\ai-mail-assistant\src\core\ai_service.py`

- [ ] **Step 1: 修改 ai_service.py 集成归属判断**

在 `AIService` 类中修改 `extract_todos_from_email` 方法：

```python
# src/core/ai_service.py

# 在文件顶部添加导入
from src.data.user_profile_repo import UserProfileRepo

# 在 __init__ 方法中添加
def __init__(self, db: Database):
    # ... 现有代码 ...
    self.profile_repo = UserProfileRepo(db)

# 修改 extract_todos_from_email 方法
def extract_todos_from_email(self, email_id: int) -> List[Dict[str, Any]]:
    """
    从邮件提取待办事项
    
    Args:
        email_id: 邮件 ID
        
    Returns:
        待办事项列表
    """
    # ... 现有的提取逻辑 ...
    
    # 获取邮件信息
    email = self.email_repo.get_email_by_id(email_id)
    if not email:
        return []
    
    # 支持字典和对象两种访问方式
    subject = email['subject'] if isinstance(email, dict) else email.subject
    body = email.get('body_text', email.get('body', '')) if isinstance(email, dict) else email.body
    recipients = email.get('recipients', '') if isinstance(email, dict) else getattr(email, 'recipients', '')
    sender = email.get('sender', '') if isinstance(email, dict) else getattr(email, 'sender', '')
    
    # 调用 AI Bridge 提取待办
    todos = self.ai_bridge.extract_todos(subject, body)
    
    # 【新增】对每个待办进行归属判断
    user_profile = self.profile_repo.get_profile()
    user_email = self.profile_repo.get_user_email()
    
    email_context = {
        'sender': sender,
        'recipients': recipients,
        'cc': '',  # TODO: 从邮件中提取抄送人
        'subject': subject
    }
    
    enriched_todos = []
    for todo in todos:
        # 调用归属判断
        assignment = self.ai_bridge.analyze_todo_assignment(
            todo_content=todo['content'],
            email_context=email_context,
            user_profile=user_profile
        )
        
        # 合并归属信息
        enriched_todo = {
            **todo,
            'assignee': assignment['assignee'],
            'assign_type': assignment['assign_type'],
            'confidence': assignment['confidence'],
            'assign_reason': assignment['reason']
        }
        enriched_todos.append(enriched_todo)
    
    return enriched_todos
```

- [ ] **Step 2: 测试集成**

手动测试或编写集成测试验证归属信息是否正确存储。

- [ ] **Step 3: 提交集成变更**

```bash
git add src/core/ai_service.py
git commit -m "feat(ai): 集成待办归属判断到 AI Service"
```

---

## Task 5: UI - 首次引导对话框

**Files:**
- Create: `D:\ai-mail-assistant\src\ui\profile_setup_dialog.py`
- Test: `D:\ai-mail-assistant\tests\test_ui_profile.py`

- [ ] **Step 1: 编写首次引导对话框**

```python
# src/ui/profile_setup_dialog.py
"""
用户画像设置对话框
首次启动时引导用户填写个人信息
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QWidget
)
from PyQt5.QtCore import Qt
from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo


class ProfileSetupDialog(QDialog):
    """用户画像设置对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.profile_repo = UserProfileRepo(db)
        self._init_ui()
        self._load_existing_profile()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("完善您的信息")
        self.setFixedSize(500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 说明文字
        info_label = QLabel("为了更准确地识别您的待办事项，建议填写以下信息：")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # 姓名
        name_layout = QHBoxLayout()
        name_label = QLabel("您的姓名：")
        name_label.setFixedWidth(100)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入您的姓名")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 部门
        dept_layout = QHBoxLayout()
        dept_label = QLabel("所属部门：")
        dept_label.setFixedWidth(100)
        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText("例如：产品部、技术部、运营部")
        dept_layout.addWidget(dept_label)
        dept_layout.addWidget(self.dept_edit)
        layout.addLayout(dept_layout)
        
        # 职位
        role_layout = QHBoxLayout()
        role_label = QLabel("职位角色：")
        role_label.setFixedWidth(100)
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("例如：产品经理、工程师、设计师")
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.role_edit)
        layout.addLayout(role_layout)
        
        # 工作描述
        desc_label = QLabel("工作描述（选填）：")
        desc_label.setFixedWidth(100)
        layout.addWidget(desc_label)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("例如：负责产品运营、用户增长、数据分析")
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        skip_btn = QPushButton("跳过，稍后设置")
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_profile)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 20px;")
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_existing_profile(self):
        """加载已有画像"""
        profile = self.profile_repo.get_profile()
        if profile['name']:
            self.name_edit.setText(profile['name'])
        if profile['department']:
            self.dept_edit.setText(profile['department'])
        if profile['role']:
            self.role_edit.setText(profile['role'])
        if profile['work_description']:
            self.desc_edit.setText(profile['work_description'])
    
    def _save_profile(self):
        """保存用户画像"""
        name = self.name_edit.text().strip()
        department = self.dept_edit.text().strip()
        role = self.role_edit.text().strip()
        work_description = self.desc_edit.toPlainText().strip()
        
        success = self.profile_repo.update_profile(
            name=name,
            department=department,
            role=role,
            work_description=work_description
        )
        
        if success:
            self.accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "保存失败", "保存用户画像时出错，请重试。")
```

- [ ] **Step 2: 在 main_window.py 中添加首次引导逻辑**

```python
# src/ui/main_window.py

# 在 __init__ 方法末尾添加
from src.data.user_profile_repo import UserProfileRepo
from src.ui.profile_setup_dialog import ProfileSetupDialog

# 在 MainWindow.__init__ 中添加
def __init__(self, db: Database):
    # ... 现有代码 ...
    
    # 检查是否需要显示首次引导
    self._check_profile_setup()

# 添加新方法
def _check_profile_setup(self):
    """检查是否需要显示用户画像设置引导"""
    profile_repo = UserProfileRepo(self.db)
    
    if profile_repo.is_profile_empty():
        # 延迟显示，确保主窗口已经显示
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self._show_profile_setup)

def _show_profile_setup(self):
    """显示用户画像设置对话框"""
    dialog = ProfileSetupDialog(self.db, self)
    dialog.exec_()
```

- [ ] **Step 3: 测试首次引导**

运行应用，验证首次启动时是否显示引导对话框。

- [ ] **Step 4: 提交首次引导 UI**

```bash
git add src/ui/profile_setup_dialog.py src/ui/main_window.py
git commit -m "feat(ui): 添加用户画像首次引导对话框"
```

---

## Task 6: UI - 设置页面用户画像标签页

**Files:**
- Modify: `D:\ai-mail-assistant\src\ui\settings_dialog.py`

- [ ] **Step 1: 在设置对话框中添加用户画像标签页**

参考现有标签页结构，添加用户画像配置页面：

```python
# src/ui/settings_dialog.py

# 在 _init_ui 方法中添加新标签页
from src.data.user_profile_repo import UserProfileRepo

# 在标签页列表中添加
self.tab_widget.addTab(self._create_profile_tab(), "用户画像")

# 添加新方法
def _create_profile_tab(self) -> QWidget:
    """创建用户画像标签页"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # 用户画像仓储
    self.profile_repo = UserProfileRepo(self.db)
    profile = self.profile_repo.get_profile()
    
    # 姓名
    name_layout = QHBoxLayout()
    name_layout.addWidget(QLabel("姓名："))
    self.profile_name_edit = QLineEdit()
    self.profile_name_edit.setText(profile['name'] or '')
    name_layout.addWidget(self.profile_name_edit)
    layout.addLayout(name_layout)
    
    # 部门
    dept_layout = QHBoxLayout()
    dept_layout.addWidget(QLabel("部门："))
    self.profile_dept_edit = QLineEdit()
    self.profile_dept_edit.setText(profile['department'] or '')
    dept_layout.addWidget(self.profile_dept_edit)
    layout.addLayout(dept_layout)
    
    # 职位
    role_layout = QHBoxLayout()
    role_layout.addWidget(QLabel("职位："))
    self.profile_role_edit = QLineEdit()
    self.profile_role_edit.setText(profile['role'] or '')
    role_layout.addWidget(self.profile_role_edit)
    layout.addLayout(role_layout)
    
    # 工作描述
    layout.addWidget(QLabel("工作描述："))
    self.profile_desc_edit = QTextEdit()
    self.profile_desc_edit.setText(profile['work_description'] or '')
    self.profile_desc_edit.setMaximumHeight(100)
    layout.addWidget(self.profile_desc_edit)
    
    layout.addStretch()
    return widget

# 修改 save_settings 方法，保存用户画像
def save_settings(self):
    # ... 现有保存逻辑 ...
    
    # 保存用户画像
    self.profile_repo.update_profile(
        name=self.profile_name_edit.text().strip(),
        department=self.profile_dept_edit.text().strip(),
        role=self.profile_role_edit.text().strip(),
        work_description=self.profile_desc_edit.toPlainText().strip()
    )
```

- [ ] **Step 2: 测试设置页面**

运行应用，打开设置对话框，验证用户画像标签页是否正常工作。

- [ ] **Step 3: 提交设置页面变更**

```bash
git add src/ui/settings_dialog.py
git commit -m "feat(ui): 设置页面添加用户画像标签页"
```

---

## Task 7: UI - 待办面板归属标记

**Files:**
- Modify: `D:\ai-mail-assistant\src\ui\todo_delegate.py`
- Modify: `D:\ai-mail-assistant\src\ui\main_window.py`

- [ ] **Step 1: 修改待办委托显示归属标记**

```python
# src/ui/todo_delegate.py

# 在 paint 方法中添加归属标记显示
def paint(self, painter, option, index):
    # ... 现有绘制逻辑 ...
    
    # 获取归属信息
    assign_type = index.data(Qt.UserRole + 3)  # assign_type
    assignee = index.data(Qt.UserRole + 4)     # assignee
    
    # 绘制归属标记
    if assign_type:
        tag_text = {
            'self': '我',
            'other': '其他',
            'team': '团队',
            'unknown': '未知'
        }.get(assign_type, '未知')
        
        tag_color = {
            'self': '#4CAF50',    # 绿色
            'other': '#FF9800',   # 橙色
            'team': '#2196F3',    # 蓝色
            'unknown': '#9E9E9E'  # 灰色
        }.get(assign_type, '#9E9E9E')
        
        # 绘制标签背景
        tag_rect = QRect(option.rect.right() - 50, option.rect.top() + 5, 40, 20)
        painter.fillRect(tag_rect, QColor(tag_color))
        
        # 绘制标签文字
        painter.setPen(Qt.white)
        painter.drawText(tag_rect, Qt.AlignCenter, tag_text)
        
        # 如果是 other 类型，在下方显示归属人
        if assign_type == 'other' and assignee:
            painter.setPen(QColor('#666'))
            painter.drawText(
                option.rect.left() + 20, 
                option.rect.bottom() - 5, 
                f"归属: {assignee}"
            )
```

- [ ] **Step 2: 修改 main_window.py 传递归属数据**

```python
# src/ui/main_window.py

# 在 _update_todo_list 方法中，设置待办项数据时添加归属信息
todo_item.setData(Qt.UserRole + 3, todo['assign_type'])  # 归属类型
todo_item.setData(Qt.UserRole + 4, todo['assignee'])     # 归属人
```

- [ ] **Step 3: 测试归属标记显示**

运行应用，验证待办列表中是否正确显示归属标记。

- [ ] **Step 4: 提交归属标记 UI**

```bash
git add src/ui/todo_delegate.py src/ui/main_window.py
git commit -m "feat(ui): 待办列表显示归属标记"
```

---

## Task 8: 集成测试与优化

**Files:**
- Create: `D:\ai-mail-assistant\tests\test_phase6_integration.py`

- [ ] **Step 1: 编写集成测试**

```python
# tests/test_phase6_integration.py
"""
Phase 6 集成测试
测试用户画像和待办归属的完整流程
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo
from src.core.ai_bridge import AIBridge
from src.core.ai_service import AIService


def test_full_workflow():
    """测试完整流程"""
    # 1. 初始化数据库
    db = Database(':memory:')
    
    # 2. 设置用户画像
    profile_repo = UserProfileRepo(db)
    profile_repo.update_profile(
        name="张三",
        department="产品部",
        role="产品经理",
        work_description="负责用户增长、数据分析"
    )
    
    # 3. 创建测试邮件
    email_id = db.execute(
        """INSERT INTO emails 
        (uid, account_id, subject, sender, sender_email, recipients, date, folder, body_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("test-uid-001", 1, "关于下周产品会议", "李四", "lisi@example.com", 
         "zhangsan@example.com", "2026-03-24 10:00:00", "INBOX",
         "张三，请你在周五前准备下周一产品演示的材料。")
    )
    
    # 4. 提取待办
    ai_service = AIService(db)
    todos = ai_service.extract_todos_from_email(email_id)
    
    # 5. 验证结果
    assert len(todos) > 0, "应该提取到待办事项"
    
    for todo in todos:
        assert 'assign_type' in todo
        assert 'assignee' in todo
        assert 'confidence' in todo
        # 由于用户是直接收件人且被点名，应该判断为 self
        assert todo['assign_type'] in ['self', 'team']


def test_assignment_accuracy():
    """测试归属判断准确性"""
    db = Database(':memory:')
    bridge = AIBridge(db)
    
    user_profile = {
        'name': '张三',
        'department': '产品部',
        'role': '产品经理',
        'work_description': '负责用户增长'
    }
    
    # 测试场景 1: 直接收件人
    result1 = bridge.analyze_todo_assignment(
        todo_content="准备产品演示",
        email_context={
            'sender': '李四',
            'recipients': 'zhangsan@example.com',
            'cc': '',
            'subject': '产品会议'
        },
        user_profile=user_profile
    )
    assert result1['assign_type'] in ['self', 'team']
    
    # 测试场景 2: 被抄送
    result2 = bridge.analyze_todo_assignment(
        todo_content="@李四 确认方案",
        email_context={
            'sender': '王五',
            'recipients': 'lisi@example.com',
            'cc': 'zhangsan@example.com',
            'subject': '技术方案'
        },
        user_profile=user_profile
    )
    assert result2['assign_type'] in ['other', 'unknown']


def test_profile_persistence():
    """测试用户画像持久化"""
    db = Database(':memory:')
    repo = UserProfileRepo(db)
    
    # 更新画像
    repo.update_profile(
        name="测试用户",
        department="测试部门",
        role="测试工程师",
        work_description="负责测试工作"
    )
    
    # 重新获取
    profile = repo.get_profile()
    assert profile['name'] == "测试用户"
    assert profile['department'] == "测试部门"
```

- [ ] **Step 2: 运行集成测试**

Run: `cd D:\ai-mail-assistant && python -m pytest tests/test_phase6_integration.py -v`
Expected: PASS

- [ ] **Step 3: 手动测试完整流程**

1. 启动应用：`python main.py`
2. 验证首次引导对话框
3. 添加邮箱账号
4. 同步邮件
5. 查看待办列表归属标记
6. 打开设置页面编辑用户画像

- [ ] **Step 4: 性能测试**

测试 AI 归属判断的响应时间：
- 目标：≤ 2 秒
- 如果超时，考虑优化 prompt 或使用更快的模型

- [ ] **Step 5: 提交集成测试**

```bash
git add tests/test_phase6_integration.py
git commit -m "test: 添加 Phase 6 集成测试"
```

---

## 验收标准

完成所有任务后，验证以下功能：

- [ ] 用户画像表正确创建
- [ ] UserProfileRepo 可以正确存储和读取用户画像
- [ ] AI Bridge 可以正确判断待办归属
- [ ] 首次启动时显示引导对话框（可跳过）
- [ ] 设置页面可以编辑用户画像
- [ ] 待办列表显示归属标记
- [ ] 所有测试通过
- [ ] 性能达标（AI 响应 ≤ 2 秒）

---

**计划完成时间**：6 人天

**下一步**：选择执行方式（Subagent-Driven 或 Inline Execution）
