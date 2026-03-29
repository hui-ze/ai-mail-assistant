#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 AI Service 层和数据库层
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import Database
from src.core.ai_service import AIService
from src.data.email_repo import EmailRepo
import time

def test_database():
    print("=" * 60)
    print("测试数据库层")
    print("=" * 60)
    
    # 使用内存数据库进行测试
    print("\n[1] 创建内存数据库")
    db = Database(":memory:")
    print("✅ 数据库创建成功")
    
    # 测试数据库表
    print("\n[2] 验证数据库表结构")
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    print(f"创建的表: {table_names}")
    
    expected_tables = ['accounts', 'emails', 'summaries', 'todos', 'settings', 'ai_settings', 'ai_usage', 'calendar_events']
    for table in expected_tables:
        if table in table_names:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} 缺失")
    
    return db

def test_email_repo(db):
    print("\n" + "=" * 60)
    print("测试邮件仓储层")
    print("=" * 60)
    
    repo = EmailRepo(db)
    
    # 创建测试账号（直接使用数据库）
    print("\n[1] 创建测试账号")
    account_id = db.execute(
        """INSERT INTO accounts 
        (email_address, display_name, imap_server, imap_port, smtp_server, smtp_port, auth_code_encrypted, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("test@example.com", "测试账号", "imap.example.com", 993, 
         "smtp.example.com", 465, "test123", 1)
    )
    print(f"✅ 账号创建成功，ID: {account_id}")
    
    # 创建测试邮件（直接使用数据库）
    print("\n[2] 创建测试邮件")
    email_id = db.execute(
        """INSERT INTO emails 
        (uid, account_id, subject, sender, sender_email, recipients, date, body_text, body_html, folder, is_read, processed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("test-uid-123", account_id, "项目周报 - 第12周",
         "张三", "zhangsan@example.com", "test@example.com",
         "2026-03-23 10:00:00",
         """各位领导好，

本周项目进展如下：

已完成工作：
1. 完成用户模块开发
2. 修复了5个Bug
3. 优化了数据库查询性能

下周计划：
- 完成支付模块开发
- 进行压力测试
- 准备上线材料

需要确认：
- 请在周五前审批预算申请
- 确认第三方服务商合作方案

此致
张三""",
         "", "INBOX", 0, 0)
    )
    print(f"✅ 邮件创建成功，ID: {email_id}")
    
    # 查询邮件
    print("\n[3] 查询邮件")
    email = repo.get_email_by_id(email_id)
    if email:
        print(f"主题: {email['subject']}")
        print(f"发件人: {email['sender']}")
        print(f"内容长度: {len(email['body_text'])} 字符")
    
    return email_id

def test_ai_service(db, email_id):
    print("\n" + "=" * 60)
    print("测试 AI Service 层")
    print("=" * 60)
    
    service = AIService(db)
    
    # 配置 Ollama
    print("\n[1] 配置 AI 服务")
    service.configure_ollama(
        base_url="http://localhost:11434",
        model="qwen3:8b"
    )
    
    status = service.get_ai_status()
    print(f"AI 可用: {status['available']}")
    print(f"提供商: {status['provider']}")
    print(f"可用模型数: {len(status['models'])}")
    
    # 生成邮件摘要
    print("\n[2] 生成邮件摘要")
    start_time = time.time()
    result = service.generate_email_summary(email_id)
    elapsed = time.time() - start_time
    
    if result['success']:
        print(f"✅ 摘要生成成功 (耗时: {elapsed:.2f}秒)")
        if result.get('cached'):
            print("  (使用缓存)")
        else:
            summary = result.get('summary', {})
            print(f"  摘要ID: {summary.get('id')}")
            print(f"  模型: {summary.get('model_used')}")
            print(f"  Token数: {summary.get('tokens_used')}")
            print(f"  待办数: {result.get('todo_count', 0)}")
            
            if summary.get('todos'):
                print(f"\n  提取的待办事项:")
                for i, todo in enumerate(summary['todos'], 1):
                    print(f"    {i}. {todo}")
    else:
        print(f"❌ 摘要生成失败: {result.get('error')}")
    
    # 测试缓存机制
    print("\n[3] 测试缓存机制")
    start_time = time.time()
    result2 = service.generate_email_summary(email_id)
    elapsed2 = time.time() - start_time
    
    if result2['success'] and result2.get('cached'):
        print(f"✅ 缓存机制正常 (耗时: {elapsed2:.2f}秒，上次: {elapsed:.2f}秒)")
    else:
        print("❌ 缓存机制未生效")
    
    # 获取邮件摘要
    print("\n[4] 查询邮件摘要")
    summary = service.get_email_summary(email_id)
    if summary:
        print(f"✅ 摘要查询成功")
        print(f"  摘要文本: {summary.summary_text[:100]}...")
    else:
        print("❌ 摘要查询失败")
    
    # 获取待办事项
    print("\n[5] 查询待办事项")
    todos = service.get_email_todos(email_id)
    if todos:
        print(f"✅ 待办事项查询成功，共 {len(todos)} 项")
        for todo in todos:
            print(f"  - {todo.content} (优先级: {todo.priority})")
    else:
        print("⚠️  该邮件无待办事项")
    
    return result['success']

if __name__ == "__main__":
    # 测试数据库
    db = test_database()
    
    # 测试邮件仓储
    email_id = test_email_repo(db)
    
    # 测试 AI Service
    success = test_ai_service(db, email_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 全部测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
