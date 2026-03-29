# Foxmail 邮件智能助手 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成一个可运行的MVP桌面应用，支持IMAP邮件获取、AI摘要生成、待办事项提取

**Architecture:** 
- PyQt5 桌面应用框架，三栏布局设计
- SQLite 本地数据库，支持多邮箱账号
- 模块化AI处理器，支持本地Ollama和云端API
- 后台线程处理IMAP和AI任务，不阻塞UI

**Tech Stack:** Python 3.10+, PyQt5, IMAPClient, SQLite, Ollama, requests

---

## 项目结构

```
D:\ai-mail-assistant\
├── src/
│   ├── main.py                          # 应用入口
│   ├── ui/
│   │   ├── main_window.py              # 主窗口（三栏布局）
│   │   ├── email_list_panel.py         # 邮件列表面板
│   │   ├── summary_panel.py            # 摘要详情面板
│   │   ├── todo_panel.py               # 待办事项面板
│   │   └── settings_dialog.py          # 设置对话框
│   ├── core/
│   │   ├── imap_client.py              # IMAP 客户端封装
│   │   ├── email_parser.py             # 邮件解析器
│   │   ├── ai_bridge.py               # AI 统一接口
│   │   ├── ollama_processor.py         # 本地 Ollama 处理
│   │   ├── cloud_ai_processor.py      # 云端 API 处理
│   │   ├── prompt_engine.py           # 提示词引擎
│   │   └── calendar_sync.py           # 日历同步
│   ├── data/
│   │   ├── database.py                # SQLite 数据库操作
│   │   ├── email_repo.py              # 邮件仓储
│   │   ├── summary_repo.py           # 摘要仓储
│   │   └── todo_repo.py              # 待办仓储
│   └── utils/
│       ├── config_manager.py          # 配置管理
│       └── logger.py                  # 日志工具
├── tests/
│   ├── test_imap_client.py
│   ├── test_ai_processor.py
│   └── test_todo_repo.py
├── requirements.txt
└── project-spec.md
```

---

## Phase 0: 项目基础搭建（1天）

### Task 0.1: 创建项目目录结构

**Files:**
- Create: `D:\ai-mail-assistant\src\__init__.py`
- Create: `D:\ai-mail-assistant\src\ui\__init__.py`
- Create: `D:\ai-mail-assistant\src\core\__init__.py`
- Create: `D:\ai-mail-assistant\src\data\__init__.py`
- Create: `D:\ai-mail-assistant\src\utils\__init__.py`
- Create: `D:\ai-mail-assistant\tests\__init__.py`

- [ ] **Step 1: 创建目录结构**

```bash
cd D:\ai-mail-assistant
mkdir -p src/ui src/core src/data src/utils tests
```

- [ ] **Step 2: 创建 __init__.py 空文件**

```bash
touch src/__init__.py src/ui/__init__.py src/core/__init__.py src/data/__init__.py src/utils/__init__.py tests/__init__.py
```

- [ ] **Step 3: 更新 requirements.txt**

```
PyQt5>=5.15.0
imapclient>=2.3.0
requests>=2.28.0
cryptography>=41.0.0
python-dateutil>=2.8.0
```

- [ ] **Step 4: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 5: 创建 .gitignore**

```bash
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo "venv/" >> .gitignore
echo ".env" >> .gitignore
```

- [ ] **Step 6: 提交代码**

```bash
git add .
git commit -m "chore: create project structure"
```

---

### Task 0.2: 创建日志工具

**Files:**
- Create: `D:\ai-mail-assistant\src\utils\logger.py`
- Create: `D:\ai-mail-assistant\tests\test_logger.py`

- [ ] **Step 1: 创建日志工具**

```python
# src/utils/logger.py
import logging
import os
from datetime import datetime

def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """创建并配置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'{name}_{datetime.now():%Y%m%d}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_dir() -> str:
    """获取日志目录"""
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(app_data, 'ai-mail-assistant', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_logger.py
import pytest
from src.utils.logger import setup_logger, get_log_dir

def test_setup_logger():
    logger = setup_logger('test', get_log_dir())
    assert logger.name == 'test'
    assert logger.level == logging.DEBUG

def test_get_log_dir():
    log_dir = get_log_dir()
    assert 'ai-mail-assistant' in log_dir
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_logger.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add src/utils/logger.py tests/test_logger.py
git commit -m "feat: add logger utility"
```

---

### Task 0.3: 创建占位符类（避免Phase 2依赖问题）

**Files:**
- Create: `D:\ai-mail-assistant\src\data\summary_repo.py`
- Create: `D:\ai-mail-assistant\src\data\todo_repo.py`
- Create: `D:\ai-mail-assistant\src\core\ai_bridge.py`

- [ ] **Step 1: 创建SummaryRepo占位符**

```python
# src/data/summary_repo.py
from typing import Optional
from src.data.database import Database

class SummaryRepo:
    """摘要数据仓储"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_summary(self, email_id: int, summary_text: str, 
                     todos_json: str, model_used: str, tokens_used: int) -> int:
        """保存摘要"""
        sql = '''
            INSERT INTO summaries 
            (email_id, summary_text, todos_json, model_used, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db.execute(sql, (email_id, summary_text, todos_json, 
                                    model_used, tokens_used))
    
    def get_summary_by_email(self, email_id: int) -> Optional[dict]:
        """根据邮件ID获取摘要"""
        sql = 'SELECT * FROM summaries WHERE email_id = ? ORDER BY created_at DESC LIMIT 1'
        result = self.db.query_one(sql, (email_id,))
        if result:
            return {
                'id': result[0],
                'email_id': result[1],
                'summary_text': result[2],
                'todos_json': result[3],
                'model_used': result[4],
                'tokens_used': result[5],
                'created_at': result[6]
            }
        return None
    
    def delete_summary(self, summary_id: int):
        """删除摘要"""
        sql = 'DELETE FROM summaries WHERE id = ?'
        self.db.execute(sql, (summary_id,))
```

- [ ] **Step 2: 创建TodoRepo占位符**

```python
# src/data/todo_repo.py
from typing import Optional, List
from src.data.database import Database

class TodoRepo:
    """待办数据仓储"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_todo(self, content: str, email_id: int = None, 
                    summary_id: int = None, priority: str = '中',
                    due_date: str = None) -> int:
        """创建待办"""
        sql = '''
            INSERT INTO todos 
            (content, email_id, summary_id, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db.execute(sql, (content, email_id, summary_id, priority, due_date))
    
    def get_all_todos(self, completed: bool = None) -> List[dict]:
        """获取所有待办"""
        if completed is None:
            sql = 'SELECT * FROM todos ORDER BY created_at DESC'
            results = self.db.query(sql)
        else:
            sql = 'SELECT * FROM todos WHERE completed = ? ORDER BY created_at DESC'
            results = self.db.query(sql, (1 if completed else 0,))
        
        return [self._row_to_dict(r) for r in results]
    
    def mark_completed(self, todo_id: int, completed: bool = True):
        """标记完成状态"""
        sql = 'UPDATE todos SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        self.db.execute(sql, (1 if completed else 0, todo_id))
    
    def delete_todo(self, todo_id: int):
        """删除待办"""
        sql = 'DELETE FROM todos WHERE id = ?'
        self.db.execute(sql, (todo_id,))
    
    def _row_to_dict(self, row) -> dict:
        """行转字典"""
        return {
            'id': row[0],
            'summary_id': row[1],
            'email_id': row[2],
            'content': row[3],
            'completed': bool(row[4]),
            'priority': row[5],
            'due_date': row[6],
            'calendar_event_id': row[7]
        }
```

