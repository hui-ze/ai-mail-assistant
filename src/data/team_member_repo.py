# src/data/team_member_repo.py
"""
团队成员数据访问层
Phase 7: 部门协作功能
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from src.data.database import Database
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('team_member_repo', get_log_dir())


@dataclass
class TeamMember:
    """团队成员数据类"""
    id: Optional[int] = None
    department_id: int = 0
    name: str = ""
    email: str = ""
    role: str = ""
    is_leader: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TeamMemberRepo:
    """团队成员数据访问类"""
    
    def __init__(self, db: Database):
        """
        初始化成员仓库
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def create(self, department_id: int, name: str, email: str, 
               role: str = "", is_leader: bool = False) -> int:
        """
        创建团队成员
        
        Args:
            department_id: 部门ID
            name: 成员姓名
            email: 成员邮箱
            role: 成员角色
            is_leader: 是否为Leader
        
        Returns:
            创建的成员ID
        """
        sql = '''
            INSERT INTO team_members (department_id, name, email, role, is_leader)
            VALUES (?, ?, ?, ?, ?)
        '''
        member_id = self.db.execute(sql, (department_id, name, email, role, is_leader))
        logger.info(f"Created team member: {name} <{email}> (ID: {member_id})")
        return member_id
    
    def get_by_id(self, member_id: int) -> Optional[TeamMember]:
        """
        根据ID获取成员
        
        Args:
            member_id: 成员ID
        
        Returns:
            成员对象,不存在返回None
        """
        sql = 'SELECT * FROM team_members WHERE id = ?'
        row = self.db.query_one(sql, (member_id,))
        if row:
            return TeamMember(
                id=row['id'],
                department_id=row['department_id'],
                name=row['name'],
                email=row['email'],
                role=row['role'] or "",
                is_leader=bool(row['is_leader']),
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def get_by_email(self, email: str, department_id: int = None) -> Optional[TeamMember]:
        """
        根据邮箱获取成员
        
        Args:
            email: 成员邮箱
            department_id: 部门ID(可选,用于跨部门查询)
        
        Returns:
            成员对象,不存在返回None
        """
        if department_id:
            sql = 'SELECT * FROM team_members WHERE email = ? AND department_id = ?'
            row = self.db.query_one(sql, (email, department_id))
        else:
            sql = 'SELECT * FROM team_members WHERE email = ?'
            row = self.db.query_one(sql, (email,))
        
        if row:
            return TeamMember(
                id=row['id'],
                department_id=row['department_id'],
                name=row['name'],
                email=row['email'],
                role=row['role'] or "",
                is_leader=bool(row['is_leader']),
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def get_by_department(self, department_id: int, active_only: bool = True) -> List[TeamMember]:
        """
        获取部门所有成员
        
        Args:
            department_id: 部门ID
            active_only: 是否只获取活跃成员
        
        Returns:
            成员列表
        """
        if active_only:
            sql = 'SELECT * FROM team_members WHERE department_id = ? AND is_active = 1 ORDER BY name'
        else:
            sql = 'SELECT * FROM team_members WHERE department_id = ? ORDER BY name'
        
        rows = self.db.query(sql, (department_id,))
        return [
            TeamMember(
                id=row['id'],
                department_id=row['department_id'],
                name=row['name'],
                email=row['email'],
                role=row['role'] or "",
                is_leader=bool(row['is_leader']),
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    def get_leaders(self, department_id: int = None) -> List[TeamMember]:
        """
        获取Leader列表
        
        Args:
            department_id: 部门ID(可选,不指定则获取所有Leader)
        
        Returns:
            Leader列表
        """
        if department_id:
            sql = 'SELECT * FROM team_members WHERE department_id = ? AND is_leader = 1 AND is_active = 1'
            rows = self.db.query(sql, (department_id,))
        else:
            sql = 'SELECT * FROM team_members WHERE is_leader = 1 AND is_active = 1'
            rows = self.db.query(sql)
        
        return [
            TeamMember(
                id=row['id'],
                department_id=row['department_id'],
                name=row['name'],
                email=row['email'],
                role=row['role'] or "",
                is_leader=bool(row['is_leader']),
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    def update(self, member_id: int, name: str = None, email: str = None,
               role: str = None, is_leader: bool = None, is_active: bool = None) -> bool:
        """
        更新成员信息
        
        Args:
            member_id: 成员ID
            name: 新姓名(可选)
            email: 新邮箱(可选)
            role: 新角色(可选)
            is_leader: 是否为Leader(可选)
            is_active: 是否活跃(可选)
        
        Returns:
            是否更新成功
        """
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if email is not None:
            updates.append('email = ?')
            params.append(email)
        if role is not None:
            updates.append('role = ?')
            params.append(role)
        if is_leader is not None:
            updates.append('is_leader = ?')
            params.append(1 if is_leader else 0)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(1 if is_active else 0)
        
        if not updates:
            return False
        
        updates.append('updated_at = ?')
        params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        params.append(member_id)
        
        sql = f"UPDATE team_members SET {', '.join(updates)} WHERE id = ?"
        try:
            self.db.execute(sql, tuple(params))
            logger.info(f"Updated team member ID {member_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update member {member_id}: {e}")
            return False
    
    def delete(self, member_id: int) -> bool:
        """
        删除成员(级联删除同步记录)
        
        Args:
            member_id: 成员ID
        
        Returns:
            是否删除成功
        """
        sql = 'DELETE FROM team_members WHERE id = ?'
        try:
            self.db.execute(sql, (member_id,))
            logger.info(f"Deleted team member ID {member_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete member {member_id}: {e}")
            return False
    
    def count_by_department(self, department_id: int) -> int:
        """
        统计部门成员数量
        
        Args:
            department_id: 部门ID
        
        Returns:
            成员数量
        """
        sql = 'SELECT COUNT(*) as count FROM team_members WHERE department_id = ? AND is_active = 1'
        row = self.db.query_one(sql, (department_id,))
        return row['count'] if row else 0
