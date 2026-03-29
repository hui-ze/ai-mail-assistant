# tests/test_database_phase6.py
"""
Phase 6 数据库层测试 - 用户画像表和待办归属字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
from src.data.database import Database


class TestPhase6Database:
    """Phase 6 数据库测试类"""
    
    def test_user_profile_table_exists(self):
        """测试 user_profile 表是否存在"""
        db = Database(':memory:')
        
        result = db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile'"
        )
        assert result is not None, "user_profile 表应该存在"
    
    def test_user_profile_initial_record(self):
        """测试 user_profile 表初始记录 id=1"""
        db = Database(':memory:')
        
        result = db.query_one(
            'SELECT * FROM user_profile WHERE id = 1'
        )
        assert result is not None, "user_profile 表应该有初始记录 id=1"
        # 检查字段存在
        assert 'name' in result.keys(), "user_profile 应该有 name 字段"
        assert 'department' in result.keys(), "user_profile 应该有 department 字段"
        assert 'role' in result.keys(), "user_profile 应该有 role 字段"
        assert 'work_description' in result.keys(), "user_profile 应该有 work_description 字段"
    
    def test_todos_new_columns(self):
        """测试 todos 表新增字段"""
        db = Database(':memory:')
        
        # 获取 todos 表结构
        result = db.query("PRAGMA table_info(todos)")
        column_names = [row[1] for row in result]
        
        # 检查新增字段
        assert 'assignee' in column_names, "todos 表应该有 assignee 字段"
        assert 'assign_type' in column_names, "todos 表应该有 assign_type 字段"
        assert 'confidence' in column_names, "todos 表应该有 confidence 字段"
        assert 'assign_reason' in column_names, "todos 表应该有 assign_reason 字段"


if __name__ == '__main__':
    # 设置UTF-8编码输出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    pytest.main([__file__, '-v', '--tb=short'])
