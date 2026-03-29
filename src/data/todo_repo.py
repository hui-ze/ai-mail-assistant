# src/data/todo_repo.py
"""
待办数据仓储模块
负责待办事项的数据库操作
"""
from typing import Optional, List
from dataclasses import dataclass
from src.data.database import Database


@dataclass
class TodoItem:
    """待办事项数据类"""
    id: int
    summary_id: int
    email_id: int
    content: str  # 待办内容（与数据库列名一致）
    is_completed: bool
    priority: str  # 'high', 'medium', 'low'
    due_date: str
    calendar_event_id: str
    assignee: str = None  # 归属人（Phase 6 新增）
    assign_type: str = None  # 归属类型（Phase 6 新增）
    confidence: float = None  # 归属置信度（Phase 6 新增）
    assign_reason: str = None  # 归属理由（Phase 6 新增）


class TodoRepo:
    """待办数据仓储类"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_todo(self, content: str, email_id: int = None, 
                    summary_id: int = None, priority: str = '中',
                    due_date: str = None,
                    assignee: str = None, assign_type: str = None,
                    confidence: float = None, assign_reason: str = None) -> int:
        """
        创建待办事项
        
        Args:
            content: 待办内容
            email_id: 关联邮件ID（可选）
            summary_id: 关联摘要ID（可选）
            priority: 优先级 ('高', '中', '低')
            due_date: 截止日期（可选）
            assignee: 归属人（Phase 6 新增）
            assign_type: 归属类型 ('self', 'other', 'team', 'unknown')（Phase 6 新增）
            confidence: 归属置信度（Phase 6 新增）
            assign_reason: 归属理由（Phase 6 新增）
        
        Returns:
            插入记录的ID
        """
        sql = '''
            INSERT INTO todos 
            (content, email_id, summary_id, priority, due_date, assignee, assign_type, confidence, assign_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute(sql, (content, email_id, summary_id, priority, due_date, 
                                     assignee, assign_type, confidence, assign_reason))
    
    def get_all_todos(self, completed: bool = None) -> List[dict]:
        """
        获取所有待办事项
        
        Args:
            completed: 筛选条件，True只返回已完成的，False只返回未完成的，None返回全部
        
        Returns:
            待办事项列表
        """
        if completed is None:
            sql = 'SELECT * FROM todos ORDER BY created_at DESC'
            results = self.db.query(sql)
        else:
            sql = 'SELECT * FROM todos WHERE completed = ? ORDER BY created_at DESC'
            results = self.db.query(sql, (1 if completed else 0,))
        
        return [self._row_to_dict(r) for r in results]
    
    def get_todo_by_id(self, todo_id: int) -> Optional[dict]:
        """
        根据ID获取待办
        
        Args:
            todo_id: 待办ID
        
        Returns:
            待办字典，不存在则返回None
        """
        sql = 'SELECT * FROM todos WHERE id = ?'
        result = self.db.query_one(sql, (todo_id,))
        if result:
            return self._row_to_dict(result)
        return None
    
    def get_todos_by_email(self, email_id: int) -> List[dict]:
        """
        获取邮件关联的待办事项
        
        Args:
            email_id: 邮件ID
        
        Returns:
            待办事项列表
        """
        sql = 'SELECT * FROM todos WHERE email_id = ? ORDER BY created_at DESC'
        results = self.db.query(sql, (email_id,))
        return [self._row_to_dict(r) for r in results]
    
    def mark_completed(self, todo_id: int, completed: bool = True):
        """
        标记待办完成状态
        
        Args:
            todo_id: 待办ID
            completed: 是否完成
        """
        sql = 'UPDATE todos SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        self.db.execute(sql, (1 if completed else 0, todo_id))
    
    def update_todo(self, todo_id: int, content: str = None, 
                    priority: str = None, due_date: str = None,
                    assignee: str = None, assign_type: str = None):
        """
        更新待办事项
        
        Args:
            todo_id: 待办ID
            content: 新内容（可选）
            priority: 新优先级（可选）
            due_date: 新截止日期（可选）
            assignee: 归属人（可选，Phase 8 新增）
            assign_type: 归属类型（可选，Phase 8 新增）
        """
        updates = []
        params = []
        
        if content is not None:
            updates.append('content = ?')
            params.append(content)
        if priority is not None:
            updates.append('priority = ?')
            params.append(priority)
        if due_date is not None:
            updates.append('due_date = ?')
            params.append(due_date)
        if assignee is not None:
            updates.append('assignee = ?')
            params.append(assignee)
        if assign_type is not None:
            updates.append('assign_type = ?')
            params.append(assign_type)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(todo_id)
            sql = f'UPDATE todos SET {", ".join(updates)} WHERE id = ?'
            self.db.execute(sql, tuple(params))
    
    def delete_todo(self, todo_id: int):
        """
        删除待办事项
        
        Args:
            todo_id: 待办ID
        """
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
            'calendar_event_id': row[7],
            'created_at': row[8] if len(row) > 8 else None,
            'updated_at': row[9] if len(row) > 9 else None,
            # Phase 6 新增字段
            'assignee': row[10] if len(row) > 10 else None,
            'assign_type': row[11] if len(row) > 11 else None,
            'confidence': row[12] if len(row) > 12 else None,
            'assign_reason': row[13] if len(row) > 13 else None
        }

    def _row_to_item(self, row) -> TodoItem:
        """行转TodoItem"""
        return TodoItem(
            id=row[0],
            summary_id=row[1],
            email_id=row[2],
            content=row[3],  # 数据库列名为 content
            is_completed=bool(row[4]),
            priority=self._normalize_priority(row[5]),
            due_date=row[6],
            calendar_event_id=row[7],
            # Phase 6 新增字段
            assignee=row[10] if len(row) > 10 else None,
            assign_type=row[11] if len(row) > 11 else None,
            confidence=row[12] if len(row) > 12 else None,
            assign_reason=row[13] if len(row) > 13 else None
        )

    def _normalize_priority(self, priority: str) -> str:
        """标准化优先级"""
        priority_map = {
            '高': 'high', '高优先级': 'high',
            '中': 'medium', '普通': 'medium',
            '低': 'low', '低优先级': 'low'
        }
        return priority_map.get(priority, 'medium')

    def get_todos_by_email_id(self, email_id: int) -> List[TodoItem]:
        """获取邮件关联的待办事项（返回TodoItem列表）"""
        sql = 'SELECT * FROM todos WHERE email_id = ? ORDER BY created_at DESC'
        results = self.db.query(sql, (email_id,))
        return [self._row_to_item(r) for r in results]

    def get_all_todos_as_items(self) -> List[TodoItem]:
        """获取所有待办事项（返回TodoItem列表）"""
        sql = 'SELECT * FROM todos ORDER BY created_at DESC'
        results = self.db.query(sql)
        return [self._row_to_item(r) for r in results]

    def update_todo_status(self, todo_id: int, is_completed: bool):
        """更新待办完成状态"""
        sql = 'UPDATE todos SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        self.db.execute(sql, (1 if is_completed else 0, todo_id))
