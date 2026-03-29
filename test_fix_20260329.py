# -*- coding: utf-8 -*-
"""
测试修复：Bug #20-21
- Bug #20: 云端API配置重启后丢失
- Bug #21: 日历设置方框显示问题
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from src.data.database import Database
from src.core.ai_bridge import AIBridge, AIProvider


def test_bug20_cloud_api_persistence():
    """测试Bug #20: 云端API配置持久化"""
    print("\n=== 测试 Bug #20: 云端API配置持久化 ===")
    
    # 创建内存数据库
    db = Database(':memory:')
    
    # 第一次配置
    print("1. 第一次配置云端API...")
    bridge1 = AIBridge(db)
    bridge1.configure_cloud(AIProvider.DEEPSEEK, "test-api-key-123", "deepseek-chat")
    
    # 验证配置已保存
    settings = bridge1._load_ai_settings()
    assert settings.get("provider") == "deepseek", f"提供商应为deepseek，实际为{settings.get('provider')}"
    assert settings.get("api_key") == "test-api-key-123", f"API密钥应为test-api-key-123，实际为{settings.get('api_key')}"
    assert settings.get("model") == "deepseek-chat", f"模型应为deepseek-chat，实际为{settings.get('model')}"
    assert settings.get("base_url") == "https://api.deepseek.com/v1/chat/completions", f"base_url不正确"
    print("[OK] 配置保存成功")
    print(f"  - provider: {settings.get('provider')}")
    print(f"  - api_key: {settings.get('api_key')}")
    print(f"  - model: {settings.get('model')}")
    print(f"  - base_url: {settings.get('base_url')}")
    
    # 模拟重启应用（重新创建AIBridge）
    print("\n2. 模拟重启应用...")
    bridge2 = AIBridge(db)
    
    # 验证配置已加载
    assert bridge2.current_provider == AIProvider.DEEPSEEK, f"提供商应为DEEPSEEK，实际为{bridge2.current_provider}"
    assert bridge2.cloud_config.api_key == "test-api-key-123", f"API密钥应为test-api-key-123，实际为{bridge2.cloud_config.api_key}"
    assert bridge2.cloud_config.model == "deepseek-chat", f"模型应为deepseek-chat，实际为{bridge2.cloud_config.model}"
    print("[OK] 配置加载成功")
    print(f"  - current_provider: {bridge2.current_provider.value}")
    print(f"  - cloud_config.api_key: {bridge2.cloud_config.api_key}")
    print(f"  - cloud_config.model: {bridge2.cloud_config.model}")
    
    print("\n[PASS] Bug #20 修复验证通过")


def test_bug21_calendar_ui():
    """测试Bug #21: 日历设置UI布局"""
    print("\n=== 测试 Bug #21: 日历设置UI布局 ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    from src.ui.settings_dialog import SettingsDialog
    
    db = Database(':memory:')
    dialog = SettingsDialog(db)
    
    # 检查日历设置页面的布局
    print("1. 检查同步选项...")
    assert dialog.sync_high_priority is not None, "sync_high_priority 不存在"
    assert dialog.set_reminder is not None, "set_reminder 不存在"
    assert dialog.reminder_minutes is not None, "reminder_minutes 不存在"
    print("[OK] 同步选项布局正确")
    
    print("2. 检查待同步待办列表...")
    assert dialog.todo_list is not None, "todo_list 不存在"
    assert dialog.todo_list.minimumHeight() >= 120, f"最小高度应为120，实际为{dialog.todo_list.minimumHeight()}"
    assert dialog.todo_list.maximumHeight() <= 200, f"最大高度应为200，实际为{dialog.todo_list.maximumHeight()}"
    print(f"[OK] 待办列表高度正确: {dialog.todo_list.minimumHeight()}-{dialog.todo_list.maximumHeight()}")
    
    print("3. 检查Outlook设置...")
    assert dialog.outlook_account is not None, "outlook_account 不存在"
    assert dialog.outlook_status is not None, "outlook_status 不存在"
    print("[OK] Outlook设置布局正确")
    
    print("\n[PASS] Bug #21 修复验证通过")


if __name__ == "__main__":
    print("=" * 60)
    print("Bug修复验证测试")
    print("=" * 60)
    
    try:
        test_bug20_cloud_api_persistence()
        test_bug21_calendar_ui()
        
        print("\n" + "=" * 60)
        print("[PASS] 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