- [ ] **Step 3: 创建AIBridge占位符**

```python
# src/core/ai_bridge.py
from typing import Optional
from src.data.database import Database
from dataclasses import dataclass

@dataclass
class SummaryResult:
    """摘要结果"""
    summary: str
    todos: list
    model_used: str
    tokens_used: int

class AIBridge:
    """AI处理器桥接器（Phase 3完整实现）"""
    
    def __init__(self, db: Database):
        self.db = db
        self.current_processor = None  # 后续设置为OllamaProcessor
    
    def generate_summary(self, email_data: dict) -> Optional[SummaryResult]:
        """生成摘要（Phase 3实现）"""
        # TODO: Phase 3实现真正的AI调用
        return SummaryResult(
            summary="[占位] AI摘要功能Phase 3实现",
            todos=[],
            model_used="placeholder",
            tokens_used=0
        )
    
    def is_available(self) -> bool:
        """检查AI是否可用"""
        return True  # 占位符总是可用
    
    def get_current_provider(self) -> str:
        """获取当前AI提供商"""
        return "placeholder"
```

- [ ] **Step 4: 提交代码**

```bash
git add src/data/summary_repo.py src/data/todo_repo.py src/core/ai_bridge.py
git commit -m "feat: add placeholder classes for Phase 2 dependencies"
```

---

## Phase 1: IMAP邮件客户端（3天）

### Task 1.1: 创建数据库模块

**Files:**
- Create: `D:\ai-mail-assistant\src\data\database.py`
- Create: `D:\ai-mail-assistant\tests\test_database.py`

- [ ] **Step 1: 创建数据库模块**

```python
# src/data/database.py
import sqlite3
import os
from typing import Optional

class Database:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            data_dir = os.path.join(app_data, 'ai-mail-assistant', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'app.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 邮箱账号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address VARCHAR(255) UNIQUE NOT NULL,
                display_name VARCHAR(100),
                imap_server VARCHAR(255),
                imap_port INTEGER DEFAULT 993,
                smtp_server VARCHAR(255),
                smtp_port INTEGER DEFAULT 465,
                auth_code_encrypted TEXT,
                default_folder VARCHAR(100) DEFAULT 'INBOX',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 邮件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid VARCHAR(255) UNIQUE NOT NULL,
                account_id INTEGER NOT NULL,
                subject TEXT,
                sender TEXT,
                sender_email TEXT,
                recipients TEXT,
                date DATETIME,
                body_text TEXT,
                body_html TEXT,
                folder VARCHAR(100),
                is_read BOOLEAN DEFAULT 0,
                processed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')
        
        # 摘要表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                summary_text TEXT,
                todos_json TEXT,
                model_used VARCHAR(100),
                tokens_used INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        ''')
        
        # 待办表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_id INTEGER,
                email_id INTEGER,
                content TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                priority VARCHAR(20) DEFAULT '中',
                due_date DATETIME,
                calendar_event_id VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (summary_id) REFERENCES summaries(id),
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        ''')
        
        # 设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                ai_provider VARCHAR(50) DEFAULT 'ollama',
                ollama_url VARCHAR(255) DEFAULT 'http://localhost:11434',
                ollama_model VARCHAR(100) DEFAULT 'qwen2.5:1.5b',
                cloud_api_key_encrypted TEXT,
                cloud_api_endpoint TEXT,
                sync_interval_minutes INTEGER DEFAULT 15,
                auto_process BOOLEAN DEFAULT 0,
                daily_limit_free INTEGER DEFAULT 20
            )
        ''')
        
        # 初始化默认设置
        cursor.execute('INSERT OR IGNORE INTO settings (id) VALUES (1)')
        
        conn.commit()
        conn.close()
    
    def execute(self, sql: str, params: tuple = ()):
        """执行SQL语句"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        result = cursor.lastrowid
        conn.close()
        return result
    
    def query(self, sql: str, params: tuple = ()) -> list:
        """查询SQL语句"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        """查询单条记录"""
        results = self.query(sql, params)
        return results[0] if results else None
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_database.py
import pytest
import os
import tempfile
from src.data.database import Database

@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    yield db
    os.unlink(path)

def test_init_db(temp_db):
    """测试数据库初始化"""
    # 检查表是否存在
    result = temp_db.query(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = [r[0] for r in result]
    assert 'accounts' in table_names
    assert 'emails' in table_names
    assert 'summaries' in table_names
    assert 'todos' in table_names
    assert 'settings' in table_names

def test_insert_account(temp_db):
    """测试插入账号"""
    sql = '''
        INSERT INTO accounts (email_address, imap_server)
        VALUES (?, ?)
    '''
    account_id = temp_db.execute(sql, ('test@example.com', 'imap.example.com'))
    assert account_id > 0
    
    # 验证插入
    result = temp_db.query_one(
        'SELECT email_address FROM accounts WHERE id = ?',
        (account_id,)
    )
    assert result[0] == 'test@example.com'
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_database.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add src/data/database.py tests/test_database.py
git commit -m "feat: add database module with schema"
```

---

### Task 1.2: 创建IMAP客户端

**Files:**
- Create: `D:\ai-mail-assistant\src\core\imap_client.py`
- Create: `D:\ai-mail-assistant\tests\test_imap_client.py`

- [ ] **Step 1: 创建IMAP客户端类**

