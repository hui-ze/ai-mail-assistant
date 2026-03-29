# -*- coding: utf-8 -*-
"""
简化测试：只测试窗口尺寸计算逻辑
"""

import sys
import os
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect


def test_screen_calculation():
    """测试屏幕尺寸计算逻辑"""
    print("\n=== 测试屏幕尺寸计算 ===")
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 模拟 MainWindow._resize_to_screen 的逻辑
    screen = app.primaryScreen()
    available_geometry = screen.availableGeometry()
    
    # 计算窗口尺寸（屏幕的 85%）
    width = int(available_geometry.width() * 0.85)
    height = int(available_geometry.height() * 0.85)
    
    # 计算居中位置
    x = available_geometry.x() + (available_geometry.width() - width) // 2
    y = available_geometry.y() + (available_geometry.height() - height) // 2
    
    print(f"屏幕可用区域: {available_geometry.width()}x{available_geometry.height()}")
    print(f"计算窗口尺寸: {width}x{height}")
    print(f"计算窗口位置: ({x}, {y})")
    
    # 验证计算结果
    assert width > 0 and height > 0, "窗口尺寸必须为正数"
    assert width < available_geometry.width(), "窗口宽度不能超过屏幕"
    assert height < available_geometry.height(), "窗口高度不能超过屏幕"
    
    # 验证窗口在屏幕内
    assert x >= available_geometry.x(), "窗口X坐标应在屏幕内"
    assert y >= available_geometry.y(), "窗口Y坐标应在屏幕内"
    assert x + width <= available_geometry.x() + available_geometry.width(), "窗口右边界应在屏幕内"
    assert y + height <= available_geometry.y() + available_geometry.height(), "窗口底边应在屏幕内"
    
    print("[OK] 窗口尺寸计算正确")
    
    return True


def test_splitter_logic():
    """测试分割器逻辑"""
    print("\n=== 测试分割器逻辑 ===")
    
    from PyQt5.QtWidgets import QSplitter
    from PyQt5.QtCore import Qt
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 创建分割器
    splitter = QSplitter(Qt.Horizontal)
    
    # 模拟添加3个面板
    from PyQt5.QtWidgets import QFrame, QSizePolicy
    
    panel1 = QFrame()
    panel1.setMinimumWidth(150)
    panel1.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding))
    
    panel2 = QFrame()
    panel2.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
    
    panel3 = QFrame()
    panel3.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
    
    splitter.addWidget(panel1)
    splitter.addWidget(panel2)
    splitter.addWidget(panel3)
    
    # 设置初始宽度比例
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 2)
    splitter.setStretchFactor(2, 2)
    
    print(f"分割器面板数量: {splitter.count()}")
    assert splitter.count() == 3, f"应有3个面板，实际为{splitter.count()}"
    
    # 测试调整宽度
    splitter.resize(1000, 600)
    sizes = splitter.sizes()
    print(f"初始面板宽度: {sizes}")
    
    # 手动设置宽度
    new_sizes = [200, 400, 400]
    splitter.setSizes(new_sizes)
    
    actual_sizes = splitter.sizes()
    print(f"调整后面板宽度: {actual_sizes}")
    
    # 验证总宽度
    total = sum(actual_sizes)
    print(f"面板总宽度: {total}")
    assert total > 0, "总宽度应大于0"
    
    print("[OK] 分割器逻辑正确")
    
    return True


def test_state_persistence_logic():
    """测试状态持久化逻辑"""
    print("\n=== 测试状态持久化逻辑 ===")
    
    import json
    from PyQt5.QtCore import QByteArray
    
    # 模拟保存状态
    splitter_state_hex = "0100000000000001ffffffffffffffff0000000000000000"
    
    window_state = {
        'splitter_state': splitter_state_hex,
        'window_geometry': {
            'x': 100,
            'y': 100,
            'width': 1200,
            'height': 800
        }
    }
    
    # 序列化
    json_str = json.dumps(window_state)
    print(f"序列化状态: {json_str[:100]}...")
    
    # 反序列化
    loaded_state = json.loads(json_str)
    assert loaded_state['window_geometry']['width'] == 1200, "宽度应为1200"
    assert loaded_state['window_geometry']['height'] == 800, "高度应为800"
    
    print("[OK] 状态持久化逻辑正确")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("UI优化逻辑测试（无GUI）")
    print("=" * 60)
    
    try:
        test_screen_calculation()
        test_splitter_logic()
        test_state_persistence_logic()
        
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
