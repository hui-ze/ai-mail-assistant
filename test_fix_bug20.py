# -*- coding: utf-8 -*-
"""
测试修复：Bug #20 - 云端API配置重启后丢失
"""

import sys
import os
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.core.ai_bridge import AIBridge, AIProvider


def test_bug20():
    """测试Bug #20: 云端API配置持久化"""
    print("\n=== 测试 Bug #20: 云端API配置持久化 ===")
    
    # 创建内存数据库
    db = Database(':memory:')
    
    # 第一次配置
    print("\n1. 第一次配置云端API...")
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
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Bug修复验证测试")
    print("=" * 60)
    
    try:
        result = test_bug20()
        
        if result:
            print("\n" + "=" * 60)
            print("[PASS] 所有测试通过！")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n[FAIL] 测试失败")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
