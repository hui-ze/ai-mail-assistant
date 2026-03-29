# src/core/assignment_service.py
"""
待办分配服务
Phase 8: 待办分配与提醒功能
"""
from typing import List, Optional, Dict
from datetime import datetime
from src.data.database import Database
from src.data.todo_assignment_repo import TodoAssignmentRepo, TodoAssignment
from src.data.reminder_repo import ReminderRepo, Reminder
from src.data.todo_repo import TodoRepo
from src.data.team_member_repo import TeamMemberRepo
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('assignment_service', get_log_dir())


class AssignmentService:
    """待办分配服务"""
    
    def __init__(self, db: Database):
        """
        初始化分配服务
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.assignment_repo = TodoAssignmentRepo(db)
        self.reminder_repo = ReminderRepo(db)
        self.todo_repo = TodoRepo(db)
        self.member_repo = TeamMemberRepo(db)
    
    def assign_todo(self, todo_id: int, from_member_id: int, to_member_id: int, 
                    message: str = "") -> Dict:
        """
        分配待办给团队成员
        
        Args:
            todo_id: 待办ID
            from_member_id: 分配人ID
            to_member_id: 接收人ID
            message: 分配说明
        
        Returns:
            结果字典 {'success': bool, 'assignment_id': int, 'message': str}
        """
        try:
            # 1. 检查待办是否存在
            todo = self.todo_repo.get_todo_by_id(todo_id)
            if not todo:
                return {'success': False, 'message': '待办不存在'}
            
            # 2. 检查接收人是否存在
            to_member = self.member_repo.get_by_id(to_member_id)
            if not to_member:
                return {'success': False, 'message': '接收人不存在'}
            
            # 3. 检查是否已分配给该成员
            assignments = self.assignment_repo.get_by_todo(todo_id)
            for a in assignments:
                if a.to_member_id == to_member_id and a.status in ['pending', 'accepted']:
                    return {'success': False, 'message': '该待办已分配给此成员'}
            
            # 4. 创建分配记录
            assignment_id = self.assignment_repo.create(
                todo_id, from_member_id, to_member_id, message
            )
            
            # 5. 创建分配提醒
            self.reminder_repo.create(
                to_member_id, 'assignment',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                f"您有一个新的待办分配：{todo['content']}",
                todo_id
            )
            
            # 6. 如果待办有截止日期,自动创建截止提醒
            if todo.get('due_date'):
                self.reminder_repo.create_auto_reminders(
                    todo_id, to_member_id, todo['due_date'], todo['content']
                )
            
            logger.info(f"Assigned todo {todo_id} to member {to_member_id}")
            
            return {
                'success': True,
                'assignment_id': assignment_id,
                'message': f'已成功分配给 {to_member.name}'
            }
            
        except Exception as e:
            logger.error(f"Failed to assign todo: {e}")
            return {'success': False, 'message': str(e)}
    
    def accept_assignment(self, assignment_id: int, response_message: str = "") -> bool:
        """
        接受分配
        
        Args:
            assignment_id: 分配ID
            response_message: 回复说明
        
        Returns:
            是否成功
        """
        try:
            assignment = self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                logger.error(f"Assignment {assignment_id} not found")
                return False
            
            success = self.assignment_repo.accept(assignment_id, response_message)
            
            if success:
                # 更新待办的归属人
                self.todo_repo.update_todo(
                    assignment.todo_id,
                    assignee=self.member_repo.get_by_id(assignment.to_member_id).name,
                    assign_type='other'
                )
                
                # 通知分配人
                self.reminder_repo.create(
                    assignment.from_member_id, 'assignment',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    f"您的待办分配已被接受",
                    assignment.todo_id
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to accept assignment: {e}")
            return False
    
    def reject_assignment(self, assignment_id: int, response_message: str = "") -> bool:
        """
        拒绝分配
        
        Args:
            assignment_id: 分配ID
            response_message: 拒绝理由
        
        Returns:
            是否成功
        """
        try:
            assignment = self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                logger.error(f"Assignment {assignment_id} not found")
                return False
            
            success = self.assignment_repo.reject(assignment_id, response_message)
            
            if success:
                # 通知分配人
                self.reminder_repo.create(
                    assignment.from_member_id, 'assignment',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    f"您的待办分配已被拒绝：{response_message}",
                    assignment.todo_id
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reject assignment: {e}")
            return False
    
    def get_pending_assignments(self, member_id: int) -> List[Dict]:
        """
        获取成员待处理的分配(含详细信息)
        
        Args:
            member_id: 成员ID
        
        Returns:
            分配列表(含待办和分配人信息)
        """
        assignments = self.assignment_repo.get_pending_by_member(member_id)
        result = []
        
        for assignment in assignments:
            todo = self.todo_repo.get_todo_by_id(assignment.todo_id)
            from_member = self.member_repo.get_by_id(assignment.from_member_id)
            
            result.append({
                'assignment': assignment,
                'todo': todo,
                'from_member': from_member
            })
        
        return result
    
    def get_assignment_history(self, todo_id: int) -> List[Dict]:
        """
        获取待办分配历史(含详细信息)
        
        Args:
            todo_id: 待办ID
        
        Returns:
            分配历史列表
        """
        assignments = self.assignment_repo.get_by_todo(todo_id)
        result = []
        
        for assignment in assignments:
            from_member = self.member_repo.get_by_id(assignment.from_member_id)
            to_member = self.member_repo.get_by_id(assignment.to_member_id)
            
            result.append({
                'assignment': assignment,
                'from_member': from_member,
                'to_member': to_member
            })
        
        return result