```python
# src/core/imap_client.py
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Optional, Dict
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailData:
    """邮件数据结构"""
    uid: str
    subject: str
    sender: str
    sender_email: str
    recipients: str
    date: datetime
    body_text: str
    body_html: Optional[str]
    folder: str
    is_read: bool = False

class IMAPClient:
    """IMAP客户端封装"""
    
    def __init__(self):
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.current_folder: Optional[str] = None
        self.email_server: Optional[str] = None
    
    def connect(self, server: str, port: int, email_addr: str, auth_code: str) -> bool:
        """
        连接到IMAP服务器
        
        Args:
            server: IMAP服务器地址 (如 imap.qq.com)
            port: 端口 (默认993)
            email_addr: 邮箱地址
            auth_code: 授权码
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(f"Connecting to IMAP server: {server}:{port}")
            self.connection = imaplib.IMAP4_SSL(server, port)
            self.connection.login(email_addr, auth_code)
            self.email_server = server
            logger.info("IMAP connection successful")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {e}")
            self.connection = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.connection = None
            return False
    
    def disconnect(self):
        """断开IMAP连接"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.connection = None
                self.current_folder = None
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connection is not None
    
    def list_folders(self) -> List[str]:
        """列出所有文件夹"""
        if not self.connection:
            return []
        
        try:
            _, folders = self.connection.list()
            folder_list = []
            for folder in folders:
                # 解析文件夹名称
                parts = folder.decode('utf-8', errors='replace').split('"/"')
                if len(parts) >= 2:
                    folder_name = parts[-1].strip()
                    folder_list.append(folder_name)
            return folder_list
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            return []
    
    def select_folder(self, folder: str = 'INBOX') -> bool:
        """选择文件夹"""
        if not self.connection:
            return False
        
        try:
            _, _ = self.connection.select(folder)
            self.current_folder = folder
            return True
        except Exception as e:
            logger.error(f"Error selecting folder {folder}: {e}")
            return False
    
    def fetch_emails(
        self,
        since_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[EmailData]:
        """
        获取邮件列表
        
        Args:
            since_date: 起始日期
            before_date: 结束日期
            limit: 最多获取数量
        
        Returns:
            List[EmailData]: 邮件列表
        """
        if not self.connection or not self.current_folder:
            return []
        
        try:
            # 构建搜索条件
            search_criteria = []
            if since_date:
                search_criteria.append(f'SINCE {since_date.strftime("%d-%b-%Y")}')
            if before_date:
                search_criteria.append(f'BEFORE {before_date.strftime("%d-%b-%Y")}')
            
            if not search_criteria:
                search_criteria = ['ALL']
            
            # 搜索邮件
            _, search_result = self.connection.search(None, *search_criteria)
            email_ids = search_result[0].split()
            
            # 限制数量
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]
            
            emails = []
            for email_id in email_ids:
                email_data = self._fetch_single_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Fetched {len(emails)} emails")
            return emails
        
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def fetch_email_by_uid(self, uid: str) -> Optional[EmailData]:
        """根据UID获取单封邮件"""
        if not self.connection or not self.current_folder:
            return None
        
        try:
            _, msg_data = self.connection.uid('FETCH', uid, '(RFC822)')
            if msg_data and msg_data[0]:
                raw_email = msg_data[0][1]
                return self._parse_email(uid, raw_email)
        except Exception as e:
            logger.error(f"Error fetching email {uid}: {e}")
        return None
    
    def _fetch_single_email(self, email_id: bytes) -> Optional[EmailData]:
        """获取单封邮件详情"""
        try:
            _, msg_data = self.connection.fetch(email_id, '(RFC822)')
            if msg_data and msg_data[0]:
                raw_email = msg_data[0][1]
                uid = email_id.decode()
                return self._parse_email(uid, raw_email)
        except Exception as e:
            logger.error(f"Error fetching single email: {e}")
        return None
    
    def _parse_email(self, uid: str, raw_email: bytes) -> Optional[EmailData]:
        """解析邮件内容"""
        try:
            msg = email.message_from_bytes(raw_email)
            
            # 解析主题
            subject = self._decode_header(msg.get('Subject', ''))
            
            # 解析发件人
            sender_raw = msg.get('From', '')
            sender, sender_email = self._parse_address(sender_raw)
            
            # 解析收件人
            recipients = self._decode_header(msg.get('To', ''))
            
            # 解析日期
            date_str = msg.get('Date', '')
            date = self._parse_date(date_str)
            
            # 解析正文
            body_text, body_html = self._parse_body(msg)
            
            # 检查是否已读
            flags = msg.get('Flags', '') or msg.get('X-Keywords', '')
            is_read = 'SEEN' in str(flags).upper()
            
            return EmailData(
                uid=uid,
                subject=subject,
                sender=sender,
                sender_email=sender_email,
                recipients=recipients,
                date=date,
                body_text=body_text,
                body_html=body_html,
                folder=self.current_folder or 'INBOX',
                is_read=is_read
            )
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """解码邮件头"""
        if not header:
            return ''
        
        decoded_parts = []
        try:
            parts = decode_header(header)
            for content, charset in parts:
                if isinstance(content, bytes):
                    charset = charset or 'utf-8'
                    decoded_parts.append(content.decode(charset, errors='replace'))
                else:
                    decoded_parts.append(content)
        except Exception:
            return header
        
        return ''.join(decoded_parts)
    
    def _parse_address(self, address_raw: str) -> tuple:
        """解析邮件地址"""
        if not address_raw:
            return ('', '')
        
        try:
            # 格式: "显示名称 <email@example.com>"
            if '<' in address_raw and '>' in address_raw:
                name = address_raw.split('<')[0].strip().strip('"')
                email = address_raw.split('<')[1].split('>')[0].strip()
                return (name, email)
            elif '@' in address_raw:
                return (address_raw, address_raw)
        except Exception:
            pass
        
        return (address_raw, '')
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析邮件日期"""
        if not date_str:
            return datetime.now()
        
        try:
            # 尝试多种日期格式
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            # 使用email.utils解析
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()
    
    def _parse_body(self, msg: email.message.Message) -> tuple:
        """解析邮件正文"""
        body_text = ''
        body_html = ''
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                # 忽略附件
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain' and not body_text:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body_text = payload.decode(charset, errors='replace')
                
                elif content_type == 'text/html' and not body_html:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body_html = payload.decode(charset, errors='replace')
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            content_type = msg.get_content_type()
            
            if content_type == 'text/html':
                body_html = payload.decode(charset, errors='replace')
            else:
                body_text = payload.decode(charset, errors='replace')
        
        return (body_text.strip(), body_html.strip())
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_imap_client.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.imap_client import IMAPClient, EmailData
from datetime import datetime

def test_imap_client_init():
    """测试IMAPClient初始化"""
    client = IMAPClient()
    assert client.connection is None
    assert client.current_folder is None

def test_is_connected():
    """测试连接状态检查"""
    client = IMAPClient()
    assert not client.is_connected()

@patch('imaplib.IMAP4_SSL')
def test_connect_success(mock_imap):
    """测试成功连接"""
    mock_connection = Mock()
    mock_imap.return_value = mock_connection
    
    client = IMAPClient()
    result = client.connect('imap.example.com', 993, 'test@example.com', 'authcode')
    
    assert result is True
    assert client.is_connected()
    mock_connection.login.assert_called_once_with('test@example.com', 'authcode')

@patch('imaplib.IMAP4_SSL')
def test_connect_failure(mock_imap):
    """测试连接失败"""
    import imaplib
    mock_imap.side_effect = imaplib.IMAP4.error("Authentication failed")
    
    client = IMAPClient()
    result = client.connect('imap.example.com', 993, 'test@example.com', 'wrongcode')
    
    assert result is False
    assert not client.is_connected()

def test_disconnect():
    """测试断开连接"""
    client = IMAPClient()
    mock_connection = Mock()
    client.connection = mock_connection
    
    client.disconnect()
    
    assert client.connection is None
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_imap_client.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add src/core/imap_client.py tests/test_imap_client.py
git commit -m "feat: add IMAP client with email parsing"
```

