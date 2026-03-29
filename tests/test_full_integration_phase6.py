# -*- coding: utf-8 -*-
"""
Phase 6 前后端全流程集成测试
测试从用户画像设置到待办归属判断的完整流程
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo
from src.data.todo_repo import TodoRepo
from src.core.ai_service import AIService
from src.core.todo_assigner import TodoAssigner


def test_full_workflow_with_assignment():
    """测试完整的待办提取和归属判断流程"""
    # 1. 初始化数据库
    db = Database(':memory:')
    
    # 2. 设置用户画像
    profile_repo = UserProfileRepo(db)
    profile_repo.update_profile(
        name="张三",
        department="产品部",
        role="产品经理",
        work_description="负责用户增长、数据分析"
    )
    
    # 3. 创建测试邮件
    email_id = db.execute(
        """INSERT INTO emails 
        (uid, account_id, subject, sender, sender_email, recipients, date, folder, body_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("test-uid-001", 1, "关于下周产品会议", "李四", "lisi@example.com", 
         "zhangsan@example.com", "2026-03-24 10:00:00", "INBOX",
         "张三，请你在周五前准备下周一产品演示的材料。我们需要展示最新的用户增长数据。")
    )
    
    # 4. 创建账号（模拟用户邮箱）
    db.execute(
        """INSERT INTO accounts 
        (email_address, display_name, imap_server, imap_port, is_active)
        VALUES (?, ?, ?, ?, ?)""",
        ("zhangsan@example.com", "张三", "imap.example.com", 993, 1)
    )
    
    # 5. 使用 TodoAssigner 进行归属判断（不依赖AI）
    assigner = TodoAssigner(db)
    todo_content = "准备下周一产品演示的材料"
    
    result = assigner.analyze_assignment(
        todo_content=todo_content,
        email_recipients=["zhangsan@example.com"],
        email_cc=[],
        email_sender="lisi@example.com",
        email_body="张三，请你在周五前准备下周一产品演示的材料。我们需要展示最新的用户增长数据。"
    )
    
    # 6. 验证归属判断结果
    assert result.assign_type in ['self', 'team'], f"归属类型应为self或team，实际为{result.assign_type}"
    assert result.confidence >= 0.0 and result.confidence <= 1.0
    assert result.assignee is not None
    assert result.assign_reason is not None
    
    print(f"[PASS] 归属判断成功: {result.to_dict()}")
    
    # 7. 创建待办项并验证存储
    todo_repo = TodoRepo(db)
    todo_id = todo_repo.create_todo(
        content=todo_content,
        email_id=email_id,
        priority="高",
        assignee=result.assignee,
        assign_type=result.assign_type,
        confidence=result.confidence,
        assign_reason=result.assign_reason
    )
    
    # 8. 验证待办项已正确存储
    todo_dict = todo_repo.get_todo_by_id(todo_id)
    assert todo_dict is not None
    assert todo_dict['content'] == todo_content
    assert todo_dict['assign_type'] == result.assign_type
    assert todo_dict['assignee'] == result.assignee
    assert todo_dict['confidence'] == result.confidence
    
    print(f"[PASS] 待办项存储成功: ID={todo_id}")


def test_assignment_with_different_scenarios():
    """测试不同场景下的归属判断"""
    db = Database(':memory:')
    profile_repo = UserProfileRepo(db)
    assigner = TodoAssigner(db)
    todo_repo = TodoRepo(db)
    
    # 设置用户画像
    profile_repo.update_profile(
        name="王五",
        department="技术部",
        role="后端工程师",
        work_description="负责服务器开发和数据库优化"
    )
    
    # 创建账号
    db.execute(
        "INSERT INTO accounts (email_address, display_name, imap_server, imap_port, is_active) VALUES (?, ?, ?, ?, ?)",
        ("wangwu@example.com", "王五", "imap.example.com", 993, 1)
    )
    
    print("\n测试场景1: 直接收件人且内容匹配职责")
    result1 = assigner.analyze_assignment(
        todo_content="优化数据库查询性能",
        email_recipients=["wangwu@example.com"],
        email_cc=[],
        email_sender="lisi@example.com",
        email_body="王五，请优化数据库查询性能"
    )
    assert result1.assign_type == 'self'
    print(f"  结果: {result1.assign_type} (置信度: {result1.confidence})")
    
    print("\n测试场景2: 不在收件人列表")
    result2 = assigner.analyze_assignment(
        todo_content="处理前端页面设计",
        email_recipients=["lisi@example.com"],
        email_cc=["wangwu@example.com"],
        email_sender="zhangsan@example.com",
        email_body="@李四 请处理前端页面设计"
    )
    # 用户在抄送列表
    print(f"  结果: {result2.assign_type} (置信度: {result2.confidence})")
    
    print("\n测试场景3: 团队邮件")
    result3 = assigner.analyze_assignment(
        todo_content="参加技术分享会",
        email_recipients=["tech-team@example.com"],
        email_cc=[],
        email_sender="lisi@example.com",
        email_body="技术部全员参加下周的技术分享会"
    )
    assert result3.assign_type == 'team'
    print(f"  结果: {result3.assign_type} (置信度: {result3.confidence})")


