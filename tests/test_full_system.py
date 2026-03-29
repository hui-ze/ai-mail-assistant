# tests/test_full_system.py
"""
全链路测试
验证 Phase 6-8 所有功能
"""
import sys
import os
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.user_profile_repo import UserProfileRepo
from src.data.todo_repo import TodoRepo
from src.data.department_repo import DepartmentRepo
from src.data.team_member_repo import TeamMemberRepo
from src.data.todo_assignment_repo import TodoAssignmentRepo
from src.data.reminder_repo import ReminderRepo
from src.core.todo_assigner import TodoAssigner
from src.core.sync_service import SyncService
from src.core.assignment_service import AssignmentService
from src.core.reminder_service import ReminderService


def test_phase6_user_profile():
    """测试 Phase 6 用户画像"""
    print("\n[Phase 6] 测试用户画像...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        repo = UserProfileRepo(db)
        
        # 测试空画像
        assert repo.is_profile_empty(), "初始画像应该为空"
        
        # 测试更新画像
        success = repo.update_profile("张三", "研发部", "工程师", "负责后端开发")
        assert success, "更新画像失败"
        
        # 测试读取画像
        profile = repo.get_profile()
        assert profile['name'] == "张三", "姓名不匹配"
        assert profile['department'] == "研发部", "部门不匹配"
        
        print("[PASS] 用户画像测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_phase6_todo_assignment():
    """测试 Phase 6 待办归属"""
    print("\n[Phase 6] 测试待办归属...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        
        # 设置用户画像
        profile_repo = UserProfileRepo(db)
        profile_repo.update_profile("张三", "研发部", "工程师", "负责后端开发")
        
        # 测试待办归属判断
        assigner = TodoAssigner(db)
        
        # 测试自己 - 发给自己的邮件
        result = assigner.analyze_assignment(
            "完成开发任务",
            email_recipients=["zhangsan@example.com"],
            email_cc=[],
            email_sender="manager@example.com",
            email_body="张三,请完成开发任务"
        )
        assert result.assign_type in ['self', 'team'], f"归属判断错误: {result.assign_type}"
        
        # 测试他人 - 发给他人的邮件
        result = assigner.analyze_assignment(
            "李四的任务",
            email_recipients=["lisi@example.com"],
            email_cc=[],
            email_sender="manager@example.com",
            email_body="李四,请完成测试"
        )
        assert result.assign_type in ['other', 'unknown'], f"归属判断错误: {result.assign_type}"
        
        print("[PASS] 待办归属测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_phase7_department():
    """测试 Phase 7 部门协作"""
    print("\n[Phase 7] 测试部门协作...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        
        # 创建部门
        dept_id = dept_repo.create("测试部门", "/shared/test")
        assert dept_id > 0, "创建部门失败"
        
        # 创建成员
        member_id = member_repo.create(dept_id, "张三", "test@example.com", "工程师", False)
        assert member_id > 0, "创建成员失败"
        
        # 查询成员
        members = member_repo.get_by_department(dept_id)
        assert len(members) == 1, "成员数量错误"
        
        print("[PASS] 部门协作测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_phase7_sync():
    """测试 Phase 7 待办同步"""
    print("\n[Phase 7] 测试待办同步...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        
        try:
            db = Database(temp_db)
            
            # 初始化数据
            dept_repo = DepartmentRepo(db)
            member_repo = TeamMemberRepo(db)
            todo_repo = TodoRepo(db)
            
            dept_id = dept_repo.create("测试部门", temp_dir)
            member_id = member_repo.create(dept_id, "张三", "test@example.com", "工程师", False)
            
            # 创建待办
            todo_repo.create_todo("测试待办", priority="高")
            
            # 测试同步
            sync_service = SyncService(db)
            result = sync_service.upload_todos(member_id)
            
            assert result.success, f"同步失败: {result.error_message}"
            assert os.path.exists(result.file_path), "同步文件未创建"
            
            print("[PASS] 待办同步测试通过")
            return True
            
        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)


def test_phase8_assignment():
    """测试 Phase 8 待办分配"""
    print("\n[Phase 8] 测试待办分配...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        
        # 初始化数据
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        todo_repo = TodoRepo(db)
        
        dept_id = dept_repo.create("测试部门", "/shared/test")
        leader_id = member_repo.create(dept_id, "领导", "leader@example.com", "Leader", True)
        member_id = member_repo.create(dept_id, "成员", "member@example.com", "工程师", False)
        
        todo_id = todo_repo.create_todo("测试任务", priority="高")
        
        # 测试分配
        assignment_service = AssignmentService(db)
        result = assignment_service.assign_todo(todo_id, leader_id, member_id, "请完成")
        
        assert result['success'], f"分配失败: {result['message']}"
        
        # 测试接受
        success = assignment_service.accept_assignment(result['assignment_id'], "好的")
        assert success, "接受失败"
        
        print("[PASS] 待办分配测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_phase8_reminder():
    """测试 Phase 8 提醒"""
    print("\n[Phase 8] 测试提醒...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        
        dept_id = dept_repo.create("测试部门", "/shared/test")
        member_id = member_repo.create(dept_id, "张三", "test@example.com", "工程师", False)
        
        # 创建提醒
        reminder_service = ReminderService(db)
        
        # 创建过期提醒
        past_time = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        reminder_id = reminder_service.create_custom_reminder(member_id, past_time, "测试提醒")
        
        assert reminder_id > 0, "创建提醒失败"
        
        # 触发提醒
        triggered = reminder_service.check_and_trigger_reminders()
        assert len(triggered) >= 1, "触发提醒失败"
        
        print("[PASS] 提醒测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_database_integrity():
    """测试数据库完整性"""
    print("\n[测试] 数据库完整性...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        db = Database(temp_db)
        
        # 验证所有表都存在
        tables = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        table_names = [t['name'] for t in tables]
        
        required_tables = [
            'accounts', 'emails', 'summaries', 'todos', 'settings',
            'ai_settings', 'ai_usage', 'user_profile',
            'departments', 'team_members', 'sync_records',
            'todo_assignments', 'reminders'
        ]
        
        for table in required_tables:
            assert table in table_names, f"表 {table} 不存在"
        
        # 验证索引
        indexes = db.query("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        assert len(indexes) >= 10, "索引数量不足"
        
        print("[PASS] 数据库完整性测试通过")
        return True
        
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("全链路测试 - Phase 6/7/8")
    print("=" * 60)
    
    tests = [
        ("数据库完整性", test_database_integrity),
        ("Phase 6 - 用户画像", test_phase6_user_profile),
        ("Phase 6 - 待办归属", test_phase6_todo_assignment),
        ("Phase 7 - 部门协作", test_phase7_department),
        ("Phase 7 - 待办同步", test_phase7_sync),
        ("Phase 8 - 待办分配", test_phase8_assignment),
        ("Phase 8 - 提醒", test_phase8_reminder),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                errors.append(f"{name}: 返回False")
        except AssertionError as e:
            failed += 1
            errors.append(f"{name}: {e}")
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            failed += 1
            errors.append(f"{name}: {str(e)}")
            print(f"[ERROR] {name}: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if errors:
        print("\n错误详情:")
        for error in errors:
            print(f"  - {error}")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
