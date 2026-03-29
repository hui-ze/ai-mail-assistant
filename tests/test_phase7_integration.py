# tests/test_phase7_integration.py
"""
Phase 7 集成测试
部门协作功能完整测试
"""
import sys
import os
import tempfile
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.data.department_repo import DepartmentRepo
from src.data.team_member_repo import TeamMemberRepo
from src.data.todo_repo import TodoRepo
from src.data.user_profile_repo import UserProfileRepo
from src.core.sync_service import SyncService


def test_department_crud():
    """测试部门增删改查"""
    print("\n[测试] 部门CRUD操作...")
    
    db = Database(':memory:')
    repo = DepartmentRepo(db)
    
    # 创建部门
    dept_id = repo.create("研发部", "\\\\server\\shared\\rd", "研发团队")
    assert dept_id > 0, "创建部门失败"
    
    # 查询部门
    dept = repo.get_by_id(dept_id)
    assert dept is not None, "查询部门失败"
    assert dept.name == "研发部", "部门名称不匹配"
    assert dept.share_path == "\\\\server\\shared\\rd", "共享路径不匹配"
    
    # 更新部门
    repo.update(dept_id, name="研发一部", description="核心研发团队")
    dept = repo.get_by_id(dept_id)
    assert dept.name == "研发一部", "更新部门名称失败"
    
    # 查询所有部门
    all_depts = repo.get_all()
    assert len(all_depts) == 1, "查询所有部门失败"
    
    # 删除部门
    repo.delete(dept_id)
    dept = repo.get_by_id(dept_id)
    assert dept is None, "删除部门失败"
    
    print("[PASS] 部门CRUD测试通过")


def test_member_crud():
    """测试成员增删改查"""
    print("\n[测试] 成员CRUD操作...")
    
    db = Database(':memory:')
    dept_repo = DepartmentRepo(db)
    member_repo = TeamMemberRepo(db)
    
    # 创建部门
    dept_id = dept_repo.create("研发部", "/shared/rd")
    
    # 创建成员
    member_id = member_repo.create(dept_id, "张三", "zhangsan@example.com", "工程师", False)
    assert member_id > 0, "创建成员失败"
    
    # 创建Leader
    leader_id = member_repo.create(dept_id, "李四", "lisi@example.com", "经理", True)
    
    # 查询成员
    member = member_repo.get_by_id(member_id)
    assert member is not None, "查询成员失败"
    assert member.name == "张三", "成员姓名不匹配"
    assert not member.is_leader, "Leader标记错误"
    
    # 查询Leader
    leader = member_repo.get_by_id(leader_id)
    assert leader.is_leader, "Leader标记错误"
    
    # 更新成员
    member_repo.update(member_id, role="高级工程师", is_leader=True)
    member = member_repo.get_by_id(member_id)
    assert member.role == "高级工程师", "更新角色失败"
    assert member.is_leader, "更新Leader标记失败"
    
    # 查询部门成员
    members = member_repo.get_by_department(dept_id)
    assert len(members) == 2, "查询部门成员数量错误"
    
    # 查询Leader列表
    leaders = member_repo.get_leaders(dept_id)
    assert len(leaders) == 2, "查询Leader数量错误"
    
    # 统计成员数量
    count = member_repo.count_by_department(dept_id)
    assert count == 2, "成员数量统计错误"
    
    # 删除成员
    member_repo.delete(member_id)
    count = member_repo.count_by_department(dept_id)
    assert count == 1, "删除成员失败"
    
    print("[PASS] 成员CRUD测试通过")


