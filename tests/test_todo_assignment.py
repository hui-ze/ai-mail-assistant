# tests/test_todo_assignment.py
"""
待办归属判断测试
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo
from src.core.todo_assigner import TodoAssigner, AssignmentResult


class TestTodoAssigner:
    """待办归属判断测试类"""
    
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
    
    @pytest.fixture
    def setup_profile(self, temp_db):
        """设置用户画像"""
        repo = UserProfileRepo(temp_db)
        repo.update_profile(
            name="张三",
            department="产品部",
            role="产品经理",
            work_description="负责用户增长和数据分析"
        )
        return repo
    
    def test_direct_recipient_assignment(self, temp_db, setup_profile):
        """测试直接收件人归属判断"""
        # 添加用户邮箱到 accounts 表
        temp_db.execute(
            "INSERT INTO accounts (email_address, display_name, imap_server, imap_port) VALUES (?, ?, ?, ?)",
            ("zhangsan@example.com", "张三", "imap.example.com", 993)
        )
        
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="准备本周周报",
            email_recipients=["zhangsan@example.com"],
            email_cc=[],
            email_sender="boss@example.com",
            email_body="张三，请准备本周周报"
        )
        
        assert result.success is True
        assert result.assign_type == "self"
        assert result.confidence >= 0.9
    
    def test_name_mention_assignment(self, temp_db, setup_profile):
        """测试姓名提及归属判断"""
        # 添加用户邮箱到 accounts 表
        temp_db.execute(
            "INSERT INTO accounts (email_address, display_name, imap_server, imap_port) VALUES (?, ?, ?, ?)",
            ("zhangsan@example.com", "张三", "imap.example.com", 993)
        )
        
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="准备产品演示材料",
            email_recipients=["team@example.com"],
            email_cc=["zhangsan@example.com"],
            email_sender="boss@example.com",
            email_body="张三，这个演示材料你负责一下"
        )
        
        assert result.success is True
        assert result.assign_type == "self"
        assert "张三" in result.assign_reason or "姓名" in result.assign_reason
    
    def test_role_based_assignment(self, temp_db, setup_profile):
        """测试基于角色的归属判断"""
        # 添加用户邮箱到 accounts 表
        temp_db.execute(
            "INSERT INTO accounts (email_address, display_name, imap_server, imap_port) VALUES (?, ?, ?, ?)",
            ("zhangsan@example.com", "张三", "imap.example.com", 993)
        )
        
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="分析用户增长数据",
            email_recipients=["product-team@example.com"],
            email_cc=[],
            email_sender="ceo@example.com",
            email_body="需要产品经理分析下用户增长数据"
        )
        
        assert result.success is True
        assert result.assign_type == "self"
        assert result.confidence >= 0.7
    
    def test_other_person_assignment(self, temp_db, setup_profile):
        """测试归属他人"""
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="设计新功能原型",
            email_recipients=["lisi@example.com"],
            email_cc=["zhangsan@example.com"],
            email_sender="boss@example.com",
            email_body="李四，你负责设计这个新功能原型"
        )
        
        assert result.success is True
        assert result.assign_type == "other"
        assert "李四" in result.assignee or "lisi" in result.assignee.lower()
    
    def test_team_assignment(self, temp_db, setup_profile):
        """测试团队待办"""
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="准备部门团建活动",
            email_recipients=["product-team@example.com"],
            email_cc=[],
            email_sender="hr@example.com",
            email_body="产品部全体成员一起准备团建活动"
        )
        
        assert result.success is True
        assert result.assign_type == "team"
    
    def test_unknown_assignment(self, temp_db, setup_profile):
        """测试无法确定归属"""
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="完成项目报告",
            email_recipients=["all@example.com"],
            email_cc=[],
            email_sender="boss@example.com",
            email_body="请相关人员完成项目报告"
        )
        
        assert result.success is True
        # 可能是 unknown 或 team
        assert result.assign_type in ["unknown", "team"]
    
    def test_empty_profile_assignment(self, temp_db):
        """测试用户画像为空时的归属判断"""
        assigner = TodoAssigner(temp_db)
        
        result = assigner.analyze_assignment(
            todo_content="准备周报",
            email_recipients=["someone@example.com"],
            email_cc=[],
            email_sender="boss@example.com",
            email_body="请准备周报"
        )
        
        # 画像为空时应该返回 unknown
        assert result.success is True
        assert result.assign_type == "unknown"
    
    def test_batch_assignment(self, temp_db, setup_profile):
        """测试批量归属判断"""
        assigner = TodoAssigner(temp_db)
        
        todos = [
            "准备本周周报",
            "分析用户增长数据",
            "设计新功能原型"
        ]
        
        email_context = {
            "recipients": ["zhangsan@example.com"],
            "cc": [],
            "sender": "boss@example.com",
            "body": "张三，准备周报和分析数据，李四负责原型设计"
        }
        
        results = assigner.batch_analyze(todos, email_context)
        
        assert len(results) == 3
        assert all(r.success for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