---

### Task 1.3: 创建邮件仓储

**Files:**
- Create: `D:\ai-mail-assistant\src\data\email_repo.py`
- Create: `D:\ai-mail-assistant\tests\test_email_repo.py`

- [ ] **Step 1: 创建邮件仓储类**

```python
# src/data/email_repo.py
from typing import List, Optional
from datetime import datetime
from src.core.imap_client import EmailData
from src.data.database import Database

class EmailRepo:
    """邮件数据仓储"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_email(self, email: EmailData, account_id: int) -> int:
        """保存邮件到数据库"""
        sql = '''
            INSERT OR REPLACE INTO emails 
            (uid, account_id, subject, sender, sender_email, recipients, 
             date, body_text, body_html, folder, is_read, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        email_id = self.db.execute(sql, (
            email.uid,
            account_id,
            email.subject,
            email.sender,
            email.sender_email,
            email.recipients,
            email.date,
            email.body_text,
            email.body_html,
            email.folder,
            email.is_read,
            0
        ))
        
        return email_id
    
    def save_emails_batch(self, emails: List[EmailData], account_id: int) -> int:
        """批量保存邮件"""
        count = 0
        for email in emails:
            self.save_email(email, account_id)
            count += 1
        return count
    
    def get_email_by_id(self, email_id: int) -> Optional[dict]:
        """根据ID获取邮件"""
        sql = 'SELECT * FROM emails WHERE id = ?'
        result = self.db.query_one(sql, (email_id,))
        if result:
            return self._row_to_dict(result)
        return None
    
    def get_email_by_uid(self, uid: str, account_id: int) -> Optional[dict]:
        """根据UID获取邮件"""
        sql = 'SELECT * FROM emails WHERE uid = ? AND account_id = ?'
        result = self.db.query_one(sql, (uid, account_id))
        if result:
            return self._row_to_dict(result)
        return None
    
    def _row_to_dict(self, row) -> dict:
        """行转字典"""
        return {
            'id': row[0], 'uid': row[1], 'account_id': row[2],
            'subject': row[3], 'sender': row[4], 'sender_email': row[5],
            'recipients': row[6], 'date': row[7], 'body_text': row[8],
            'body_html': row[9], 'folder': row[10], 'is_read': bool(row[11]),
            'processed': bool(row[12])
        }
    
    def get_emails_by_account(
        self,
        account_id: int,
        folder: str = 'INBOX',
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """获取账号的邮件列表"""
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? AND folder = ?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        '''
        return self.db.query(sql, (account_id, folder, limit, offset))
    
    def get_unprocessed_emails(self, account_id: int, limit: int = 20) -> List[dict]:
        """获取未处理的邮件"""
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? AND processed = 0
            ORDER BY date DESC
            LIMIT ?
        '''
        return self.db.query(sql, (account_id, limit))
    
    def mark_as_processed(self, email_id: int):
        """标记邮件已处理"""
        sql = 'UPDATE emails SET processed = 1 WHERE id = ?'
        self.db.execute(sql, (email_id,))
    
    def mark_as_read(self, email_id: int):
        """标记邮件已读"""
        sql = 'UPDATE emails SET is_read = 1 WHERE id = ?'
        self.db.execute(sql, (email_id,))
    
    def search_emails(
        self,
        account_id: int,
        keyword: str,
        folder: Optional[str] = None
    ) -> List[dict]:
        """搜索邮件"""
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? 
            AND (subject LIKE ? OR sender LIKE ? OR body_text LIKE ?)
        '''
        params = (account_id, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
        
        if folder:
            sql += ' AND folder = ?'
            params += (folder,)
        
        sql += ' ORDER BY date DESC LIMIT 50'
        
        return self.db.query(sql, params)
    
    def delete_email(self, email_id: int):
        """删除邮件"""
        sql = 'DELETE FROM emails WHERE id = ?'
        self.db.execute(sql, (email_id,))
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_email_repo.py
import pytest
from unittest.mock import Mock, patch
from src.data.email_repo import EmailRepo
from src.data.database import Database
from src.core.imap_client import EmailData
from datetime import datetime
import os
import tempfile

@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    # 创建测试账号
    db.execute(
        'INSERT INTO accounts (email_address, imap_server) VALUES (?, ?)',
        ('test@example.com', 'imap.example.com')
    )
    yield db
    os.unlink(path)

@pytest.fixture
def email_repo(temp_db):
    return EmailRepo(temp_db)

def test_save_email(email_repo, temp_db):
    """测试保存邮件"""
    email = EmailData(
        uid='12345',
        subject='Test Subject',
        sender='Sender Name',
        sender_email='sender@example.com',
        recipients='test@example.com',
        date=datetime.now(),
        body_text='Test body content',
        body_html='',
        folder='INBOX'
    )
    
    email_id = email_repo.save_email(email, account_id=1)
    assert email_id > 0
    
    # 验证保存
    saved = temp_db.query_one('SELECT * FROM emails WHERE id = ?', (email_id,))
    assert saved[2] == '12345'  # uid
    assert saved[3] == 'Test Subject'

def test_save_emails_batch(email_repo):
    """测试批量保存"""
    emails = [
        EmailData(
            uid=f'uid_{i}',
            subject=f'Subject {i}',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            body_html='',
            folder='INBOX'
        )
        for i in range(5)
    ]
    
    count = email_repo.save_emails_batch(emails, account_id=1)
    assert count == 5

def test_mark_as_processed(email_repo, temp_db):
    """测试标记已处理"""
    # 先保存邮件
    email = EmailData(
        uid='test_uid',
        subject='Test',
        sender='Sender',
        sender_email='sender@example.com',
        recipients='test@example.com',
        date=datetime.now(),
        body_text='Body',
        body_html='',
        folder='INBOX'
    )
    email_id = email_repo.save_email(email, account_id=1)
    
    # 标记已处理
    email_repo.mark_as_processed(email_id)
    
    # 验证
    result = temp_db.query_one(
        'SELECT processed FROM emails WHERE id = ?', (email_id,)
    )
    assert result[0] == 1
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_email_repo.py -v
```

- [ ] **Step 4: 提交代码**

```bash
git add src/data/email_repo.py tests/test_email_repo.py
git commit -m "feat: add email repository"
```

---

