# tests/test_phase8_integration.py
"""
Phase 8 集成测试
待办分配与提醒功能完整测试
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.todo_assignment_repo import TodoAssignmentRepo
from src.data.reminder_repo import ReminderRepo
from src.data.todo_repo import TodoRepo
from src.data.team_member_repo import TeamMemberRepo
from src.data.department_repo import DepartmentRepo
from src.core.assignment_service import AssignmentService
from src.core.reminder_service import ReminderService


def test_database_migration():
    """测试数据库迁移"""
    print("\n[测试] 数据库迁移...")
    
    db = Database(':memory:')
    
    # 验证表是否创建
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    table_names = [t['name'] for t in tables]
    
    assert 'todo_assignments' in table_names, "todo_assignments表未创建"
    assert 'reminders' in table_names, "reminders表未创建"
    
    # 验证索引
    indexes = db.query("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    index_names = [i['name'] for i in indexes]
    
    assert 'idx_assignments_todo' in index_names, "待办分配索引未创建"
    assert 'idx_assignments_to_member' in index_names, "接收成员索引未创建"
    assert 'idx_reminders_member' in index_names, "提醒成员索引未创建"
    assert 'idx_reminders_time' in index_names, "提醒时间索引未创建"
    
    print("[PASS] 数据库迁移测试通过")


def test_assignment_crud():
    """测试分配CRUD操作"""
    print("\n[测试] 分配CRUD操作...")
    
    db = Database(':memory:')
    assignment_repo = TodoAssignmentRepo(db)
    
    # 创建分配
    assignment_id = assignment_repo.create(
        todo_id=1, from_member_id=1, to_member_id=2, 
        message="请尽快处理"
    )
    assert assignment_id > 0, "创建分配失败"
    
    # 查询分配
    assignment = assignment_repo.get_by_id(assignment_id)
    assert assignment is not None, "查询分配失败"
    assert assignment.status == "pending", "初始状态错误"
    assert assignment.message == "请尽快处理", "分配说明错误"
    
    # 接受分配
    assignment_repo.accept(assignment_id, "好的,我会处理")
    assignment = assignment_repo.get_by_id(assignment_id)
    assert assignment.status == "accepted", "接受状态错误"
    assert assignment.response_message == "好的,我会处理", "回复说明错误"
    
    # 拒绝分配(创建新分配测试)
    assignment_id2 = assignment_repo.create(2, 1, 2, "另一个任务")
    assignment_repo.reject(assignment_id2, "时间不够")
    assignment = assignment_repo.get_by_id(assignment_id2)
    assert assignment.status == "rejected", "拒绝状态错误"
    
    # 查询待处理分配
    pending = assignment_repo.get_pending_by_member(2)
    assert len(pending) == 0, "待处理分配数量错误"
    
    # 查询分配历史
    history = assignment_repo.get_by_todo(1)
    assert len(history) == 1, "分配历史数量错误"
    
    print("[PASS] 分配CRUD测试通过")


def test_reminder_crud():
    """测试提醒CRUD操作"""
    print("\n[测试] 提醒CRUD操作...")
    
    db = Database(':memory:')
    reminder_repo = ReminderRepo(db)
    
    # 创建提醒
    remind_at = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    reminder_id = reminder_repo.create(
        member_id=1, reminder_type='due_date',
        remind_at=remind_at, message="待办即将到期",
        todo_id=1
    )
    assert reminder_id > 0, "创建提醒失败"
    
    # 查询提醒
    reminder = reminder_repo.get_by_id(reminder_id)
    assert reminder is not None, "查询提醒失败"
    assert reminder.reminder_type == "due_date", "提醒类型错误"
    assert not reminder.is_sent, "初始发送状态错误"
    
    # 标记已发送
    reminder_repo.mark_sent(reminder_id)
    reminder = reminder_repo.get_by_id(reminder_id)
    assert reminder.is_sent, "标记发送状态失败"
    
    # 查询待发送提醒
    pending = reminder_repo.get_pending_by_member(1)
    assert len(pending) == 0, "待发送提醒数量错误"
    
    # 创建到期提醒
    now = datetime.now()
    past_time = (now - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
    reminder_id2 = reminder_repo.create(1, 'custom', past_time, "过期提醒")
    
    due_reminders = reminder_repo.get_due_reminders()
    assert len(due_reminders) == 1, "到期提醒数量错误"
    assert due_reminders[0].id == reminder_id2, "到期提醒ID错误"
    
    print("[PASS] 提醒CRUD测试通过")


def test_auto_reminders():
    """测试自动创建截止提醒"""
    print("\n[测试] 自动截止提醒...")
    
    db = Database(':memory:')
    reminder_repo = ReminderRepo(db)
    
    # 设置截止日期为明天
    due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 创建自动提醒
    reminder_ids = reminder_repo.create_auto_reminders(
        todo_id=1, member_id=1,
        due_date=due_date, todo_title="测试待办"
    )
    
    # 应该创建1天和1小时的提醒(10分钟已过期)
    assert len(reminder_ids) >= 1, "自动提醒创建失败"
    
    # 验证提醒内容
    for rid in reminder_ids:
        reminder = reminder_repo.get_by_id(rid)
        assert reminder.reminder_type == "due_date", "提醒类型错误"
        assert "测试待办" in reminder.message, "提醒消息错误"
    
    print("[PASS] 自动截止提醒测试通过")


def test_assignment_service():
    """测试分配服务"""
    print("\n[测试] 分配服务...")
    
    # 使用临时文件数据库
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    
    try:
        db = Database(temp_db_path)
        
        # 初始化基础数据
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        todo_repo = TodoRepo(db)
        
        # 创建部门
        dept_id = dept_repo.create("测试研发部-独立", "/shared/rd")  # 使用完全不同的名称
        
        # 创建成员
        member1_id = member_repo.create(dept_id, "张三-独立", "zhang_independent@example.com", "Leader", True)
        member2_id = member_repo.create(dept_id, "李四-独立", "li_independent@example.com", "工程师", False)
        
        # 创建待办
        todo_id = todo_repo.create_todo("完成Phase 8开发-独立测试", priority="高")  # 使用完全不同的标题
        
        # 初始化服务
        assignment_service = AssignmentService(db)
        
        # 测试分配
        result = assignment_service.assign_todo(
            todo_id, member1_id, member2_id, "请在本周内完成"
        )
        
        assert result['success'], f"分配失败: {result['message']}"
        assert 'assignment_id' in result, "缺少assignment_id"
        
        # 验证分配创建
        assignment_id = result['assignment_id']
        pending = assignment_service.get_pending_assignments(member2_id)
        assert len(pending) == 1, "待处理分配数量错误"
        assert pending[0]['assignment'].id == assignment_id, "分配ID不匹配"
        
        # 测试接受分配
        success = assignment_service.accept_assignment(assignment_id, "好的,我会尽快完成")
        assert success, "接受分配失败"
        
        # 验证状态更新
        pending = assignment_service.get_pending_assignments(member2_id)
        assert len(pending) == 0, "接受后不应有待处理分配"
        
        # 测试分配历史
        history = assignment_service.get_assignment_history(todo_id)
        assert len(history) == 1, "分配历史数量错误"
        assert history[0]['assignment'].status == "accepted", "历史状态错误"
        
        print("[PASS] 分配服务测试通过")
        
    finally:
        # 清理临时数据库
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_reminder_service():
    """测试提醒服务"""
    print("\n[测试] 提醒服务...")
    
    # 使用临时文件数据库
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    
    try:
        db = Database(temp_db_path)
        
        # 初始化数据
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        dept_id = dept_repo.create("测试部门-独立", "/shared/test")
        member_id = member_repo.create(dept_id, "张三-独立", "test_independent@example.com", "工程师", False)
        
        # 初始化服务
        reminder_service = ReminderService(db)
        
        # 创建自定义提醒
        remind_at = (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        reminder_id = reminder_service.create_custom_reminder(
            member_id, remind_at, "自定义提醒测试"
        )
        assert reminder_id > 0, "创建自定义提醒失败"
        
        # 获取待发送提醒
        pending = reminder_service.get_pending_reminders(member_id)
        assert len(pending) == 1, "待发送提醒数量错误"
        
        # 获取提醒统计
        stats = reminder_service.get_reminder_stats(member_id)
        assert stats['pending'] == 1, "待发送统计错误"
        
        # 创建过期提醒
        past_time = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        expired_id = reminder_service.create_custom_reminder(member_id, past_time, "过期提醒")
        
        # 触发提醒检查
        triggered = reminder_service.check_and_trigger_reminders()
        
        # 只应该触发过期提醒
        assert len(triggered) >= 1, "触发提醒数量错误"
        assert any(t['reminder'].id == expired_id for t in triggered), "未找到过期提醒"
        
        # 验证已发送
        pending = reminder_service.get_pending_reminders(member_id)
        assert len(pending) == 1, "触发后待发送数量错误"  # 只剩未来提醒
        assert pending[0].id == reminder_id, "剩余提醒ID错误"
        
        print("[PASS] 提醒服务测试通过")
        
    finally:
        # 清理临时数据库
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_full_workflow():
    """测试完整工作流"""
    print("\n[测试] 完整工作流...")
    
    # 使用文件临时数据库确保完全独立
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    
    try:
        db = Database(temp_db_path)
        
        # 初始化所有仓库和服务
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        todo_repo = TodoRepo(db)
        assignment_service = AssignmentService(db)
        reminder_service = ReminderService(db)
        
        # 1. 创建部门和成员
        dept_id = dept_repo.create("产品部-测试", "/shared/product")
        leader_id = member_repo.create(dept_id, "王经理-测试", "wang_test@example.com", "产品经理", True)
        member_id = member_repo.create(dept_id, "李四-测试", "li_test@example.com", "产品专员", False)
        
        print("  步骤1: 创建部门和成员")
        
        # 2. 创建待办(带截止日期)
        due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        todo_id = todo_repo.create_todo(
            "完成产品需求文档-测试", priority="高",
            due_date=due_date
        )
        
        print("  步骤2: 创建待办")
        
        # 3. 分配待办
        result = assignment_service.assign_todo(
            todo_id, leader_id, member_id, "请在明天下午前完成初稿"
        )
        assert result['success'], "分配失败"
        assignment_id = result['assignment_id']
        
        print("  步骤3: 分配待办给成员")
        
        # 4. 验证自动提醒
        pending_reminders = reminder_service.get_pending_reminders(member_id)
        assert len(pending_reminders) >= 2, "自动提醒创建失败"  # assignment + due_date提醒
        
        print(f"  步骤4: 自动创建{len(pending_reminders)}个提醒")
        
        # 5. 成员接受分配
        success = assignment_service.accept_assignment(assignment_id, "收到,开始处理")
        assert success, "接受分配失败"
        
        print("  步骤5: 成员接受分配")
        
        # 6. 验证分配历史
        history = assignment_service.get_assignment_history(todo_id)
        assert len(history) == 1, f"分配历史错误: 应该有1条历史,实际有{len(history)}条"
        assert history[0]['assignment'].status == "accepted", "最终状态错误"
        
        print("  步骤6: 验证分配历史")
        
        # 7. 验证提醒统计
        stats = reminder_service.get_reminder_stats(member_id)
        assert stats['pending'] >= 2, "提醒统计错误"
        
        print(f"  步骤7: 验证提醒统计 - {stats['pending']}个待发送")
        
        print("[PASS] 完整工作流测试通过")
        
    finally:
        # 清理临时数据库
        import os
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Phase 8 集成测试")
    print("=" * 60)
    
    tests = [
        test_database_migration,
        test_assignment_crud,
        test_reminder_crud,
        test_auto_reminders,
        test_assignment_service,
        test_reminder_service,
        test_full_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
