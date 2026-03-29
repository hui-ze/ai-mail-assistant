# src/data/summary_repo.py
"""
摘要数据仓储模块
负责摘要数据的数据库操作
"""
from typing import Optional, List
from dataclasses import dataclass
from src.data.database import Database


@dataclass
class SummaryResult:
    """摘要结果数据类"""
    id: int
    email_id: int
    title: str
    summary_text: str
    todos_json: str
    model_used: str
    tokens_used: int
    created_at: str


class SummaryRepo:
    """摘要数据仓储类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_summary(self, email_id: int, summary_text: str, 
                     todos_json: str, model_used: str, tokens_used: int) -> int:
        """
        保存邮件摘要
        
        Args:
            email_id: 邮件ID
            summary_text: 摘要文本
            todos_json: 待办事项JSON字符串
            model_used: 使用的AI模型
            tokens_used: 使用的token数量
        
        Returns:
            插入记录的ID
        """
        sql = '''
            INSERT INTO summaries 
            (email_id, summary_text, todos_json, model_used, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db.execute(sql, (email_id, summary_text, todos_json, 
                                    model_used, tokens_used))
    
    def get_summary_by_email(self, email_id: int) -> Optional[dict]:
        """
        根据邮件ID获取摘要

        Args:
            email_id: 邮件ID

        Returns:
            摘要字典，不存在则返回None
        """
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

    def get_summary_by_email_id(self, email_id: int) -> Optional[SummaryResult]:
        """根据邮件ID获取摘要（返回SummaryResult对象）"""
        sql = 'SELECT * FROM summaries WHERE email_id = ? ORDER BY created_at DESC LIMIT 1'
        result = self.db.query_one(sql, (email_id,))
        if result:
            # 提取标题（取摘要文本前50字符）
            summary_text = result[2] or ""
            title = summary_text[:50] + "..." if len(summary_text) > 50 else summary_text

            return SummaryResult(
                id=result[0],
                email_id=result[1],
                title=title,
                summary_text=result[2],
                todos_json=result[3],
                model_used=result[4],
                tokens_used=result[5],
                created_at=result[6]
            )
        return None
    
    def get_summaries_by_account(self, account_id: int, limit: int = 50) -> List[dict]:
        """
        获取账号的所有摘要
        
        Args:
            account_id: 账号ID
            limit: 返回数量限制
        
        Returns:
            摘要列表
        """
        sql = '''
            SELECT s.* FROM summaries s
            JOIN emails e ON s.email_id = e.id
            WHERE e.account_id = ?
            ORDER BY s.created_at DESC
            LIMIT ?
        '''
        results = self.db.query(sql, (account_id, limit))
        return [self._row_to_dict(r) for r in results]
    
    def delete_summary(self, summary_id: int):
        """
        删除摘要
        
        Args:
            summary_id: 摘要ID
        """
        sql = 'DELETE FROM summaries WHERE id = ?'
        self.db.execute(sql, (summary_id,))
    
    def _row_to_dict(self, row) -> dict:
        """行转字典"""
        return {
            'id': row[0],
            'email_id': row[1],
            'summary_text': row[2],
            'todos_json': row[3],
            'model_used': row[4],
            'tokens_used': row[5],
            'created_at': row[6]
        }