## Phase 2: PyQt5 UI开发（5天）

### Task 2.1: 创建主窗口

**Files:**
- Create: `D:\ai-mail-assistant\src\ui\main_window.py`
- Modify: `D:\ai-mail-assistant\src\main.py`

- [ ] **Step 1: 创建主窗口类**

```python
# src/ui/main_window.py
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QApplication, QStatusBar, QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from src.ui.email_list_panel import EmailListPanel
from src.ui.summary_panel import SummaryPanel
from src.ui.todo_panel import TodoPanel
from src.utils.logger import setup_logger, get_log_dir
from src.data.database import Database
from src.data.email_repo import EmailRepo
from src.data.todo_repo import TodoRepo
from src.data.summary_repo import SummaryRepo
from src.core.imap_client import IMAPClient
from src.core.ai_bridge import AIBridge

logger = setup_logger('main_window', get_log_dir())

class MainWindow(QMainWindow):
    """主窗口 - 三栏布局"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self.db = Database()
        self.imap_client = IMAPClient()
        self.ai_bridge = AIBridge(self.db)
        
        # 初始化仓储
        self.email_repo = EmailRepo(self.db)
        self.summary_repo = SummaryRepo(self.db)
        self.todo_repo = TodoRepo(self.db)
        
        # 初始化UI
        self.init_ui()
        
        # 设置定时器 - 自动检查新邮件
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.auto_check_emails)
        
        # 加载设置
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('Foxmail 邮件智能助手')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 三栏
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 左侧 - 邮件列表面板
        self.email_list_panel = EmailListPanel()
        self.email_list_panel.email_selected.connect(self.on_email_selected)
        self.email_list_panel.refresh_clicked.connect(self.refresh_emails)
        main_layout.addWidget(self.email_list_panel, 1)
        
        # 中间 - 摘要详情面板
        self.summary_panel = SummaryPanel()
        self.summary_panel.resummarize_requested.connect(self.resummarize_email)
        main_layout.addWidget(self.summary_panel, 1.5)
        
        # 右侧 - 待办面板
        self.todo_panel = TodoPanel()
        self.todo_panel.sync_to_calendar_requested.connect(self.sync_todo_to_calendar)
        main_layout.addWidget(self.todo_panel, 1)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')
        
        # 创建菜单栏
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        add_account_action = QAction('添加邮箱账号', self)
        add_account_action.triggered.connect(self.show_add_account_dialog)
        file_menu.addAction(add_account_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction('设置(&S)', self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&X)', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        refresh_action = QAction('刷新邮件(&R)', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_emails)
        tools_menu.addAction(refresh_action)
        
        process_all_action = QAction('处理所有未读邮件', self)
        process_all_action.triggered.connect(self.process_all_unread)
        tools_menu.addAction(process_all_action)
    
    def load_settings(self):
        """加载设置并启动定时器"""
        settings = self.db.query_one('SELECT * FROM settings WHERE id = 1')
        if settings:
            interval = settings[6] or 15  # sync_interval_minutes
            self.sync_timer.start(interval * 60 * 1000)  # 转换为毫秒
            logger.info(f"Sync timer started: every {interval} minutes")
    
    def auto_check_emails(self):
        """自动检查新邮件"""
        logger.info("Auto checking for new emails...")
        self.status_bar.showMessage('检查新邮件...')
        # TODO: 实现自动检查逻辑
        self.status_bar.showMessage('就绪')
    
    def on_email_selected(self, email_id: int):
        """邮件选中事件"""
        email = self.email_repo.get_email_by_id(email_id)
        if email:
            summary = self.summary_repo.get_summary_by_email(email_id)
            self.summary_panel.display_email(email, summary)
    
    def refresh_emails(self):
        """刷新邮件"""
        self.status_bar.showMessage('刷新邮件...')
        # TODO: 实现邮件刷新逻辑
        self.status_bar.showMessage('就绪')
    
    def resummarize_email(self, email_id: int):
        """重新生成摘要"""
        # TODO: 实现重新生成摘要逻辑
        pass
    
    def sync_todo_to_calendar(self, todo_id: int):
        """同步待办到日历"""
        # TODO: 实现日历同步逻辑
        pass
    
    def show_add_account_dialog(self):
        """显示添加账号对话框"""
        from src.ui.settings_dialog import AddAccountDialog
        dialog = AddAccountDialog(self.db, self)
        if dialog.exec_():
            # 刷新账号列表
            pass
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.db, self)
        if dialog.exec_():
            # 重新加载设置
            self.load_settings()
    
    def process_all_unread(self):
        """处理所有未读邮件"""
        # TODO: 实现批量处理逻辑
        pass
    
    def closeEvent(self, event):
        """关闭事件"""
        self.imap_client.disconnect()
        self.sync_timer.stop()
        event.accept()
```

- [ ] **Step 2: 创建主入口**

```python
# src/main.py
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger, get_log_dir

def main():
    """应用入口"""
    logger = setup_logger('main', get_log_dir())
    logger.info("Application starting...")
    
    app = QApplication(sys.argv)
    app.setApplicationName('Foxmail邮件智能助手')
    
    window = MainWindow()
    window.show()
    
    logger.info("Application window displayed")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

- [ ] **Step 3: 创建邮件列表面板**

```python
# src/ui/email_list_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QLabel, QComboBox, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

