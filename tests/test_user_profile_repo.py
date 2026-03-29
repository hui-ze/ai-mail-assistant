# tests/test_user_profile_repo.py
"""
用户画像仓储测试
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo


class TestUserProfileRepo:
    """用户画像仓储测试类"""
    
    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        db = Database(path)
        yield db
        # 清理
        try:
            os.unlink(path)
        except:
            pass
    
    def test_get_empty_profile(self, temp_db):
        """测试获取空用户画像"""
        repo = UserProfileRepo(temp_db)
        
        profile = repo.get_profile()
        assert profile['name'] is None
        assert profile['department'] is None
        assert profile['role'] is None
    
    def test_update_profile(self, temp_db):
        """测试更新用户画像"""
        repo = UserProfileRepo(temp_db)
        
        # 更新画像
        success = repo.update_profile(
            name="张三",
            department="产品部",
            role="产品经理",
            work_description="负责用户增长和数据分析"
        )
        assert success is True
        
        # 验证更新
        profile = repo.get_profile()
        assert profile['name'] == "张三"
        assert profile['department'] == "产品部"
        assert profile['role'] == "产品经理"
        assert "用户增长" in profile['work_description']
    
    def test_is_profile_empty(self, temp_db):
        """测试检查画像是否为空"""
        repo = UserProfileRepo(temp_db)
        
        # 初始为空
        assert repo.is_profile_empty() is True
        
        # 填写姓名后不为空
        repo.update_profile(name="张三", department="", role="", work_description="")
        assert repo.is_profile_empty() is False
    
    def test_get_user_email(self, temp_db):
        """测试获取用户邮箱（从 accounts 表）"""
        repo = UserProfileRepo(temp_db)
        
        # 创建测试账号
        temp_db.execute(
            "INSERT INTO accounts (email_address, display_name, imap_server, imap_port) VALUES (?, ?, ?, ?)",
            ("zhangsan@example.com", "张三", "imap.example.com", 993)
        )
        
        email = repo.get_user_email()
        assert email == "zhangsan@example.com"
    
    def test_get_user_email_no_account(self, temp_db):
        """测试没有账号时获取用户邮箱"""
        repo = UserProfileRepo(temp_db)
        
        email = repo.get_user_email()
        assert email is None


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    pytest.main([__file__, '-v', '--tb=short'])
