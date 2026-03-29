# src/data/email_repo.py
"""
邮件数据仓储模块
负责邮件数据的数据库操作
"""
from typing import List, Optional
from datetime import datetime
from src.core.imap_client import EmailData
from src.data.database import Database
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('email_repo', get_log_dir())


class EmailRepo:
    """邮件数据仓储类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_email(self, email: EmailData, account_id: int) -> int:
        """
        保存邮件到数据库
        
        Args:
            email: 邮件数据对象
            account_id: 账号ID
        
        Returns:
            插入记录的ID
        """
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
            0  # processed = False
        ))
        
        logger.debug(f"Saved email: {email.subject}, id={email_id}")
        return email_id
    
    def save_emails_batch(self, emails: List[EmailData], account_id: int) -> int:
        """
        批量保存邮件
        
        Args:
            emails: 邮件列表
            account_id: 账号ID
        
        Returns:
            保存的邮件数量
        """
        count = 0
        for email in emails:
            try:
                self.save_email(email, account_id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to save email {email.uid}: {e}")
        logger.info(f"Batch saved {count}/{len(emails)} emails")
        return count
    
    def get_email_by_id(self, email_id: int) -> Optional[dict]:
        """
        根据ID获取邮件
        
        Args:
            email_id: 邮件ID
        
        Returns:
            邮件字典，不存在则返回None
        """
        sql = 'SELECT * FROM emails WHERE id = ?'
        result = self.db.query_one(sql, (email_id,))
        if result:
            return self._row_to_dict(result)
        return None
    
    def get_email_by_uid(self, uid: str, account_id: int) -> Optional[dict]:
        """
        根据UID获取邮件
        
        Args:
            uid: 邮件UID
            account_id: 账号ID
        
        Returns:
            邮件字典，不存在则返回None
        """
        sql = 'SELECT * FROM emails WHERE uid = ? AND account_id = ?'
        result = self.db.query_one(sql, (uid, account_id))
        if result:
            return self._row_to_dict(result)
        return None
    
    def get_emails_by_account(
        self,
        account_id: int,
        folder: str = 'INBOX',
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        获取账号的邮件列表
        
        Args:
            account_id: 账号ID
            folder: 文件夹名称
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            邮件列表
        """
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? AND folder = ?
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        '''
        results = self.db.query(sql, (account_id, folder, limit, offset))
        return [self._row_to_dict(r) for r in results]
    
    def get_recent_emails(
        self,
        account_id: int,
        days: int = 7,
        limit: int = 100
    ) -> List[dict]:
        """
        获取最近N天的邮件
        
        Args:
            account_id: 账号ID
            days: 天数
            limit: 返回数量限制
        
        Returns:
            邮件列表
        """
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? 
            AND date >= datetime('now', '-' || ? || ' days')
            ORDER BY date DESC
            LIMIT ?
        '''
        results = self.db.query(sql, (account_id, days, limit))
        return [self._row_to_dict(r) for r in results]
    
    def get_unprocessed_emails(self, account_id: int, limit: int = 20) -> List[dict]:
        """
        获取未处理的邮件
        
        Args:
            account_id: 账号ID
            limit: 返回数量限制
        
        Returns:
            未处理邮件列表
        """
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? AND processed = 0
            ORDER BY date DESC
            LIMIT ?
        '''
        results = self.db.query(sql, (account_id, limit))
        return [self._row_to_dict(r) for r in results]
    
    def get_unread_emails(self, account_id: int, limit: int = 50) -> List[dict]:
        """
        获取未读邮件
        
        Args:
            account_id: 账号ID
            limit: 返回数量限制
        
        Returns:
            未读邮件列表
        """
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? AND is_read = 0
            ORDER BY date DESC
            LIMIT ?
        '''
        results = self.db.query(sql, (account_id, limit))
        return [self._row_to_dict(r) for r in results]
    
    def mark_as_processed(self, email_id: int):
        """
        标记邮件已处理
        
        Args:
            email_id: 邮件ID
        """
        self.db.execute('UPDATE emails SET processed = 1 WHERE id = ?', (email_id,))
        logger.debug(f"Marked email {email_id} as processed")
    
    def mark_as_read(self, email_id: int):
        """
        标记邮件已读
        
        Args:
            email_id: 邮件ID
        """
        self.db.execute('UPDATE emails SET is_read = 1 WHERE id = ?', (email_id,))
        logger.debug(f"Marked email {email_id} as read")
    
    def mark_as_unread(self, email_id: int):
        """
        标记邮件未读
        
        Args:
            email_id: 邮件ID
        """
        self.db.execute('UPDATE emails SET is_read = 0 WHERE id = ?', (email_id,))
        logger.debug(f"Marked email {email_id} as unread")
    
    def search_emails(
        self,
        account_id: int,
        keyword: str,
        folder: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        搜索邮件
        
        Args:
            account_id: 账号ID
            keyword: 搜索关键词
            folder: 指定文件夹（可选）
            limit: 返回数量限制
        
        Returns:
            匹配的邮件列表
        """
        sql = '''
            SELECT * FROM emails 
            WHERE account_id = ? 
            AND (subject LIKE ? OR sender LIKE ? OR body_text LIKE ?)
        '''
        params = (account_id, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
        
        if folder:
            sql += ' AND folder = ?'
            params += (folder,)
        
        sql += ' ORDER BY date DESC LIMIT ?'
        params += (limit,)
        
        results = self.db.query(sql, params)
        return [self._row_to_dict(r) for r in results]
    
    def delete_email(self, email_id: int):
        """
        删除邮件
        
        Args:
            email_id: 邮件ID
        """
        # 先删除关联的摘要和待办
        self.db.execute('DELETE FROM summaries WHERE email_id = ?', (email_id,))
        self.db.execute('DELETE FROM todos WHERE email_id = ?', (email_id,))
        # 再删除邮件
        self.db.execute('DELETE FROM emails WHERE id = ?', (email_id,))
        logger.debug(f"Deleted email {email_id}")
    
    def get_email_count(self, account_id: int, folder: str = None) -> int:
        """
        获取邮件数量
        
        Args:
            account_id: 账号ID
            folder: 文件夹名称（可选）
        
        Returns:
            邮件数量
        """
        if folder:
            sql = 'SELECT COUNT(*) FROM emails WHERE account_id = ? AND folder = ?'
            result = self.db.query_one(sql, (account_id, folder))
        else:
            sql = 'SELECT COUNT(*) FROM emails WHERE account_id = ?'
            result = self.db.query_one(sql, (account_id,))
        
        return result[0] if result else 0
    
    def get_unprocessed_count(self, account_id: int) -> int:
        """
        获取未处理邮件数量
        
        Args:
            account_id: 账号ID
        
        Returns:
            未处理邮件数量
        """
        sql = 'SELECT COUNT(*) FROM emails WHERE account_id = ? AND processed = 0'
        result = self.db.query_one(sql, (account_id,))
        return result[0] if result else 0
    
    def _row_to_dict(self, row) -> dict:
        """行转字典"""
        if hasattr(row, '_row'):
            # sqlite3.Row对象
            return {
                'id': row[0],
                'uid': row[1],
                'account_id': row[2],
                'subject': row[3],
                'sender': row[4],
                'sender_email': row[5],
                'recipients': row[6],
                'date': row[7],
                'body_text': row[8],
                'body_html': row[9],
                'folder': row[10],
                'is_read': bool(row[11]),
                'processed': bool(row[12])
            }
        else:
            # 普通tuple
            return {
                'id': row[0],
                'uid': row[1],
                'account_id': row[2],
                'subject': row[3],
                'sender': row[4],
                'sender_email': row[5],
                'recipients': row[6],
                'date': row[7],
                'body_text': row[8],
                'body_html': row[9],
                'folder': row[10],
                'is_read': bool(row[11]),
                'processed': bool(row[12])
            }