def test_sync_service():
    """测试同步服务"""
    print("\n[测试] 同步服务...")
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        db = Database(':memory:')
        
        # 初始化数据
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        todo_repo = TodoRepo(db)
        profile_repo = UserProfileRepo(db)
        sync_service = SyncService(db)
        
        # 创建部门(使用不同的名称避免冲突)
        dept_id = dept_repo.create("测试研发部", temp_dir, "测试用研发团队")
        
        # 创建成员
        member_id = member_repo.create(dept_id, "张三", "zhangsan@example.com", "工程师", False)
        
        # 创建测试待办
        todo_repo.create_todo("完成测试用例", priority="高", assignee="张三", assign_type="self")
        todo_repo.create_todo("代码审查", priority="中", assignee="团队", assign_type="team")
        todo_repo.create_todo("文档编写", priority="低", assignee="李四", assign_type="other")
        
        # 设置用户画像
        profile_repo.update_profile("张三", "研发部", "工程师", "负责测试工作")
        
        # 测试上传
        result = sync_service.upload_todos(member_id)
        assert result.success, f"上传失败: {result.error_message}"
        assert result.todo_count == 3, f"待办数量错误: {result.todo_count}"
        assert os.path.exists(result.file_path), "同步文件未创建"
        
        # 验证文件内容
        with open(result.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['version'] == '1.0', "版本号错误"
        assert data['member']['name'] == "张三", "成员姓名错误"
        assert len(data['todos']) == 3, "待办数量错误"
        assert data['stats']['total'] == 3, "统计数据错误"
        
        # 测试下载
        result = sync_service.download_todos(member_id)
        assert result.success, f"下载失败: {result.error_message}"
        assert result.todo_count == 3, f"下载待办数量错误"
        
        # 测试获取团队待办
        team_todos = sync_service.get_team_todos(dept_id)
        assert len(team_todos) == 1, "团队待办数量错误"
        assert "zhangsan@example.com" in team_todos, "未找到成员待办"
        
        print("[PASS] 同步服务测试通过")


def test_full_department_workflow():
    """测试完整的部门协作流程"""
    print("\n[测试] 完整部门协作流程...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db = Database(':memory:')
        
        # 初始化仓库
        dept_repo = DepartmentRepo(db)
        member_repo = TeamMemberRepo(db)
        todo_repo = TodoRepo(db)
        profile_repo = UserProfileRepo(db)
        sync_service = SyncService(db)
        
        # 1. 创建部门
        dept_id = dept_repo.create("产品部", temp_dir)
        print(f"  步骤1: 创建部门 - ID: {dept_id}")
        
        # 2. 添加团队成员
        leader_id = member_repo.create(dept_id, "王经理", "wang@example.com", "产品经理", True)
        member1_id = member_repo.create(dept_id, "张三", "zhang@example.com", "产品专员", False)
        member2_id = member_repo.create(dept_id, "李四", "li@example.com", "产品专员", False)
        print(f"  步骤2: 添加3名团队成员")
        
        # 3. 成员各自创建待办
        profile_repo.update_profile("张三", "产品部", "产品专员", "负责产品规划")
        todo1 = todo_repo.create_todo("需求调研", priority="高", assignee="张三", assign_type="self")
        todo2 = todo_repo.create_todo("竞品分析", priority="中", assignee="团队", assign_type="team")
        
        profile_repo.update_profile("李四", "产品部", "产品专员", "负责用户研究")
        todo3 = todo_repo.create_todo("用户访谈", priority="高", assignee="李四", assign_type="self")
        
        print(f"  步骤3: 创建测试待办数据")
        
        # 4. 成员上传待办
        result1 = sync_service.upload_todos(member1_id)
        assert result1.success, f"成员1上传失败: {result1.error_message}"
        
        result2 = sync_service.upload_todos(member2_id)
        assert result2.success, f"成员2上传失败: {result2.error_message}"
        
        print(f"  步骤4: 成员上传待办 - 成功")
        
        # 5. Leader查看团队待办
        team_todos = sync_service.get_team_todos(dept_id)
        assert len(team_todos) == 2, f"团队待办数量错误: {len(team_todos)}"
        
        total_todos = sum(len(data.todos) for data in team_todos.values())
        print(f"  步骤5: Leader查看团队待办 - {len(team_todos)}位成员, 共{total_todos}条待办")
        
        # 6. 验证同步记录
        sync_records = db.query('SELECT COUNT(*) as count FROM sync_records WHERE status = "success"')
        assert sync_records[0]['count'] >= 2, "同步记录数量错误"
        print(f"  步骤6: 验证同步记录 - {sync_records[0]['count']}条记录")
        
        print("[PASS] 完整部门协作流程测试通过")


def test_database_migration():
    """测试数据库迁移"""
    print("\n[测试] 数据库迁移...")
    
    db = Database(':memory:')
    
    # 验证表是否创建
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    table_names = [t['name'] for t in tables]
    
    assert 'departments' in table_names, "departments表未创建"
    assert 'team_members' in table_names, "team_members表未创建"
    assert 'sync_records' in table_names, "sync_records表未创建"
    
    # 验证索引
    indexes = db.query("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    index_names = [i['name'] for i in indexes]
    
    assert 'idx_team_members_department' in index_names, "部门索引未创建"
    assert 'idx_team_members_email' in index_names, "邮箱索引未创建"
    assert 'idx_sync_records_member' in index_names, "成员同步索引未创建"
    assert 'idx_sync_records_time' in index_names, "时间同步索引未创建"
    
    print("[PASS] 数据库迁移测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Phase 7 集成测试")
    print("=" * 60)
    
    tests = [
        test_database_migration,
        test_department_crud,
        test_member_crud,
        test_sync_service,
        test_full_department_workflow
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