def test_profile_update_workflow():
    """测试用户画像更新工作流"""
    db = Database(':memory:')
    profile_repo = UserProfileRepo(db)
    
    # 清空用户画像（确保初始状态）
    profile_repo.update_profile(name="", department="", role="", work_description="")
    
    # 验证画像为空
    assert profile_repo.is_profile_empty() is True
    
    # 更新画像
    success = profile_repo.update_profile(
        name="测试用户",
        department="测试部门",
        role="测试工程师",
        work_description="负责测试工作"
    )
    assert success is True
    
    # 验证画像不为空
    assert profile_repo.is_profile_empty() is False
    
    # 获取画像
    profile = profile_repo.get_profile()
    assert profile['name'] == "测试用户"
    assert profile['department'] == "测试部门"
    
    # 再次更新
    profile_repo.update_profile(
        name="修改后用户",
        department="修改后部门",
        role="高级工程师",
        work_description="负责核心开发"
    )
    
    # 验证更新成功
    profile = profile_repo.get_profile()
    assert profile['name'] == "修改后用户"
    assert profile['role'] == "高级工程师"


def test_todo_crud_with_assignment():
    """测试待办项CRUD操作包含归属字段"""
    db = Database(':memory:')
    todo_repo = TodoRepo(db)
    
    # 创建待办
    todo_id = todo_repo.create_todo(
        content="测试待办项",
        email_id=1,
        priority="高",
        assignee="测试用户",
        assign_type="self",
        confidence=0.95,
        assign_reason="测试创建"
    )
    
    assert todo_id > 0
    
    # 读取待办
    todo = todo_repo.get_todo_by_id(todo_id)
    assert todo['content'] == "测试待办项"
    assert todo['assign_type'] == "self"
    assert todo['assignee'] == "测试用户"
    assert todo['confidence'] == 0.95
    
    # 获取所有待办
    todos = todo_repo.get_all_todos()
    # 验证创建成功（可能已有其他测试数据）
    assert any(t['id'] == todo_id for t in todos)
    
    # 更新状态
    todo_repo.update_todo_status(todo_id, True)
    todo = todo_repo.get_todo_by_id(todo_id)
    assert todo['completed'] is True
    
    # 删除待办
    todo_repo.delete_todo(todo_id)
    todo = todo_repo.get_todo_by_id(todo_id)
    assert todo is None


def test_database_schema():
    """测试数据库表结构正确"""
    db = Database(':memory:')
    
    # 检查 user_profile 表
    result = db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'"
    )
    assert result is not None, "user_profile 表应该存在"
    
    # 检查 user_profile 初始记录
    result = db.query_one("SELECT * FROM user_profile WHERE id = 1")
    assert result is not None, "user_profile 应该有初始记录"
    
    # 检查 todos 表新增字段
    email_id = db.execute(
        "INSERT INTO emails (uid, account_id, subject, sender, sender_email, recipients, date, folder) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("test", 1, "test", "test", "test@test.com", "test@test.com", "2026-03-24", "INBOX")
    )
    
    todo_id = db.execute(
        "INSERT INTO todos (email_id, content, assignee, assign_type, confidence, assign_reason) VALUES (?, ?, ?, ?, ?, ?)",
        (email_id, "Test", "张三", "self", 0.95, "测试")
    )
    
    result = db.query_one("SELECT * FROM todos WHERE id = ?", (todo_id,))
    assert result['assignee'] == "张三"
    assert result['assign_type'] == "self"
    assert result['confidence'] == 0.95


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
