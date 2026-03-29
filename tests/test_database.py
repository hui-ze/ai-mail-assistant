# tests/test_database.py
"""
数据库模块测试
"""
import pytest
import os
import tempfile
from src.data.database import Database


class TestDatabase:
    """数据库测试类"""
    
    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        db = Database(path)
        yield db
        # 清理
        try:
            os.unlink(path)
        except:
            pass
        try:
            os.unlink(f"{path}.bak")
        except:
            pass
    
    def test_init_db_creates_all_tables(self, temp_db):
        """测试数据库初始化创建所有表"""
        result = temp_db.query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [r[0] for r in result]
        
        assert 'accounts' in table_names
        assert 'emails' in table_names
        assert 'summaries' in table_names
        assert 'todos' in table_names
        assert 'settings' in table_names
    
    def test_insert_account(self, temp_db):
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
    
    def test_query_account(self, temp_db):
        """测试查询账号"""
        # 插入测试数据
        temp_db.execute(
            'INSERT INTO accounts (email_address, imap_server) VALUES (?, ?)',
            ('query@test.com', 'imap.test.com')
        )
        
        # 查询
        result = temp_db.query_one(
            'SELECT * FROM accounts WHERE email_address = ?',
            ('query@test.com',)
        )
        assert result is not None
        assert result['email_address'] == 'query@test.com'
    
    def test_insert_email(self, temp_db):
        """测试插入邮件"""
        # 先插入账号
        account_id = temp_db.execute(
            'INSERT INTO accounts (email_address, imap_server) VALUES (?, ?)',
            ('email@test.com', 'imap.test.com')
        )
        
        # 插入邮件
        email_sql = '''
            INSERT INTO emails 
            (uid, account_id, subject, sender, sender_email, recipients, date, body_text, folder)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        import datetime
        email_id = temp_db.execute(email_sql, (
            'test_uid_123',
            account_id,
            'Test Subject',
            'Sender Name',
            'sender@test.com',
            'email@test.com',
            datetime.datetime.now(),
            'Test body content',
            'INBOX'
        ))
        
        assert email_id > 0
        
        # 验证
        result = temp_db.query_one(
            'SELECT subject FROM emails WHERE id = ?',
            (email_id,)
        )
        assert result[0] == 'Test Subject'
    
    def test_insert_todo(self, temp_db):
        """测试插入待办"""
        todo_sql = '''
            INSERT INTO todos (content, priority)
            VALUES (?, ?)
        '''
        todo_id = temp_db.execute(todo_sql, ('完成报告', '高'))
        assert todo_id > 0
        
        # 验证
        result = temp_db.query_one(
            'SELECT content, priority FROM todos WHERE id = ?',
            (todo_id,)
        )
        assert result[0] == '完成报告'
        assert result[1] == '高'
    
    def test_update_todo_completed(self, temp_db):
        """测试更新待办状态"""
        # 插入待办
        todo_id = temp_db.execute(
            'INSERT INTO todos (content) VALUES (?)',
            ('Test Todo',)
        )
        
        # 更新为已完成
        temp_db.execute(
            'UPDATE todos SET completed = 1 WHERE id = ?',
            (todo_id,)
        )
        
        # 验证
        result = temp_db.query_one(
            'SELECT completed FROM todos WHERE id = ?',
            (todo_id,)
        )
        assert result[0] == 1
    
    def test_delete_todo(self, temp_db):
        """测试删除待办"""
        # 插入待办
        todo_id = temp_db.execute(
            'INSERT INTO todos (content) VALUES (?)',
            ('To Delete',)
        )
        
        # 删除
        temp_db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        
        # 验证
        result = temp_db.query_one(
            'SELECT * FROM todos WHERE id = ?',
            (todo_id,)
        )
        assert result is None
    
    def test_settings_initialized(self, temp_db):
        """测试设置表已初始化"""
        result = temp_db.query_one('SELECT * FROM settings WHERE id = 1')
        assert result is not None
        assert result['ai_provider'] == 'ollama'
        assert result['sync_interval_minutes'] == 15
    
    def test_query_returns_list(self, temp_db):
        """测试query返回列表"""
        # 插入多条数据
        for i in range(3):
            temp_db.execute(
                'INSERT INTO todos (content) VALUES (?)',
                (f'Todo {i}',)
            )
        
        results = temp_db.query('SELECT * FROM todos')
        assert len(results) == 3
    
    def test_query_one_returns_none_for_empty(self, temp_db):
        """测试query_one对空结果返回None"""
        result = temp_db.query_one('SELECT * FROM todos WHERE id = 9999')
        assert result is None
    
    def test_execute_many(self, temp_db):
        """测试批量插入"""
        sql = 'INSERT INTO todos (content) VALUES (?)'
        params = [('Todo 1',), ('Todo 2',), ('Todo 3',)]
        
        count = temp_db.execute_many(sql, params)
        assert count == 3
        
        results = temp_db.query('SELECT * FROM todos')
        assert len(results) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
