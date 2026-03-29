# src/core/sync_service.py
"""
团队待办同步服务
Phase 7: 部门协作功能
"""
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime
from src.data.database import Database
from src.data.todo_repo import TodoRepo, TodoItem
from src.data.team_member_repo import TeamMemberRepo, TeamMember
from src.data.department_repo import DepartmentRepo, Department
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('sync_service', get_log_dir())


@dataclass
class MemberTodoData:
    """成员待办数据结构(用于JSON同步)"""
    version: str = "1.0"
    member: Dict = None  # {"name": "", "email": "", "department": "", "role": ""}
    sync_time: str = ""
    todos: List[Dict] = None  # 待办列表
    stats: Dict = None  # {"total": 0, "completed": 0, "overdue": 0}


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    sync_type: str  # 'upload' 或 'download'
    member_id: int
    todo_count: int = 0
    file_path: str = ""
    error_message: str = ""
    sync_time: str = ""


class SyncService:
    """团队待办同步服务"""
    
    def __init__(self, db: Database):
        """
        初始化同步服务
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.todo_repo = TodoRepo(db)
        self.member_repo = TeamMemberRepo(db)
        self.dept_repo = DepartmentRepo(db)
    
    def upload_todos(self, member_id: int) -> SyncResult:
        """
        上传当前用户的待办到共享目录
        
        Args:
            member_id: 成员ID
        
        Returns:
            同步结果
        """
        sync_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 1. 获取成员信息
            member = self.member_repo.get_by_id(member_id)
            if not member:
                return SyncResult(
                    success=False,
                    sync_type='upload',
                    member_id=member_id,
                    error_message="Member not found",
                    sync_time=sync_time
                )
            
            # 2. 获取部门信息
            dept = self.dept_repo.get_by_id(member.department_id)
            if not dept:
                return SyncResult(
                    success=False,
                    sync_type='upload',
                    member_id=member_id,
                    error_message="Department not found",
                    sync_time=sync_time
                )
            
            # 3. 获取待办列表
            todos = self.todo_repo.get_all_todos()
            todo_list = [
                {
                    'id': todo['id'],
                    'title': todo['content'],
                    'is_completed': todo['completed'],
                    'priority': todo['priority'],
                    'due_date': todo.get('due_date', "") or "",
                    'assignee': todo.get('assignee', "") or "",
                    'assign_type': todo.get('assign_type', "") or ""
                }
                for todo in todos
            ]
            
            # 4. 统计数据
            stats = {
                'total': len(todos),
                'completed': sum(1 for t in todos if t['completed']),
                'overdue': self._count_overdue(todos)
            }
            
            # 5. 构建JSON数据
            data = MemberTodoData(
                member={
                    'name': member.name,
                    'email': member.email,
                    'department': dept.name,
                    'role': member.role
                },
                sync_time=sync_time,
                todos=todo_list,
                stats=stats
            )
            
            # 6. 写入文件
            file_path = self._get_member_file_path(dept.share_path, member.email)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(data), f, ensure_ascii=False, indent=2)
            
            # 7. 记录同步日志
            self._record_sync(member_id, 'upload', file_path, len(todos), 'success')
            
            logger.info(f"Uploaded {len(todos)} todos for member {member.name}")
            
            return SyncResult(
                success=True,
                sync_type='upload',
                member_id=member_id,
                todo_count=len(todos),
                file_path=file_path,
                sync_time=sync_time
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Upload failed for member {member_id}: {error_msg}")
            self._record_sync(member_id, 'upload', "", 0, 'failed', error_msg)
            
            return SyncResult(
                success=False,
                sync_type='upload',
                member_id=member_id,
                error_message=error_msg,
                sync_time=sync_time
            )
    
    def download_todos(self, member_id: int) -> SyncResult:
        """
        从共享目录下载成员待办(Leader查看)
        
        Args:
            member_id: 成员ID
        
        Returns:
            同步结果
        """
        sync_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 1. 获取成员信息
            member = self.member_repo.get_by_id(member_id)
            if not member:
                return SyncResult(
                    success=False,
                    sync_type='download',
                    member_id=member_id,
                    error_message="Member not found",
                    sync_time=sync_time
                )
            
            # 2. 获取部门信息
            dept = self.dept_repo.get_by_id(member.department_id)
            if not dept:
                return SyncResult(
                    success=False,
                    sync_type='download',
                    member_id=member_id,
                    error_message="Department not found",
                    sync_time=sync_time
                )
            
            # 3. 读取文件
            file_path = self._get_member_file_path(dept.share_path, member.email)
            
            if not os.path.exists(file_path):
                return SyncResult(
                    success=False,
                    sync_type='download',
                    member_id=member_id,
                    error_message="Sync file not found",
                    sync_time=sync_time
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 4. 验证数据格式
            if data.get('version') != '1.0':
                raise ValueError("Unsupported sync file version")
            
            # 5. 记录同步日志
            todo_count = len(data.get('todos', []))
            self._record_sync(member_id, 'download', file_path, todo_count, 'success')
            
            logger.info(f"Downloaded {todo_count} todos for member {member.name}")
            
            return SyncResult(
                success=True,
                sync_type='download',
                member_id=member_id,
                todo_count=todo_count,
                file_path=file_path,
                sync_time=sync_time
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed for member {member_id}: {error_msg}")
            self._record_sync(member_id, 'download', "", 0, 'failed', error_msg)
            
            return SyncResult(
                success=False,
                sync_type='download',
                member_id=member_id,
                error_message=error_msg,
                sync_time=sync_time
            )
    
    def get_team_todos(self, department_id: int) -> Dict[str, MemberTodoData]:
        """
        获取整个团队的待办数据(Leader视图)
        
        Args:
            department_id: 部门ID
        
        Returns:
            成员邮箱 -> 待办数据的映射
        """
        result = {}
        
        try:
            # 获取部门所有成员
            members = self.member_repo.get_by_department(department_id)
            dept = self.dept_repo.get_by_id(department_id)
            
            if not dept:
                logger.error(f"Department {department_id} not found")
                return result
            
            # 遍历每个成员的同步文件
            for member in members:
                file_path = self._get_member_file_path(dept.share_path, member.email)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        result[member.email] = MemberTodoData(
                            version=data.get('version', '1.0'),
                            member=data.get('member', {}),
                            sync_time=data.get('sync_time', ''),
                            todos=data.get('todos', []),
                            stats=data.get('stats', {})
                        )
                    except Exception as e:
                        logger.warning(f"Failed to load sync file for {member.email}: {e}")
            
            logger.info(f"Loaded team todos for {len(result)} members")
            
        except Exception as e:
            logger.error(f"Failed to get team todos: {e}")
        
        return result
    
    def _get_member_file_path(self, share_path: str, email: str) -> str:
        """
        获取成员同步文件路径
        
        Args:
            share_path: 共享目录路径
            email: 成员邮箱
        
        Returns:
            文件路径
        """
        # 使用邮箱作为文件名(替换特殊字符)
        safe_email = email.replace('@', '_at_').replace('.', '_')
        return os.path.join(share_path, 'todos', f"{safe_email}.json")
    
    def _count_overdue(self, todos: List[dict]) -> int:
        """
        统计过期待办数量
        
        Args:
            todos: 待办列表(dict)
        
        Returns:
            过期数量
        """
        count = 0
        now = datetime.now()
        
        for todo in todos:
            due_date = todo.get('due_date')
            if due_date and not todo['completed']:
                try:
                    due = datetime.strptime(due_date, '%Y-%m-%d')
                    if due < now:
                        count += 1
                except:
                    pass
        
        return count
    
    def _record_sync(self, member_id: int, sync_type: str, file_path: str, 
                     todo_count: int, status: str, error_message: str = ""):
        """
        记录同步日志到数据库
        
        Args:
            member_id: 成员ID
            sync_type: 同步类型
            file_path: 文件路径
            todo_count: 待办数量
            status: 状态
            error_message: 错误信息
        """
        sql = '''
            INSERT INTO sync_records (member_id, sync_type, file_path, todo_count, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        try:
            self.db.execute(sql, (member_id, sync_type, file_path, todo_count, status, error_message))
        except Exception as e:
            logger.error(f"Failed to record sync log: {e}")