class EmailListPanel(QWidget):
    """邮件列表面板"""
    
    email_selected = pyqtSignal(int)  # 邮件ID信号
    refresh_clicked = pyqtSignal()    # 刷新信号
    
    def __init__(self):
        super().__init__()
        self.current_account_id = None
        self.current_folder = 'INBOX'
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 顶部 - 文件夹选择
        top_bar = QHBoxLayout()
        
        folder_label = QLabel('文件夹:')
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(['收件箱', 'INBOX'])
        self.folder_combo.currentTextChanged.connect(self.on_folder_changed)
        
        top_bar.addWidget(folder_label)
        top_bar.addWidget(self.folder_combo)
        top_bar.addStretch()
        
        layout.addLayout(top_bar)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索邮件...')
        self.search_button = QPushButton('搜索')
        self.refresh_button = QPushButton('刷新')
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.refresh_button)
        
        layout.addLayout(search_layout)
        
        # 邮件列表
        self.email_list = QListWidget()
        self.email_list.itemClicked.connect(self.on_email_item_clicked)
        layout.addWidget(self.email_list)
    
    def load_emails(self, emails: list):
        """加载邮件列表"""
        self.email_list.clear()
        
        for email in emails:
            item = QListWidgetItem()
            
            # 构建显示文本
            sender = email.get('sender', '未知发件人')
            subject = email.get('subject', '无主题')
            date = email.get('date', '')
            
            display_text = f"<b>{subject}</b><br>{sender} - {date}"
            item.setData(Qt.UserRole, email.get('id'))
            
            # 创建自定义部件
            widget = self.create_email_item_widget(sender, subject, date, email)
            self.email_list.addItem(item)
            self.email_list.setItemWidget(item, widget)
        
        # 设置列表项高度
        self.email_list.setItemDelegate(EmailListDelegate())
    
    def create_email_item_widget(self, sender: str, subject: str, 
                                  date: str, email: dict) -> QWidget:
        """创建邮件项部件"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setStyleSheet('''
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #f5f5f5;
            }
        ''')
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 主题
        subject_label = QLabel(f'<b>{subject}</b>')
        subject_label.setStyleSheet('color: #333; font-size: 14px;')
        layout.addWidget(subject_label)
        
        # 发件人和时间
        info_label = QLabel(f'{sender} - {date}')
        info_label.setStyleSheet('color: #888; font-size: 12px;')
        layout.addWidget(info_label)
        
        # 待办标签
        if email.get('processed'):
            processed_label = QLabel('✅ 已摘要')
            processed_label.setStyleSheet('''
                background-color: #e8f5e9;
                color: #2e7d32;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            ''')
            layout.addWidget(processed_label)
        
        return widget
    
    def on_email_item_clicked(self, item):
        """邮件项点击"""
        email_id = item.data(Qt.UserRole)
        if email_id:
            self.email_selected.emit(email_id)
    
    def on_folder_changed(self, folder: str):
        """文件夹变更"""
        self.current_folder = folder
        self.refresh_clicked.emit()
    
    def on_refresh_clicked(self):
        """刷新按钮点击"""
        self.refresh_clicked.emit()
    
    def set_account(self, account_id: int):
        """设置当前账号"""
        self.current_account_id = account_id

class EmailListDelegate(QAbstractItemDelegate):
    """邮件列表代理 - 控制列表项高度"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_height = 80  # 每个邮件项的高度
    
    def sizeHint(self, option, index):
        """设置每个列表项的大小"""
        return QSize(0, self.item_height)
    
    def setItemHeight(self, height: int):
        """设置项高度"""
        self.item_height = height
```

- [ ] **Step 4: 创建摘要详情面板**

```python
# src/ui/summary_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton,
    QFrame, QCheckBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

