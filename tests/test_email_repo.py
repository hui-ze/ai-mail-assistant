# tests/test_email_repo.py
"""
邮件仓储模块测试
"""
import pytest
import os
import tempfile
from datetime import datetime
from src.data.database import Database
from src.data.email_repo import EmailRepo
from src.core.imap_client import EmailData


class TestEmailRepo:
    """邮件仓储测试类"""
    
    @pytest.fixture
    def temp_db(self):
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
    def email_repo(self, temp_db):
        """创建邮件仓储"""
        return EmailRepo(temp_db)
    
    def test_save_email(self, email_repo, temp_db):
        """测试保存邮件"""
        email = EmailData(
            uid='test_uid_123',
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
        saved = temp_db.query_one(
            'SELECT subject, sender FROM emails WHERE id = ?',
            (email_id,)
        )
        assert saved[0] == 'Test Subject'
        assert saved[1] == 'Sender Name'
    
    def test_save_emails_batch(self, email_repo):
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
    
    def test_get_email_by_id(self, email_repo):
        """测试根据ID获取邮件"""
        email = EmailData(
            uid='get_by_id_test',
            subject='Get By ID Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX'
        )
        email_id = email_repo.save_email(email, account_id=1)
        
        result = email_repo.get_email_by_id(email_id)
        assert result is not None
        assert result['subject'] == 'Get By ID Test'
        assert result['uid'] == 'get_by_id_test'
    
    def test_get_email_by_uid(self, email_repo):
        """测试根据UID获取邮件"""
        email = EmailData(
            uid='get_by_uid_test',
            subject='Get By UID Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX'
        )
        email_repo.save_email(email, account_id=1)
        
        result = email_repo.get_email_by_uid('get_by_uid_test', 1)
        assert result is not None
        assert result['subject'] == 'Get By UID Test'
    
    def test_mark_as_processed(self, email_repo, temp_db):
        """测试标记已处理"""
        email = EmailData(
            uid='processed_test',
            subject='Processed Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX'
        )
        email_id = email_repo.save_email(email, account_id=1)
        
        email_repo.mark_as_processed(email_id)
        
        result = temp_db.query_one(
            'SELECT processed FROM emails WHERE id = ?',
            (email_id,)
        )
        assert result[0] == 1
    
    def test_mark_as_read(self, email_repo, temp_db):
        """测试标记已读"""
        email = EmailData(
            uid='read_test',
            subject='Read Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX',
            is_read=False
        )
        email_id = email_repo.save_email(email, account_id=1)
        
        email_repo.mark_as_read(email_id)
        
        result = temp_db.query_one(
            'SELECT is_read FROM emails WHERE id = ?',
            (email_id,)
        )
        assert result[0] == 1
    
    def test_search_emails(self, email_repo):
        """测试搜索邮件"""
        # 保存包含关键词的邮件
        email = EmailData(
            uid='search_test',
            subject='Important Meeting',
            sender='boss@company.com',
            sender_email='boss@company.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Please attend the meeting tomorrow',
            folder='INBOX'
        )
        email_repo.save_email(email, account_id=1)
        
        # 搜索
        results = email_repo.search_emails(1, 'Meeting')
        assert len(results) >= 1
        assert any('Meeting' in r['subject'] for r in results)
    
    def test_get_unprocessed_emails(self, email_repo):
        """测试获取未处理邮件"""
        # 保存邮件（默认未处理）
        email = EmailData(
            uid='unprocessed_test',
            subject='Unprocessed Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX'
        )
        email_repo.save_email(email, account_id=1)
        
        results = email_repo.get_unprocessed_emails(1)
        assert len(results) >= 1
        assert all(not r['processed'] for r in results)
    
    def test_delete_email(self, email_repo, temp_db):
        """测试删除邮件"""
        email = EmailData(
            uid='delete_test',
            subject='Delete Test',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Body',
            folder='INBOX'
        )
        email_id = email_repo.save_email(email, account_id=1)
        
        email_repo.delete_email(email_id)
        
        result = temp_db.query_one(
            'SELECT * FROM emails WHERE id = ?',
            (email_id,)
        )
        assert result is None
    
    def test_get_email_count(self, email_repo):
        """测试获取邮件数量"""
        # 保存多封邮件
        for i in range(3):
            email = EmailData(
                uid=f'count_test_{i}',
                subject=f'Count Test {i}',
                sender='Sender',
                sender_email='sender@example.com',
                recipients='test@example.com',
                date=datetime.now(),
                body_text='Body',
                folder='INBOX'
            )
            email_repo.save_email(email, account_id=1)
        
        count = email_repo.get_email_count(1)
        assert count >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
