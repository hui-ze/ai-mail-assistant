#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Foxmail邮件智能助手 - 综合测试报告
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import time
from datetime import datetime

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试结果
test_results = []

def run_test(name, test_func):
    """运行测试并记录结果"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print('='*60)
    
    start_time = time.time()
    try:
        result = test_func()
        elapsed = time.time() - start_time
        
        if result:
            print(f"✅ 通过 (耗时: {elapsed:.2f}秒)")
            test_results.append({
                'name': name,
                'status': '通过',
                'time': elapsed,
                'error': None
            })
            return True
        else:
            print(f"❌ 失败 (耗时: {elapsed:.2f}秒)")
            test_results.append({
                'name': name,
                'status': '失败',
                'time': elapsed,
                'error': '返回False'
            })
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 异常: {str(e)} (耗时: {elapsed:.2f}秒)")
        test_results.append({
            'name': name,
            'status': '异常',
            'time': elapsed,
            'error': str(e)
        })
        return False

def test_ollama_connection():
    """测试 Ollama 连接"""
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    return response.status_code == 200

def test_ai_bridge_summary():
    """测试 AI Bridge 摘要生成"""
    from src.core.ai_bridge import AIBridge
    bridge = AIBridge(db=None)
    bridge.configure_ollama(model="qwen3:8b")
    
    result = bridge.generate_summary(
        "项目周报",
        "本周完成了用户模块开发，下周计划完成支付模块。"
    )
    return result.success

def test_ai_bridge_todos():
    """测试 AI Bridge 待办提取"""
    from src.core.ai_bridge import AIBridge
    bridge = AIBridge(db=None)
    bridge.configure_ollama(model="qwen3:8b")
    
    todos = bridge.extract_todos(
        "会议通知",
        "请准备演示PPT，提交工作总结，确认参会名单。"
    )
    return len(todos) > 0

def test_database_operations():
    """测试数据库操作"""
    from src.data.database import Database
    db = Database(":memory:")
    
    # 测试表创建
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    
    return 'accounts' in table_names and 'emails' in table_names

def test_ai_service():
    """测试 AI Service"""
    from src.data.database import Database
    from src.core.ai_service import AIService
    
    db = Database(":memory:")
    
    # 创建测试账号和邮件
    account_id = db.execute(
        "INSERT INTO accounts (email_address, imap_server) VALUES (?, ?)",
        ("test@example.com", "imap.example.com")
    )
    
    email_id = db.execute(
        """INSERT INTO emails 
        (uid, account_id, subject, sender, sender_email, recipients, date, body_text, folder)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("test-uid", account_id, "测试邮件", "发送者", "sender@test.com",
         "test@example.com", "2026-03-23", "这是一封测试邮件", "INBOX")
    )
    
    service = AIService(db)
    service.configure_ollama(model="qwen3:8b")
    
    result = service.generate_email_summary(email_id)
    return result['success']

def test_ui_creation():
    """测试 UI 创建"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from src.data.database import Database
    from src.ui.main_window import MainWindow
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication.instance() or QApplication(sys.argv)
    
    db = Database(":memory:")
    window = MainWindow(db)
    
    return window.windowTitle() == "Foxmail邮件智能助手"

def generate_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r['status'] == '通过')
    failed = sum(1 for r in test_results if r['status'] == '失败')
    errors = sum(1 for r in test_results if r['status'] == '异常')
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"异常: {errors}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print("\n详细结果:")
    print("-" * 60)
    for r in test_results:
        status_icon = "✅" if r['status'] == '通过' else "❌"
        print(f"{status_icon} {r['name']}: {r['status']} ({r['time']:.2f}秒)")
        if r['error']:
            print(f"   错误: {r['error']}")
    
    return passed == total

if __name__ == "__main__":
    print("="*60)
    print("Foxmail邮件智能助手 - 全流程测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    run_test("Ollama 连接", test_ollama_connection)
    run_test("AI Bridge 摘要生成", test_ai_bridge_summary)
    run_test("AI Bridge 待办提取", test_ai_bridge_todos)
    run_test("数据库操作", test_database_operations)
    run_test("AI Service 业务逻辑", test_ai_service)
    run_test("UI 创建", test_ui_creation)
    
    # 生成报告
    all_passed = generate_report()
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("="*60)
