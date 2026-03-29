# src/data/database.py
"""
数据库模块
SQLite数据库管理，支持账号、邮件、摘要、待办等数据存储
"""
import sqlite3
import os
from typing import Optional, List, Tuple
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('database', get_log_dir())


class Database:
    """SQLite数据库管理类"""

    # 类级别的共享连接（用于内存数据库）
    _shared_connection: Optional[sqlite3.Connection] = None

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认使用AppData目录
        """
        if db_path is None:
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            data_dir = os.path.join(app_data, 'ai-mail-assistant', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'app.db')

        self.db_path = db_path
        self._is_memory = db_path == ':memory:' or db_path.startswith(':memory:')

        logger.info(f"Database path: {self.db_path}")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接

        Returns:
            SQLite连接对象
        """
        # 对于内存数据库，使用共享连接
        if self._is_memory:
            if Database._shared_connection is None:
                Database._shared_connection = sqlite3.connect(self.db_path, check_same_thread=False)
                Database._shared_connection.row_factory = sqlite3.Row
            return Database._shared_connection

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持列名访问
        return conn
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
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
                    uid VARCHAR(255) NOT NULL,
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
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    UNIQUE(uid, account_id)
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

            # AI设置表（JSON格式存储）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # AI使用记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100),
                    tokens_used INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 用户画像表（Phase 6 新增）
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

            # 初始化用户画像默认记录
            cursor.execute('INSERT OR IGNORE INTO user_profile (id) VALUES (1)')

            # 为 todos 表添加归属相关字段（Phase 6 新增）
            try:
                cursor.execute('ALTER TABLE todos ADD COLUMN assignee VARCHAR(100)')
            except:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE todos ADD COLUMN assign_type VARCHAR(20)')
            except:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE todos ADD COLUMN confidence REAL')
            except:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE todos ADD COLUMN assign_reason TEXT')
            except:
                pass  # 字段已存在

            # 迁移：为 settings 表添加 value 列（兼容旧数据库）
            try:
                cursor.execute('ALTER TABLE settings ADD COLUMN value TEXT')
                logger.info("settings 表已添加 value 列（数据库迁移）")
            except:
                pass  # 列已存在，忽略
            
            # 迁移：为 todos 表添加 completed_at 列（记录完成时间）
            try:
                cursor.execute('ALTER TABLE todos ADD COLUMN completed_at DATETIME')
                logger.info("todos 表已添加 completed_at 列（数据库迁移）")
            except:
                pass  # 列已存在，忽略

            # 初始化默认设置
            cursor.execute('INSERT OR IGNORE INTO settings (id) VALUES (1)')

            # Phase 7: 部门协作功能表
            # 部门表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    share_path VARCHAR(500) NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 团队成员表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    role VARCHAR(100),
                    is_leader BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
                    UNIQUE(email, department_id)
                )
            ''')
            
            # 同步记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    sync_type VARCHAR(20) NOT NULL,
                    file_path VARCHAR(500),
                    todo_count INTEGER DEFAULT 0,
                    sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'success',
                    error_message TEXT,
                    FOREIGN KEY (member_id) REFERENCES team_members(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_members_department ON team_members(department_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_members_email ON team_members(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_records_member ON sync_records(member_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_records_time ON sync_records(sync_time)')

            # Phase 8: 待办分配与提醒功能表
            # 待办分配表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS todo_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    todo_id INTEGER NOT NULL,
                    from_member_id INTEGER NOT NULL,
                    to_member_id INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    message TEXT,
                    response_message TEXT,
                    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    responded_at DATETIME,
                    FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_member_id) REFERENCES team_members(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_member_id) REFERENCES team_members(id) ON DELETE CASCADE
                )
            ''')
            
            # 提醒表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    todo_id INTEGER,
                    member_id INTEGER NOT NULL,
                    reminder_type VARCHAR(50) NOT NULL,
                    remind_at DATETIME NOT NULL,
                    is_sent BOOLEAN DEFAULT 0,
                    message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE,
                    FOREIGN KEY (member_id) REFERENCES team_members(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assignments_todo ON todo_assignments(todo_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assignments_to_member ON todo_assignments(to_member_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assignments_status ON todo_assignments(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_member ON reminders(member_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(remind_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_sent ON reminders(is_sent)')

            conn.commit()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            conn.rollback()
            raise
        finally:
            if not self._is_memory:
                conn.close()
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """
        执行SQL语句（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            插入记录的ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            result = cursor.lastrowid
            logger.debug(f"SQL executed: {sql[:50]}..., params: {params}")
            return result if result else 0
        except Exception as e:
            logger.error(f"SQL execution failed: {e}, sql: {sql}")
            conn.rollback()
            raise
        finally:
            if not self._is_memory:
                conn.close()

    def query(self, sql: str, params: tuple = ()) -> List[Tuple]:
        """
        执行查询SQL

        Args:
            sql: SELECT语句
            params: 参数元组

        Returns:
            查询结果列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            logger.debug(f"Query executed: {sql[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}, sql: {sql}")
            raise
        finally:
            if not self._is_memory:
                conn.close()
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[Tuple]:
        """
        查询单条记录
        
        Args:
            sql: SELECT语句
            params: 参数元组
        
        Returns:
            单条记录，不存在则返回None
        """
        results = self.query(sql, params)
        return results[0] if results else None
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行SQL

        Args:
            sql: SQL语句
            params_list: 参数列表

        Returns:
            影响的行数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, params_list)
            conn.commit()
            result = cursor.rowcount
            logger.debug(f"Batch executed: {len(params_list)} rows affected")
            return result
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            conn.rollback()
            raise
        finally:
            if not self._is_memory:
                conn.close()
    
    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """
        创建数据库备份
        
        Args:
            backup_path: 备份文件路径，默认在原路径加.bak后缀
        
        Returns:
            备份文件路径
        """
        if backup_path is None:
            backup_path = f"{self.db_path}.bak"
        
        conn = self._get_connection()
        try:
            with open(backup_path, 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        finally:
            conn.close()
