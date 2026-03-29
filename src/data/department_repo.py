# src/data/department_repo.py
"""
部门数据访问层
Phase 7: 部门协作功能
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from src.data.database import Database
from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('department_repo', get_log_dir())


@dataclass
class Department:
    """部门数据类"""
    id: Optional[int] = None
    name: str = ""
    share_path: str = ""
    description: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DepartmentRepo:
    """部门数据访问类"""
    
    def __init__(self, db: Database):
        """
        初始化部门仓库
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def create(self, name: str, share_path: str, description: str = "") -> int:
        """
        创建部门
        
        Args:
            name: 部门名称
            share_path: 共享文件路径
            description: 部门描述
        
        Returns:
            创建的部门ID
        """
        sql = '''
            INSERT INTO departments (name, share_path, description)
            VALUES (?, ?, ?)
        '''
        dept_id = self.db.execute(sql, (name, share_path, description))
        logger.info(f"Created department: {name} (ID: {dept_id})")
        return dept_id
    
    def get_by_id(self, dept_id: int) -> Optional[Department]:
        """
        根据ID获取部门
        
        Args:
            dept_id: 部门ID
        
        Returns:
            部门对象,不存在返回None
        """
        sql = 'SELECT * FROM departments WHERE id = ?'
        row = self.db.query_one(sql, (dept_id,))
        if row:
            return Department(
                id=row['id'],
                name=row['name'],
                share_path=row['share_path'],
                description=row['description'] or "",
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """
        根据名称获取部门
        
        Args:
            name: 部门名称
        
        Returns:
            部门对象,不存在返回None
        """
        sql = 'SELECT * FROM departments WHERE name = ?'
        row = self.db.query_one(sql, (name,))
        if row:
            return Department(
                id=row['id'],
                name=row['name'],
                share_path=row['share_path'],
                description=row['description'] or "",
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None
    
    def get_all(self) -> List[Department]:
        """
        获取所有部门
        
        Returns:
            部门列表
        """
        sql = 'SELECT * FROM departments ORDER BY name'
        rows = self.db.query(sql)
        return [
            Department(
                id=row['id'],
                name=row['name'],
                share_path=row['share_path'],
                description=row['description'] or "",
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    def update(self, dept_id: int, name: str = None, share_path: str = None, 
               description: str = None) -> bool:
        """
        更新部门信息
        
        Args:
            dept_id: 部门ID
            name: 新名称(可选)
            share_path: 新路径(可选)
            description: 新描述(可选)
        
        Returns:
            是否更新成功
        """
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if share_path is not None:
            updates.append('share_path = ?')
            params.append(share_path)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if not updates:
            return False
        
        updates.append('updated_at = ?')
        params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        params.append(dept_id)
        
        sql = f"UPDATE departments SET {', '.join(updates)} WHERE id = ?"
        try:
            self.db.execute(sql, tuple(params))
            logger.info(f"Updated department ID {dept_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update department {dept_id}: {e}")
            return False
    
    def delete(self, dept_id: int) -> bool:
        """
        删除部门(级联删除成员和同步记录)
        
        Args:
            dept_id: 部门ID
        
        Returns:
            是否删除成功
        """
        sql = 'DELETE FROM departments WHERE id = ?'
        try:
            self.db.execute(sql, (dept_id,))
            logger.info(f"Deleted department ID {dept_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete department {dept_id}: {e}")
            return False
