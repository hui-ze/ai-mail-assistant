#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 AI Bridge 模块
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ai_bridge import AIBridge, AIProvider, OllamaConfig
import time

def test_ai_bridge():
    print("=" * 60)
    print("测试 AI Bridge 模块")
    print("=" * 60)
    
    # 创建 AI Bridge 实例（不使用数据库）
    bridge = AIBridge(db=None)
    
    # 配置 Ollama
    print("\n[1] 配置 Ollama 模型")
    bridge.configure_ollama(
        base_url="http://localhost:11434",
        model="qwen3:8b"
    )
    print(f"当前提供商: {bridge.get_current_provider()}")
    print(f"服务可用: {bridge.is_available()}")
    
    # 测试摘要生成
    print("\n[2] 测试邮件摘要生成")
    test_email = {
        "subject": "项目进度报告 - 2026年3月第三周",
        "body": """
张总您好，

本周项目进展如下：

1. 完成了用户登录模块的开发和测试
2. 修复了3个关键Bug（详见附件）
3. 下周计划：开始开发支付集成功能

需要您确认的事项：
- 请在周五前审批预算申请
- 安排下周的技术评审会议
- 确认第三方API的采购计划

此致
李明
项目组
        """.strip()
    }
    
    start_time = time.time()
    result = bridge.generate_summary(test_email["subject"], test_email["body"])
    elapsed = time.time() - start_time
    
    if result.success:
        print(f"\n✅ 摘要生成成功 (耗时: {elapsed:.2f}秒)")
        print(f"使用模型: {result.model_used}")
        print(f"Token数: {result.tokens_used}")
        print(f"\n摘要内容:")
        print(f"  {result.summary}")
        
        if result.todos:
            print(f"\n提取的待办事项 ({len(result.todos)} 项):")
            for i, todo in enumerate(result.todos, 1):
                print(f"  {i}. {todo}")
    else:
        print(f"❌ 摘要生成失败: {result.error}")
    
    # 测试待办提取
    print("\n[3] 测试待办事项提取")
    test_email2 = {
        "subject": "会议通知",
        "body": """
各位同事，

提醒大家参加明天下午3点的项目启动会议。

需要准备：
1. 准备项目演示PPT
2. 提交本周工作总结
3. 确认参会人员名单

会议地点：3楼会议室A
时间：明天下午3点

请务必准时参加。
        """.strip()
    }
    
    start_time = time.time()
    todos = bridge.extract_todos(test_email2["subject"], test_email2["body"])
    elapsed = time.time() - start_time
    
    print(f"\n✅ 待办提取完成 (耗时: {elapsed:.2f}秒)")
    print(f"提取到 {len(todos)} 个待办事项:")
    for i, todo in enumerate(todos, 1):
        print(f"  {i}. {todo}")
    
    # 获取可用模型
    print("\n[4] 获取可用模型列表")
    models = bridge.get_available_models()
    print(f"可用模型: {models}")
    
    # 使用统计
    print("\n[5] 使用统计")
    stats = bridge.get_usage_stats()
    print(f"统计: {stats}")
    
    return result.success

if __name__ == "__main__":
    success = test_ai_bridge()
    print("\n" + "=" * 60)
    if success:
        print("✅ AI Bridge 测试全部通过")
    else:
        print("❌ AI Bridge 测试失败")
    print("=" * 60)
