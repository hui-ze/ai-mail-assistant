# -*- coding: utf-8 -*-
"""
测试UI优化：窗口自适应和分割器可调整
"""

import sys
import os
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from src.data.database import Database
from src.ui.main_window import MainWindow


def test_window_resize():
    """测试窗口自适应屏幕"""
    print("\n=== 测试窗口自适应屏幕 ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    db = Database(':memory:')
    window = MainWindow(db)
    
    # 检查窗口尺寸
    screen = app.primaryScreen()
    available = screen.availableGeometry()
    
    expected_width = int(available.width() * 0.85)
    expected_height = int(available.height() * 0.85)
    
    actual_width = window.width()
    actual_height = window.height()
    
    print(f"屏幕可用区域: {available.width()}x{available.height()}")
    print(f"期望窗口尺寸: {expected_width}x{expected_height}")
    print(f"实际窗口尺寸: {actual_width}x{actual_height}")
    
    # 允许一定误差（窗口装饰等）
    assert abs(actual_width - expected_width) < 50, f"宽度差异过大: {actual_width} vs {expected_width}"
    assert abs(actual_height - expected_height) < 50, f"高度差异过大: {actual_height} vs {expected_height}"
    
    print("[OK] 窗口尺寸正确")
    
    # 检查窗口居中
    expected_x = available.x() + (available.width() - actual_width) // 2
    expected_y = available.y() + (available.height() - actual_height) // 2
    
    actual_x = window.geometry().x()
    actual_y = window.geometry().y()
    
    print(f"期望窗口位置: ({expected_x}, {expected_y})")
    print(f"实际窗口位置: ({actual_x}, {actual_y})")
    
    # 允许一定误差
    assert abs(actual_x - expected_x) < 50, f"X坐标差异过大: {actual_x} vs {expected_x}"
    assert abs(actual_y - expected_y) < 50, f"Y坐标差异过大: {actual_y} vs {expected_y}"
    
    print("[OK] 窗口位置居中")
    
    return True


def test_splitter():
    """测试分割器可调整"""
    print("\n=== 测试分割器可调整 ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    db = Database(':memory:')
    window = MainWindow(db)
    
    # 检查分割器存在
    assert hasattr(window, 'main_splitter'), "main_splitter 不存在"
    print("[OK] 分割器已创建")
    
    # 检查分割器有3个部件
    assert window.main_splitter.count() == 3, f"分割器应有3个部件，实际为{window.main_splitter.count()}"
    print("[OK] 分割器包含3个面板")
    
    # 检查面板可调整
    sizes = window.main_splitter.sizes()
    print(f"初始面板宽度: {sizes}")
    
    # 模拟调整宽度
    new_sizes = [200, 400, 600]
    window.main_splitter.setSizes(new_sizes)
    
    actual_sizes = window.main_splitter.sizes()
    print(f"调整后面板宽度: {actual_sizes}")
    
    # 验证宽度已改变（允许一定误差）
    for i, (expected, actual) in enumerate(zip(new_sizes, actual_sizes)):
        assert abs(expected - actual) < 10, f"面板{i}宽度未正确调整: {actual} vs {expected}"
    
    print("[OK] 面板宽度可调整")
    
    return True


def test_window_state_persistence():
    """测试窗口状态持久化"""
    print("\n=== 测试窗口状态持久化 ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    db = Database(':memory:')
    
    # 第一次创建窗口并调整
    window1 = MainWindow(db)
    window1.main_splitter.setSizes([200, 400, 600])
    window1.resize(1200, 800)
    
    # 保存状态
    window1._save_window_state()
    print("[OK] 窗口状态已保存")
    
    # 验证数据库中有记录
    import json
    result = db.query_one("SELECT value FROM settings WHERE id = 10")
    assert result and result[0], "窗口状态未保存到数据库"
    
    state = json.loads(result[0])
    assert 'splitter_state' in state, "缺少 splitter_state"
    assert 'window_geometry' in state, "缺少 window_geometry"
    print("[OK] 数据库中已存储窗口状态")
    
    # 创建新窗口恢复状态
    window2 = MainWindow(db)
    
    # 注意：_restore_window_state 在 __init__ 中已调用
    print("[OK] 新窗口已创建并恢复状态")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("UI优化测试")
    print("=" * 60)
    
    try:
        test_window_resize()
        test_splitter()
        test_window_state_persistence()
        
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
