# src/core/reminder_service.py
"""
提醒服务
Phase 8: 待办分配与提醒功能
"""
from typing import List, Dict
from datetime import datetime
from src.data.database import Database
from src.data.reminder_repo import ReminderRepo, Reminder
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('reminder_service', get_log_dir())


class ReminderService:
    """提醒服务"""
    
    def __init__(self, db: Database):
        """
        初始化提醒服务
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.reminder_repo = ReminderRepo(db)
    
    def check_and_trigger_reminders(self) -> List[Dict]:
        """
        检查并触发到期提醒
        
        Returns:
            触发的提醒列表
        """
        try:
            # 获取到期提醒
            due_reminders = self.reminder_repo.get_due_reminders()
            triggered = []
            
            for reminder in due_reminders:
                # 触发通知
                notification_result = self._send_notification(reminder)
                
                if notification_result['success']:
                    # 标记为已发送
                    self.reminder_repo.mark_sent(reminder.id)
                    triggered.append({
                        'reminder': reminder,
                        'notification': notification_result
                    })
                    logger.info(f"Triggered reminder {reminder.id}: {reminder.message}")
            
            return triggered
            
        except Exception as e:
            logger.error(f"Failed to check reminders: {e}")
            return []
    
    def _send_notification(self, reminder: Reminder) -> Dict:
        """
        发送通知(系统通知)
        
        Args:
            reminder: 提醒对象
        
        Returns:
            结果字典
        """
        try:
            # 尝试使用 plyer 发送系统通知
            try:
                from plyer import notification
                
                notification.notify(
                    title='待办提醒',
                    message=reminder.message,
                    app_name='AI邮件助手',
                    timeout=10
                )
                
                return {'success': True, 'method': 'system'}
                
            except ImportError:
                # plyer 未安装,返回成功但不发送实际通知
                logger.warning("plyer not installed, notification not sent")
                return {'success': True, 'method': 'none'}
                
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
                return {'success': False, 'error': str(e)}
                
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_custom_reminder(self, member_id: int, remind_at: str, 
                                message: str, todo_id: int = None) -> int:
        """
        创建自定义提醒
        
        Args:
            member_id: 成员ID
            remind_at: 提醒时间
            message: 提醒消息
            todo_id: 关联待办ID(可选)
        
        Returns:
            提醒ID
        """
        return self.reminder_repo.create(
            member_id, 'custom', remind_at, message, todo_id
        )
    
    def get_pending_reminders(self, member_id: int) -> List[Reminder]:
        """
        获取成员待发送提醒
        
        Args:
            member_id: 成员ID
        
        Returns:
            提醒列表
        """
        return self.reminder_repo.get_pending_by_member(member_id)
    
    def cancel_reminder(self, reminder_id: int) -> bool:
        """
        取消提醒
        
        Args:
            reminder_id: 提醒ID
        
        Returns:
            是否成功
        """
        return self.reminder_repo.delete(reminder_id)
    
    def get_reminder_stats(self, member_id: int) -> Dict:
        """
        获取提醒统计信息
        
        Args:
            member_id: 成员ID
        
        Returns:
            统计字典
        """
        pending = self.reminder_repo.count_unsent_by_member(member_id)
        
        # 获取今日提醒数量
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        today_reminders = self.db.query(
            '''SELECT COUNT(*) as count FROM reminders 
               WHERE member_id = ? AND remind_at BETWEEN ? AND ?''',
            (member_id, today_start.strftime('%Y-%m-%d %H:%M:%S'), 
             today_end.strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        return {
            'pending': pending,
            'today': today_reminders[0]['count'] if today_reminders else 0
        }