class SummaryPanel(QWidget):
    """摘要详情面板"""
    
    resummarize_requested = pyqtSignal(int)  # 重新摘要信号
    
    def __init__(self):
        super().__init__()
        self.current_email_id = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 顶部 - 邮件信息
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet('''
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
        ''')
        header_layout = QVBoxLayout(self.header_frame)
        
        self.subject_label = QLabel()
        self.subject_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #333;')
        header_layout.addWidget(self.subject_label)
        
        self.sender_label = QLabel()
        self.sender_label.setStyleSheet('font-size: 13px; color: #666;')
        header_layout.addWidget(self.sender_label)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet('font-size: 12px; color: #999;')
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(self.header_frame)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.resummarize_btn = QPushButton('🔄 重新摘要')
        self.resummarize_btn.clicked.connect(self.on_resummarize_clicked)
        self.mark_read_btn = QPushButton('✓ 标记已读')
        btn_layout.addWidget(self.resummarize_btn)
        btn_layout.addWidget(self.mark_read_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # AI摘要区域
        summary_label = QLabel('📝 AI摘要')
        summary_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #667eea;')
        layout.addWidget(summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet('''
            background-color: #e8eaf6;
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            line-height: 1.6;
        ''')
        layout.addWidget(self.summary_text, 1)
        
        # 待办事项区域
        todo_label = QLabel('📋 提取的待办事项')
        todo_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #4caf50;')
        layout.addWidget(todo_label)
        
        self.todo_list = QVBoxLayout()
        layout.addLayout(self.todo_list)
        
        # 原始邮件内容（可折叠）
        self.original_btn = QPushButton('📄 查看原始邮件')
        self.original_btn.setCheckable(True)
        self.original_btn.clicked.connect(self.toggle_original)
        layout.addWidget(self.original_btn)
        
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setMaximumHeight(0)
        self.original_text.setStyleSheet('''
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
        ''')
        layout.addWidget(self.original_text)
    
    def display_email(self, email: dict, summary: dict = None):
        """显示邮件和摘要"""
        self.current_email_id = email.get('id')
        
        # 显示邮件信息
        self.subject_label.setText(email.get('subject', '无主题'))
        self.sender_label.setText(f"发件人: {email.get('sender', '未知')} <{email.get('sender_email', '')}>")
        self.date_label.setText(f"时间: {email.get('date', '')}")
        
        # 显示摘要
        if summary:
            self.summary_text.setText(summary.get('summary_text', '暂无摘要'))
            self._display_todos(summary.get('todos_json'))
        else:
            self.summary_text.setText('点击"重新摘要"按钮生成AI摘要')
            self._clear_todos()
        
        # 显示原始邮件
        self.original_text.setText(email.get('body_text', email.get('body_html', '')))
    
    def _display_todos(self, todos_json: str):
        """显示待办事项"""
        self._clear_todos()
        
        if not todos_json:
            return
        
        import json
        try:
            todos = json.loads(todos_json)
        except:
            return
        
        for todo in todos:
            todo_widget = QFrame()
            todo_widget.setStyleSheet('''
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 8px;
            ''')
            
            todo_layout = QHBoxLayout(todo_widget)
            todo_layout.setContentsMargins(5, 5, 5, 5)
            
            checkbox = QCheckBox(todo)
            checkbox.setStyleSheet('font-size: 14px;')
            todo_layout.addWidget(checkbox)
            todo_layout.addStretch()
            
            self.todo_list.addWidget(todo_widget)
    
    def _clear_todos(self):
        """清除待办事项"""
        while self.todo_list.count():
            item = self.todo_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_resummarize_clicked(self):
        """重新摘要按钮点击"""
        if self.current_email_id:
            self.resummarize_requested.emit(self.current_email_id)
    
    def toggle_original(self, checked: bool):
        """切换原始邮件显示"""
        if checked:
            self.original_text.setMaximumHeight(200)
            self.original_btn.setText('📄 收起原始邮件')
        else:
            self.original_text.setMaximumHeight(0)
            self.original_btn.setText('📄 查看原始邮件')
```

- [ ] **Step 5: 创建待办面板**

```python
# src/ui/todo_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QCheckBox,
    QButtonGroup, QRadioButton, QScrollArea,
    QVBoxLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

class TodoPanel(QWidget):
    """待办事项面板"""
    
    sync_to_calendar_requested = pyqtSignal(int)  # 同步到日历信号
    
    def __init__(self):
        super().__init__()
        self.current_filter = 'all'
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel('✅ 我的待办')
        title_label.setStyleSheet('''
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            padding: 8px;
        ''')
        layout.addWidget(title_label)
        
        # 筛选按钮
        filter_layout = QHBoxLayout()
        self.filter_group = QButtonGroup()
        
        self.all_btn = QRadioButton('全部')
        self.uncompleted_btn = QRadioButton('未完成')
        self.completed_btn = QRadioButton('已完成')
        
        self.filter_group.addButton(self.all_btn, 0)
        self.filter_group.addButton(self.uncompleted_btn, 1)
        self.filter_group.addButton(self.completed_btn, 2)
        
        self.all_btn.setChecked(True)
        self.filter_group.buttonClicked[int].connect(self.on_filter_changed)
        
        filter_layout.addWidget(self.all_btn)
        filter_layout.addWidget(self.uncompleted_btn)
        filter_layout.addWidget(self.completed_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 待办列表（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('border: none;')
        
        self.todo_container = QWidget()
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.todo_container)
        layout.addWidget(scroll, 1)
        
        # 底部 - 版本信息
        footer_frame = QFrame()
        footer_frame.setStyleSheet('''
            background-color: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            padding: 10px;
        ''')
        footer_layout = QVBoxLayout(footer_frame)
        
        version_label = QLabel('🆓 免费版 · 本地Ollama模型')
        version_label.setStyleSheet('font-size: 12px; color: #888; text-align: center;')
        version_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(version_label)
        
        upgrade_btn = QPushButton('💎 升级到付费版')
        upgrade_btn.setStyleSheet('''
            background-color: #667eea;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: bold;
        ''')
        footer_layout.addWidget(upgrade_btn)
        
        layout.addWidget(footer_frame)
    
    def load_todos(self, todos: list):
        """加载待办列表"""
        self._clear_todos()
        
        for todo in todos:
            # 根据筛选条件
            if self.current_filter == 'uncompleted' and todo.get('completed'):
                continue
            if self.current_filter == 'completed' and not todo.get('completed'):
                continue
            
            todo_widget = self.create_todo_widget(todo)
            self.todo_layout.addWidget(todo_widget)
    
    def create_todo_widget(self, todo: dict) -> QWidget:
        """创建待办项部件"""
        widget = QFrame()
        
        if todo.get('completed'):
            widget.setStyleSheet('''
                background-color: #e8f5e9;
                border-left: 3px solid #4caf50;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 8px;
            ''')
        else:
            widget.setStyleSheet('''
                background-color: white;
                border-left: 3px solid #ff9800;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 8px;
            ''')
        
        layout = QVBoxLayout(widget)
        
        # 待办内容
        content_label = QLabel(todo.get('content', ''))
        if todo.get('completed'):
            content_label.setStyleSheet('text-decoration: line-through; color: #888; font-size: 13px;')
        else:
            content_label.setStyleSheet('font-size: 13px; color: #333;')
        layout.addWidget(content_label)
        
        # 来源和截止日期
        info = f"来源: {todo.get('source', '手动添加')}"
        if todo.get('due_date'):
            info += f" · 截止: {todo.get('due_date')}"
        
        info_label = QLabel(info)
        info_label.setStyleSheet('font-size: 11px; color: #888;')
        layout.addWidget(info_label)
        
        # 操作按钮
        if not todo.get('completed'):
            btn_layout = QHBoxLayout()
            sync_btn = QPushButton('📅 同步日历')
            sync_btn.setStyleSheet('''
                background-color: #e3f2fd;
                color: #1565c0;
                border: none;
                padding: 4px 10px;
                border-radius: 10px;
                font-size: 11px;
            ''')
            sync_btn.clicked.connect(lambda: self.on_sync_clicked(todo.get('id')))
            btn_layout.addWidget(sync_btn)
            btn_layout.addStretch()
            
            layout.addLayout(btn_layout)
        
        return widget
    
    def _clear_todos(self):
        """清除待办列表"""
        while self.todo_layout.count():
            item = self.todo_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def on_filter_changed(self, id: int):
        """筛选条件变更"""
        filters = {0: 'all', 1: 'uncompleted', 2: 'completed'}
        self.current_filter = filters.get(id, 'all')
        # TODO: 重新加载待办列表
    
    def on_sync_clicked(self, todo_id: int):
        """同步到日历"""
        self.sync_to_calendar_requested.emit(todo_id)
```

- [ ] **Step 6: 运行测试确认UI正常**

```bash
python src/main.py
```

- [ ] **Step 7: 提交代码**

```bash
git add src/ui/main_window.py src/ui/email_list_panel.py src/ui/summary_panel.py src/ui/todo_panel.py src/main.py
git commit -m "feat: add PyQt5 main window with three-panel layout"
```

---

### Task 2.2: 创建设置对话框

**Files:**
- Create: `D:\ai-mail-assistant\src\ui\settings_dialog.py`

- [ ] **Step 1: 创建设置对话框**

```python
# src/ui/settings_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTabWidget, QWidget, QFormLayout, QGroupBox,
    QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('设置')
        self.setGeometry(300, 200, 500, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # AI设置页
        ai_tab = self.create_ai_tab()
        tabs.addTab(ai_tab, '🤖 AI设置')
        
        # 同步设置页
        sync_tab = self.create_sync_tab()
        tabs.addTab(sync_tab, '🔄 同步设置')
        
        # 账号管理页
        account_tab = self.create_account_tab()
        tabs.addTab(account_tab, '📧 邮箱账号')
        
        layout.addWidget(tabs)
        
        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def create_ai_tab(self) -> QWidget:
        """创建AI设置页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # AI提供商
        provider_group = QGroupBox('AI模型提供商')
        provider_layout = QFormLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            'Ollama (本地 - 免费)',
            '文心一言 (云端)',
            '通义千问 (云端)',
            'DeepSeek (云端)'
        ])
        provider_layout.addRow('提供商:', self.provider_combo)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Ollama设置
        ollama_group = QGroupBox('Ollama本地模型设置')
        ollama_layout = QFormLayout()
        
        self.ollama_url = QLineEdit('http://localhost:11434')
        ollama_layout.addRow('服务地址:', self.ollama_url)
        
        self.ollama_model = QComboBox()
        self.ollama_model.addItems([
            'qwen2.5:1.5b (推荐，低内存)',
            'qwen2.5:3b (更高质量)',
            'qwen2.5:7b (最佳质量)'
        ])
        ollama_layout.addRow('模型:', self.ollama_model)
        
        ollama_group.setLayout(ollama_layout)
        layout.addWidget(ollama_group)
        
        # 云端API设置
        cloud_group = QGroupBox('云端API设置（付费功能）')
        cloud_layout = QFormLayout()
        
        self.api_endpoint = QLineEdit()
        self.api_endpoint.setPlaceholderText('https://api.example.com/v1/chat')
        cloud_layout.addRow('API地址:', self.api_endpoint)
        
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText('输入API密钥')
        cloud_layout.addRow('API密钥:', self.api_key)
        
        cloud_group.setLayout(cloud_layout)
        layout.addWidget(cloud_group)
        
        layout.addStretch()
        return widget
    
    def create_sync_tab(self) -> QWidget:
        """创建同步设置页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # 自动同步设置
        sync_group = QGroupBox('自动同步')
        sync_layout = QFormLayout()
        
        self.auto_sync = QCheckBox('启用自动检查新邮件')
        sync_layout.addRow('自动检查:', self.auto_sync)
        
        self.sync_interval = QSpinBox()
        self.sync_interval.setRange(5, 60)
        self.sync_interval.setSuffix(' 分钟')
        sync_layout.addRow('检查间隔:', self.sync_interval)
        
        self.auto_process = QCheckBox('收到新邮件自动生成摘要')
        sync_layout.addRow('自动处理:', self.auto_process)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # 免费版限制
        limit_group = QGroupBox('免费版限制')
        limit_layout = QVBoxLayout()
        
        limit_info = QLabel(
            '🆓 免费版每天最多处理 20 封邮件\n'
            '💎 升级到付费版可解除限制'
        )
        limit_info.setStyleSheet('padding: 10px;')
        limit_layout.addWidget(limit_info)
        
        self.daily_limit = QSpinBox()
        self.daily_limit.setRange(10, 100)
        self.daily_limit.setSuffix(' 封')
        limit_layout.addRow('每日限制:', self.daily_limit)
        
        limit_group.setLayout(limit_layout)
        layout.addWidget(limit_group)
        
        layout.addStretch()
        return widget
    
    def create_account_tab(self) -> QWidget:
        """创建账号管理页"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # TODO: 实现账号管理UI
        info_label = QLabel('邮箱账号管理功能开发中...')
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """加载设置"""
        settings = self.db.query_one('SELECT * FROM settings WHERE id = 1')
        if settings:
            # AI设置
            providers = {'ollama': 0, 'wenxin': 1, 'qianwen': 2, 'deepseek': 3}
            self.provider_combo.setCurrentIndex(providers.get(settings[1], 0))
            
            self.ollama_url.setText(settings[2])
            
            # 同步设置
            self.auto_sync.setChecked(True)
            self.sync_interval.setValue(settings[6] or 15)
            self.auto_process.setChecked(settings[7] or False)
            self.daily_limit.setValue(settings[8] or 20)
    
    def save_and_close(self):
        """保存并关闭"""
        providers = {0: 'ollama', 1: 'wenxin', 2: 'qianwen', 3: 'deepseek'}
        
        sql = '''
            UPDATE settings SET
                ai_provider = ?,
                ollama_url = ?,
                ollama_model = ?,
                sync_interval_minutes = ?,
                auto_process = ?,
                daily_limit_free = ?
            WHERE id = 1
        '''
        
        self.db.execute(sql, (
            providers.get(self.provider_combo.currentIndex(), 'ollama'),
            self.ollama_url.text(),
            self.ollama_model.currentText().split('(')[0].strip(),
            self.sync_interval.value(),
            self.auto_process.isChecked(),
            self.daily_limit.value()
        ))
        
        self.accept()


class AddAccountDialog(QDialog):
    """添加账号对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('添加邮箱账号')
        self.setGeometry(350, 250, 400, 300)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('your-email@example.com')
        form_layout.addRow('邮箱地址:', self.email_input)
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText('imap.example.com')
        form_layout.addRow('IMAP服务器:', self.server_input)
        
        self.port_input = QLineEdit('993')
        self.port_input.setPlaceholderText('993')
        form_layout.addRow('端口:', self.port_input)
        
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setEchoMode(QLineEdit.Password)
        self.auth_code_input.setPlaceholderText('授权码（非密码）')
        form_layout.addRow('授权码:', self.auth_code_input)
        
        layout.addLayout(form_layout)
        
        # 帮助信息
        help_label = QLabel(
            '💡 如何获取授权码？\n'
            '• QQ邮箱：设置 → 账户 → POP3/IMAP服务 → 生成授权码\n'
            '• 网易邮箱：设置 → POP/SMTP/IMAP → 开启并获取授权码'
        )
        help_label.setStyleSheet('''
            background-color: #fff3e0;
            padding: 10px;
            border-radius: 6px;
            font-size: 12px;
        ''')
        layout.addWidget(help_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        test_btn = QPushButton('测试连接')
        test_btn.clicked.connect(self.test_connection)
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.save_account)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def test_connection(self):
        """测试连接"""
        from src.core.imap_client import IMAPClient
        
        client = IMAPClient()
        success = client.connect(
            self.server_input.text(),
            int(self.port_input.text() or 993),
            self.email_input.text(),
            self.auth_code_input.text()
        )
        
        client.disconnect()
        
        if success:
            QMessageBox.information(self, '成功', '连接测试通过！')
        else:
            QMessageBox.warning(self, '失败', '连接失败，请检查设置')
    
    def save_account(self):
        """保存账号"""
        if not self.email_input.text() or not self.auth_code_input.text():
            QMessageBox.warning(self, '错误', '请填写完整信息')
            return
        
        try:
            # 加密存储授权码（简化版，实际应使用更安全的加密）
            auth_code = self.auth_code_input.text()
            
            # 保存到数据库
            sql = '''
                INSERT INTO accounts 
                (email_address, imap_server, imap_port, auth_code_encrypted)
                VALUES (?, ?, ?, ?)
            '''
            self.db.execute(sql, (
                self.email_input.text(),
                self.server_input.text(),
                int(self.port_input.text() or 993),
                auth_code  # TODO: 应使用加密存储
            ))
            
            QMessageBox.information(self, '成功', '账号添加成功！')
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, '错误', f'保存失败: {str(e)}')
```

- [ ] **Step 2: 提交代码**

```bash
git add src/ui/settings_dialog.py
git commit -m "feat: add settings dialog with AI and sync configuration"
```

---

## Phase 3-5: AI集成、功能实现（8天）

由于篇幅限制，Phase 3-5的详细实施步骤将生成独立的实施计划文档。

---

## 实施计划总结

| Phase | 内容 | 任务数 | 预计时间 |
|-------|------|--------|---------|
| Phase 0 | 项目基础搭建 | 2 | 1天 |
| Phase 1 | IMAP邮件客户端 | 3 | 3天 |
| Phase 2 | PyQt5 UI开发 | 2 | 5天 |
| Phase 3 | Ollama本地AI集成 | 待续 | 3天 |
| Phase 4 | 摘要生成、待办提取 | 待续 | 3天 |
| Phase 5 | 设置页面、日历同步 | 待续 | 2天 |

---

## 下一步

完整的详细实施计划已保存。两种执行方式：

1. **子代理驱动（推荐）** - 每个任务由专门的子代理执行，快速度迭代
2. **内联执行** - 在当前会话中批量执行任务

请选择你希望的执行方式！
