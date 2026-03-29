#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 PyQt5 UI 启动
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pyqt5_import():
    print("=" * 60)
    print("测试 PyQt5 导入")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        print("✅ PyQt5 导入成功")
        return True
    except ImportError as e:
        print(f"❌ PyQt5 导入失败: {e}")
        return False

def test_main_window_import():
    print("\n" + "=" * 60)
    print("测试主窗口模块导入")
    print("=" * 60)
    
    try:
        from src.ui.main_window import MainWindow
        print("✅ MainWindow 导入成功")
        return True
    except ImportError as e:
        print(f"❌ MainWindow 导入失败: {e}")
        return False

def test_app_startup():
    print("\n" + "=" * 60)
    print("测试应用启动")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        from src.ui.main_window import MainWindow
        from src.data.database import Database
        
        # 创建应用
        print("\n[1] 创建 QApplication")
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(sys.argv)
        print("✅ QApplication 创建成功")
        
        # 创建内存数据库
        print("\n[2] 创建内存数据库")
        db = Database(":memory:")
        print("✅ 数据库创建成功")
        
        # 创建主窗口
        print("\n[3] 创建主窗口")
        window = MainWindow(db)
        print("✅ 主窗口创建成功")
        
        # 检查窗口组件
        print("\n[4] 检查窗口组件")
        print(f"  窗口标题: {window.windowTitle()}")
        print(f"  窗口大小: {window.width()}x{window.height()}")
        print(f"  组件数量: {len(window.children())}")
        
        # 不显示窗口，只创建
        print("\n✅ UI 启动测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ UI 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = True
    
    # 测试 PyQt5 导入
    if not test_pyqt5_import():
        success = False
    
    # 测试主窗口导入
    if not test_main_window_import():
        success = False
    
    # 测试应用启动
    if success:
        success = test_app_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ UI 测试全部通过")
    else:
        print("❌ UI 测试失败")
    print("=" * 60)
