# src/data/reminder_repo.py
"""
提醒数据访问层
Phase 8: 待办分配与提醒功能
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from src.data.database import Database
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('reminder_repo', get_log_dir())


@dataclass
class Reminder:
    """提醒数据类"""
    id: Optional[int] = None
    todo_id: Optional[int] = None
    member_id: int = 0
    reminder_type: str = ""  # due_date/custom/assignment
    remind_at: str = ""
    is_sent: bool = False
    message: str = ""
    created_at: Optional[str] = None


class ReminderRepo:
    """提醒数据访问类"""
    
    def __init__(self, db: Database):
        """
        初始化提醒仓库
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def create(self, member_id: int, reminder_type: str, remind_at: str, 
               message: str = "", todo_id: int = None) -> int:
        """
        创建提醒
        
        Args:
            member_id: 成员ID
            reminder_type: 提醒类型 (due_date/custom/assignment)
            remind_at: 提醒时间
            message: 提醒消息
            todo_id: 关联待办ID(可选)
        
        Returns:
            创建的提醒ID
        """
        sql = '''
            INSERT INTO reminders (todo_id, member_id, reminder_type, remind_at, message)
            VALUES (?, ?, ?, ?, ?)
        '''
        reminder_id = self.db.execute(sql, (todo_id, member_id, reminder_type, remind_at, message))
        logger.info(f"Created reminder: type={reminder_type}, time={remind_at}")
        return reminder_id
    
    def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        """
        根据ID获取提醒
        
        Args:
            reminder_id: 提醒ID
        
        Returns:
            提醒对象,不存在返回None
        """
        sql = 'SELECT * FROM reminders WHERE id = ?'
        row = self.db.query_one(sql, (reminder_id,))
        if row:
            return self._row_to_reminder(row)
        return None
    
    def get_pending_by_member(self, member_id: int) -> List[Reminder]:
        """
        获取成员待发送的提醒
        
        Args:
            member_id: 成员ID
        
        Returns:
            提醒列表
        """
        sql = '''
            SELECT * FROM reminders 
            WHERE member_id = ? AND is_sent = 0
            ORDER BY remind_at ASC
        '''
        rows = self.db.query(sql, (member_id,))
        return [self._row_to_reminder(row) for row in rows]
    
    def get_due_reminders(self, current_time: str = None) -> List[Reminder]:
        """
        获取到期应发送的提醒
        
        Args:
            current_time: 当前时间(可选),默认使用系统当前时间
        
        Returns:
            提醒列表
        """
        if current_time is None:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = '''
            SELECT * FROM reminders 
            WHERE is_sent = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
        '''
        rows = self.db.query(sql, (current_time,))
        return [self._row_to_reminder(row) for row in rows]
    
    def mark_sent(self, reminder_id: int) -> bool:
        """
        标记提醒已发送
        
        Args:
            reminder_id: 提醒ID
        
        Returns:
            是否成功
        """
        sql = 'UPDATE reminders SET is_sent = 1 WHERE id = ?'
        try:
            self.db.execute(sql, (reminder_id,))
            logger.debug(f"Reminder {reminder_id} marked as sent")
            return True
        except Exception as e:
            logger.error(f"Failed to mark reminder {reminder_id} as sent: {e}")
            return False
    
    def delete(self, reminder_id: int) -> bool:
        """
        删除提醒
        
        Args:
            reminder_id: 提醒ID
        
        Returns:
            是否成功
        """
        sql = 'DELETE FROM reminders WHERE id = ?'
        try:
            self.db.execute(sql, (reminder_id,))
            logger.info(f"Deleted reminder {reminder_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete reminder {reminder_id}: {e}")
            return False
    
    def delete_by_todo(self, todo_id: int) -> bool:
        """
        删除待办的所有提醒
        
        Args:
            todo_id: 待办ID
        
        Returns:
            是否成功
        """
        sql = 'DELETE FROM reminders WHERE todo_id = ?'
        try:
            self.db.execute(sql, (todo_id,))
            logger.info(f"Deleted all reminders for todo {todo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete reminders for todo {todo_id}: {e}")
            return False
    
    def create_auto_reminders(self, todo_id: int, member_id: int, 
                              due_date: str, todo_title: str) -> List[int]:
        """
        为待办自动创建截止提醒
        
        Args:
            todo_id: 待办ID
            member_id: 成员ID
            due_date: 截止日期
            todo_title: 待办标题
        
        Returns:
            创建的提醒ID列表
        """
        reminder_ids = []
        
        try:
            due_dt = datetime.strptime(due_date, '%Y-%m-%d')
            now = datetime.now()
            
            # 提前1天提醒
            if due_dt - timedelta(days=1) > now:
                remind_at = (due_dt - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                reminder_id = self.create(
                    member_id, 'due_date', remind_at,
                    f"待办「{todo_title}」将于明天到期", todo_id
                )
                reminder_ids.append(reminder_id)
            
            # 提前1小时提醒
            if due_dt - timedelta(hours=1) > now:
                remind_at = (due_dt - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
                reminder_id = self.create(
                    member_id, 'due_date', remind_at,
                    f"待办「{todo_title}」将于1小时后到期", todo_id
                )
                reminder_ids.append(reminder_id)
            
            # 提前10分钟提醒
            if due_dt - timedelta(minutes=10) > now:
                remind_at = (due_dt - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
                reminder_id = self.create(
                    member_id, 'due_date', remind_at,
                    f"待办「{todo_title}」将于10分钟后到期", todo_id
                )
                reminder_ids.append(reminder_id)
            
            logger.info(f"Created {len(reminder_ids)} auto reminders for todo {todo_id}")
            
        except Exception as e:
            logger.error(f"Failed to create auto reminders: {e}")
        
        return reminder_ids
    
    def count_unsent_by_member(self, member_id: int) -> int:
        """
        统计成员未发送提醒数量
        
        Args:
            member_id: 成员ID
        
        Returns:
            数量
        """
        sql = 'SELECT COUNT(*) as count FROM reminders WHERE member_id = ? AND is_sent = 0'
        row = self.db.query_one(sql, (member_id,))
        return row['count'] if row else 0
    
    def _row_to_reminder(self, row) -> Reminder:
        """将数据库行转换为对象"""
        return Reminder(
            id=row['id'],
            todo_id=row['todo_id'],
            member_id=row['member_id'],
            reminder_type=row['reminder_type'],
            remind_at=row['remind_at'],
            is_sent=bool(row['is_sent']),
            message=row['message'] or "",
            created_at=row['created_at']
        )
