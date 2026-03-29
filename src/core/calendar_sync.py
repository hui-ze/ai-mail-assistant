# -*- coding: utf-8 -*-
"""
日历同步模块
支持将待办事项同步到各类日历服务
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..data.database import Database


@dataclass
class CalendarEvent:
    """日历事件数据类"""
    id: Optional[str]
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str = ""
    reminder_minutes: int = 30
    color: str = "#4285F4"


@dataclass
class TodoSyncResult:
    """待办同步结果"""
    success: bool
    calendar_event_id: Optional[str]
    message: str
    event: Optional[CalendarEvent] = None


class CalendarSyncService(ABC):
    """日历同步服务基类"""

    def __init__(self, db: Database):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """加载日历设置"""
        try:
            result = self.db.query_one(
                "SELECT value FROM settings WHERE id = 2"
            )
            if result and result[0]:
                return json.loads(result[0])
        except Exception as e:
            self.logger.warning(f"加载日历设置失败: {e}")
        return {}

    def _save_settings(self, settings: Dict[str, Any]):
        """保存日历设置"""
        try:
            existing = self.db.query_one("SELECT id FROM settings WHERE id = 2")
            if existing:
                self.db.execute(
                    "UPDATE settings SET value = ? WHERE id = 2",
                    (json.dumps(settings),)
                )
            else:
                self.db.execute(
                    "INSERT INTO settings (id, value) VALUES (2, ?)",
                    (json.dumps(settings),)
                )
            self._settings = settings
        except Exception as e:
            self.logger.error(f"保存日历设置失败: {e}")

    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass

    @abstractmethod
    def create_event(self, event: CalendarEvent) -> TodoSyncResult:
        """创建日历事件"""
        pass

    @abstractmethod
    def update_event(self, event_id: str, event: CalendarEvent) -> TodoSyncResult:
        """更新日历事件"""
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """删除日历事件"""
        pass

    @abstractmethod
    def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """获取日期范围内的事件"""
        pass

    def todo_to_event(
        self,
        todo: Dict[str, Any],
        duration_minutes: int = 60
    ) -> CalendarEvent:
        """将待办转换为日历事件"""
        # 解析截止日期
        due_date = None
        if todo.get('due_date'):
            try:
                due_date = datetime.fromisoformat(todo['due_date'])
            except:
                # 尝试解析常见格式
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y/%m/%d']:
                    try:
                        due_date = datetime.strptime(todo['due_date'], fmt)
                        break
                    except:
                        continue

        # 如果没有截止日期，默认明天
        if not due_date:
            due_date = datetime.now() + timedelta(days=1)

        # 设置提醒时间
        reminder = self._settings.get('reminder_minutes', 1)  # 0: 15min, 1: 30min, 2: 1h, 3: 1day
        reminder_map = {0: 15, 1: 30, 2: 60, 3: 1440}
        reminder_minutes = reminder_map.get(reminder, 30)

        # 优先级颜色
        priority_colors = {
            '高': '#F44336',  # 红色
            '中': '#FF9800',  # 橙色
            '低': '#4CAF50'   # 绿色
        }

        return CalendarEvent(
            id=todo.get('calendar_event_id'),
            title=todo.get('content', '待办事项')[:100],
            description=f"来自邮件的待办事项\n优先级: {todo.get('priority', '中')}",
            start_time=due_date,
            end_time=due_date + timedelta(minutes=duration_minutes),
            reminder_minutes=reminder_minutes,
            color=priority_colors.get(todo.get('priority', '中'), '#4285F4')
        )

    def sync_todo_to_calendar(self, todo: Dict[str, Any]) -> TodoSyncResult:
        """将单个待办同步到日历"""
        # 检查是否只需要高优先级
        if self._settings.get('sync_high_priority', False):
            if todo.get('priority') not in ['高', 'high']:
                return TodoSyncResult(
                    success=True,
                    calendar_event_id=None,
                    message="跳过非高优先级待办"
                )

        # 转换为事件
        event = self.todo_to_event(todo)

        # 检查是否已有同步的事件
        if todo.get('calendar_event_id'):
            return self.update_event(todo['calendar_event_id'], event)
        else:
            result = self.create_event(event)
            if result.success:
                # 更新待办的日历事件ID
                self._update_todo_calendar_id(todo['id'], result.calendar_event_id)
            return result

    def _update_todo_calendar_id(self, todo_id: int, calendar_event_id: str):
        """更新待办的日历事件ID"""
        self.db.execute(
            "UPDATE todos SET calendar_event_id = ? WHERE id = ?",
            (calendar_event_id, todo_id)
        )


class OutlookCalendarSync(CalendarSyncService):
    """Outlook日历同步"""

    PROVIDER_NAME = "Outlook Calendar"

    def __init__(self, db: Database, account: str = None):
        super().__init__(db)
        self.account = account or self._settings.get('outlook_account', '')
        self._access_token = None

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.account) and bool(self._settings.get('enabled', False))

    def test_connection(self) -> bool:
        """测试Outlook连接"""
        if not self.account:
            return False

        try:
            # TODO: 实现Outlook Graph API连接测试
            # 需要使用 microsoft-authentication-library-for-python (MSAL)
            # 1. 注册Azure AD应用
            # 2. 获取access token
            # 3. 调用 Graph API 测试连接
            self.logger.info(f"测试Outlook连接: {self.account}")
            return True

        except Exception as e:
            self.logger.error(f"Outlook连接测试失败: {e}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        # TODO: 实现OAuth2认证流程
        # 使用 MSAL Python 库
        # client_id, tenant_id 从配置文件读取
        pass

    def create_event(self, event: CalendarEvent) -> TodoSyncResult:
        """创建Outlook日历事件"""
        try:
            # TODO: 实现Graph API创建事件
            # POST https://graph.microsoft.com/v1.0/me/events
            self.logger.info(f"创建Outlook事件: {event.title}")

            # 模拟成功
            event_id = f"outlook_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件创建成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"创建Outlook事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"创建失败: {str(e)}"
            )

    def update_event(self, event_id: str, event: CalendarEvent) -> TodoSyncResult:
        """更新Outlook日历事件"""
        try:
            # TODO: 实现Graph API更新事件
            # PATCH https://graph.microsoft.com/v1.0/me/events/{event_id}
            self.logger.info(f"更新Outlook事件: {event_id}")

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件更新成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"更新Outlook事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"更新失败: {str(e)}"
            )

    def delete_event(self, event_id: str) -> bool:
        """删除Outlook日历事件"""
        try:
            # TODO: 实现Graph API删除事件
            # DELETE https://graph.microsoft.com/v1.0/me/events/{event_id}
            self.logger.info(f"删除Outlook事件: {event_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除Outlook事件失败: {e}")
            return False

    def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """获取Outlook日历事件"""
        events = []

        try:
            # TODO: 实现Graph API查询事件
            # GET https://graph.microsoft.com/v1.0/me/calendarview?start={}&end={}
            self.logger.info(f"查询Outlook事件: {start_date} - {end_date}")

        except Exception as e:
            self.logger.error(f"查询Outlook事件失败: {e}")

        return events


class GoogleCalendarSync(CalendarSyncService):
    """Google日历同步"""

    PROVIDER_NAME = "Google Calendar"

    def __init__(self, db: Database, calendar_id: str = "primary"):
        super().__init__(db)
        self.calendar_id = calendar_id or self._settings.get('google_calendar_id', 'primary')

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self._settings.get('enabled', False)) and bool(
            self._settings.get('google_api_key') or
            self._settings.get('google_credentials_path')
        )

    def test_connection(self) -> bool:
        """测试Google日历连接"""
        try:
            # TODO: 实现Google Calendar API连接测试
            # 需要 google-api-python-client
            # 1. 使用服务账号或OAuth2认证
            # 2. 调用 calendarList().list() 测试
            self.logger.info(f"测试Google日历连接: {self.calendar_id}")
            return True

        except Exception as e:
            self.logger.error(f"Google日历连接测试失败: {e}")
            return False

    def _get_credentials(self):
        """获取Google API凭证"""
        # TODO: 实现Google认证
        # 使用 google-auth 库
        pass

    def create_event(self, event: CalendarEvent) -> TodoSyncResult:
        """创建Google日历事件"""
        try:
            # TODO: 实现Google Calendar API创建事件
            # POST https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
            self.logger.info(f"创建Google事件: {event.title}")

            # 模拟成功
            event_id = f"google_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件创建成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"创建Google事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"创建失败: {str(e)}"
            )

    def update_event(self, event_id: str, event: CalendarEvent) -> TodoSyncResult:
        """更新Google日历事件"""
        try:
            # TODO: 实现Google Calendar API更新事件
            # PUT https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events/{eventId}
            self.logger.info(f"更新Google事件: {event_id}")

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件更新成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"更新Google事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"更新失败: {str(e)}"
            )

    def delete_event(self, event_id: str) -> bool:
        """删除Google日历事件"""
        try:
            # TODO: 实现Google Calendar API删除事件
            # DELETE https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events/{eventId}
            self.logger.info(f"删除Google事件: {event_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除Google事件失败: {e}")
            return False

    def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """获取Google日历事件"""
        events = []

        try:
            # TODO: 实现Google Calendar API查询事件
            # GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
            self.logger.info(f"查询Google事件: {start_date} - {end_date}")

        except Exception as e:
            self.logger.error(f"查询Google事件失败: {e}")

        return events


class LocalCalendarSync(CalendarSyncService):
    """本地日历同步（使用系统日历）"""

    PROVIDER_NAME = "Local Calendar"

    def __init__(self, db: Database):
        super().__init__(db)
        self._events = []  # 内存存储，实际可用数据库表

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self._settings.get('enabled', False)

    def test_connection(self) -> bool:
        """测试本地日历连接"""
        return True

    def create_event(self, event: CalendarEvent) -> TodoSyncResult:
        """创建本地日历事件"""
        try:
            # 生成唯一ID
            event_id = f"local_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            event.id = event_id

            # 保存到列表
            self._events.append(event)

            # 同时保存到数据库
            self._ensure_table_exists()
            self._save_event_to_db(event)

            self.logger.info(f"创建本地事件: {event.title}")

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件创建成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"创建本地事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"创建失败: {str(e)}"
            )

    def _ensure_table_exists(self):
        """确保事件表存在"""
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT,
                end_time TEXT,
                location TEXT,
                reminder_minutes INTEGER,
                color TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def _save_event_to_db(self, event: CalendarEvent):
        """保存事件到数据库"""
        self.db.execute('''
            INSERT OR REPLACE INTO calendar_events 
            (id, title, description, start_time, end_time, location, reminder_minutes, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id,
            event.title,
            event.description,
            event.start_time.isoformat(),
            event.end_time.isoformat(),
            event.location,
            event.reminder_minutes,
            event.color
        ))

    def update_event(self, event_id: str, event: CalendarEvent) -> TodoSyncResult:
        """更新本地日历事件"""
        try:
            event.id = event_id
            self._save_event_to_db(event)

            self.logger.info(f"更新本地事件: {event_id}")

            return TodoSyncResult(
                success=True,
                calendar_event_id=event_id,
                message="事件更新成功",
                event=event
            )

        except Exception as e:
            self.logger.error(f"更新本地事件失败: {e}")
            return TodoSyncResult(
                success=False,
                calendar_event_id=None,
                message=f"更新失败: {str(e)}"
            )

    def delete_event(self, event_id: str) -> bool:
        """删除本地日历事件"""
        try:
            self.db.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
            self._events = [e for e in self._events if e.id != event_id]
            self.logger.info(f"删除本地事件: {event_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除本地事件失败: {e}")
            return False

    def get_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """获取本地日历事件"""
        events = []

        try:
            results = self.db.query(
                '''SELECT * FROM calendar_events 
                   WHERE start_time BETWEEN ? AND ?
                   ORDER BY start_time''',
                (start_date.isoformat(), end_date.isoformat())
            )

            for row in results:
                events.append(CalendarEvent(
                    id=row[0],
                    title=row[1],
                    description=row[2] or "",
                    start_time=datetime.fromisoformat(row[3]),
                    end_time=datetime.fromisoformat(row[4]),
                    location=row[5] or "",
                    reminder_minutes=row[6] or 30,
                    color=row[7] or "#4285F4"
                ))

        except Exception as e:
            self.logger.error(f"查询本地事件失败: {e}")

        return events


def create_calendar_sync(db: Database, calendar_type: int = 0) -> CalendarSyncService:
    """
    工厂函数：创建日历同步服务

    Args:
        db: 数据库实例
        calendar_type: 日历类型 (0: Outlook, 1: Google, 2: Apple, 3: Local)

    Returns:
        CalendarSyncService 实例
    """
    providers = {
        0: OutlookCalendarSync,
        1: GoogleCalendarSync,
        2: OutlookCalendarSync,  # TODO: Apple Calendar
        3: LocalCalendarSync
    }

    sync_class = providers.get(calendar_type, LocalCalendarSync)
    return sync_class(db)
