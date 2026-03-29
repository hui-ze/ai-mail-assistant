# src/data/user_profile_repo.py
"""
用户画像仓储模块
管理用户个人信息、部门、角色等数据
"""
from typing import Dict, Any, Optional
from src.data.database import Database


class UserProfileRepo:
    """用户画像仓储类"""
    
    def __init__(self, db: Database):
        """
        初始化用户画像仓储
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def get_profile(self) -> Dict[str, Any]:
        """
        获取用户画像
        
        Returns:
            用户画像字典，包含 name, department, role, work_description
        """
        result = self.db.query_one("SELECT * FROM user_profile WHERE id = 1")
        if result:
            return {
                'name': result['name'],
                'department': result['department'],
                'role': result['role'],
                'work_description': result['work_description'],
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
        return {
            'name': None,
            'department': None,
            'role': None,
            'work_description': None,
            'created_at': None,
            'updated_at': None
        }
    
    def update_profile(self, name: str, department: str, 
                       role: str, work_description: str) -> bool:
        """
        更新用户画像
        
        Args:
            name: 用户姓名
            department: 部门名称
            role: 职位角色
            work_description: 工作描述
            
        Returns:
            是否更新成功
        """
        try:
            self.db.execute(
                """UPDATE user_profile 
                SET name = ?, department = ?, role = ?, work_description = ?, 
                    updated_at = datetime('now')
                WHERE id = 1""",
                (name, department, role, work_description)
            )
            return True
        except Exception as e:
            print(f"更新用户画像失败: {e}")
            return False
    
    def is_profile_empty(self) -> bool:
        """
        检查用户画像是否为空
        
        Returns:
            如果姓名为空则返回 True
        """
        profile = self.get_profile()
        return profile['name'] is None or profile['name'].strip() == ''
    
    def get_user_email(self) -> Optional[str]:
        """
        获取用户邮箱（从 accounts 表）
        
        Returns:
            第一个账号的邮箱地址，如果没有则返回 None
        """
        result = self.db.query_one(
            "SELECT email_address FROM accounts WHERE is_active = 1 LIMIT 1"
        )
        if result:
            return result['email_address']
        return None
