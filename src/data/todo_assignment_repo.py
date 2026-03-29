# src/data/todo_assignment_repo.py
"""
待办分配数据访问层
Phase 8: 待办分配与提醒功能
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from src.data.database import Database
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('todo_assignment_repo', get_log_dir())


@dataclass
class TodoAssignment:
    """待办分配数据类"""
    id: Optional[int] = None
    todo_id: int = 0
    from_member_id: int = 0
    to_member_id: int = 0
    status: str = "pending"  # pending/accepted/rejected/completed
    message: str = ""
    response_message: str = ""
    assigned_at: Optional[str] = None
    responded_at: Optional[str] = None


class TodoAssignmentRepo:
    """待办分配数据访问类"""
    
    def __init__(self, db: Database):
        """
        初始化分配仓库
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def create(self, todo_id: int, from_member_id: int, to_member_id: int, 
               message: str = "") -> int:
        """
        创建待办分配
        
        Args:
            todo_id: 待办ID
            from_member_id: 分配人ID
            to_member_id: 接收人ID
            message: 分配说明
        
        Returns:
            创建的分配ID
        """
        sql = '''
            INSERT INTO todo_assignments (todo_id, from_member_id, to_member_id, message)
            VALUES (?, ?, ?, ?)
        '''
        assignment_id = self.db.execute(sql, (todo_id, from_member_id, to_member_id, message))
        logger.info(f"Created assignment: todo {todo_id} from {from_member_id} to {to_member_id}")
        return assignment_id
    
    def get_by_id(self, assignment_id: int) -> Optional[TodoAssignment]:
        """
        根据ID获取分配
        
        Args:
            assignment_id: 分配ID
        
        Returns:
            分配对象,不存在返回None
        """
        sql = 'SELECT * FROM todo_assignments WHERE id = ?'
        row = self.db.query_one(sql, (assignment_id,))
        if row:
            return TodoAssignment(
                id=row['id'],
                todo_id=row['todo_id'],
                from_member_id=row['from_member_id'],
                to_member_id=row['to_member_id'],
                status=row['status'],
                message=row['message'] or "",
                response_message=row['response_message'] or "",
                assigned_at=row['assigned_at'],
                responded_at=row['responded_at']
            )
        return None
    
    def get_pending_by_member(self, member_id: int) -> List[TodoAssignment]:
        """
        获取成员待处理的分配
        
        Args:
            member_id: 成员ID
        
        Returns:
            分配列表
        """
        sql = '''
            SELECT * FROM todo_assignments 
            WHERE to_member_id = ? AND status = 'pending'
            ORDER BY assigned_at DESC
        '''
        rows = self.db.query(sql, (member_id,))
        return [self._row_to_assignment(row) for row in rows]
    
    def get_by_todo(self, todo_id: int) -> List[TodoAssignment]:
        """
        获取待办的所有分配历史
        
        Args:
            todo_id: 待办ID
        
        Returns:
            分配列表
        """
        sql = '''
            SELECT * FROM todo_assignments 
            WHERE todo_id = ?
            ORDER BY assigned_at DESC
        '''
        rows = self.db.query(sql, (todo_id,))
        return [self._row_to_assignment(row) for row in rows]
    
    def get_sent_by_member(self, member_id: int) -> List[TodoAssignment]:
        """
        获取成员发出的分配
        
        Args:
            member_id: 成员ID
        
        Returns:
            分配列表
        """
        sql = '''
            SELECT * FROM todo_assignments 
            WHERE from_member_id = ?
            ORDER BY assigned_at DESC
        '''
        rows = self.db.query(sql, (member_id,))
        return [self._row_to_assignment(row) for row in rows]
    
    def accept(self, assignment_id: int, response_message: str = "") -> bool:
        """
        接受分配
        
        Args:
            assignment_id: 分配ID
            response_message: 回复说明
        
        Returns:
            是否成功
        """
        sql = '''
            UPDATE todo_assignments 
            SET status = 'accepted', 
                response_message = ?, 
                responded_at = ?
            WHERE id = ?
        '''
        try:
            self.db.execute(sql, (response_message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), assignment_id))
            logger.info(f"Assignment {assignment_id} accepted")
            return True
        except Exception as e:
            logger.error(f"Failed to accept assignment {assignment_id}: {e}")
            return False
    
    def reject(self, assignment_id: int, response_message: str = "") -> bool:
        """
        拒绝分配
        
        Args:
            assignment_id: 分配ID
            response_message: 拒绝理由
        
        Returns:
            是否成功
        """
        sql = '''
            UPDATE todo_assignments 
            SET status = 'rejected', 
                response_message = ?, 
                responded_at = ?
            WHERE id = ?
        '''
        try:
            self.db.execute(sql, (response_message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), assignment_id))
            logger.info(f"Assignment {assignment_id} rejected")
            return True
        except Exception as e:
            logger.error(f"Failed to reject assignment {assignment_id}: {e}")
            return False
    
    def complete(self, assignment_id: int) -> bool:
        """
        标记分配完成
        
        Args:
            assignment_id: 分配ID
        
        Returns:
            是否成功
        """
        sql = 'UPDATE todo_assignments SET status = ? WHERE id = ?'
        try:
            self.db.execute(sql, ('completed', assignment_id))
            logger.info(f"Assignment {assignment_id} completed")
            return True
        except Exception as e:
            logger.error(f"Failed to complete assignment {assignment_id}: {e}")
            return False
    
    def delete(self, assignment_id: int) -> bool:
        """
        删除分配
        
        Args:
            assignment_id: 分配ID
        
        Returns:
            是否成功
        """
        sql = 'DELETE FROM todo_assignments WHERE id = ?'
        try:
            self.db.execute(sql, (assignment_id,))
            logger.info(f"Deleted assignment {assignment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete assignment {assignment_id}: {e}")
            return False
    
    def count_pending_by_member(self, member_id: int) -> int:
        """
        统计成员待处理分配数量
        
        Args:
            member_id: 成员ID
        
        Returns:
            数量
        """
        sql = 'SELECT COUNT(*) as count FROM todo_assignments WHERE to_member_id = ? AND status = "pending"'
        row = self.db.query_one(sql, (member_id,))
        return row['count'] if row else 0
    
    def _row_to_assignment(self, row) -> TodoAssignment:
        """将数据库行转换为对象"""
        return TodoAssignment(
            id=row['id'],
            todo_id=row['todo_id'],
            from_member_id=row['from_member_id'],
            to_member_id=row['to_member_id'],
            status=row['status'],
            message=row['message'] or "",
            response_message=row['response_message'] or "",
            assigned_at=row['assigned_at'],
            responded_at=row['responded_at']
        )
