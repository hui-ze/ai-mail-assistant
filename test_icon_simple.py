# -*- coding: utf-8 -*-
"""测试图标集成"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from src.utils.icon_manager import init_icon_manager, get_icon_manager


def test_icon():
    """测试图标"""
    # 初始化图标管理器
    icons_dir = project_root / "assets" / "icons"
    icon_manager = init_icon_manager(str(icons_dir))
    
    # 检查图标文件
    print("检查图标文件:")
    for name, path in icon_manager.icon_paths.items():
        exists = "YES" if path.exists() else "NO"
        print(f"  {name}: {exists} - {path}")
    
    # 测试加载图标
    app_icon = icon_manager.get_icon('app')
    if app_icon.isNull():
        print("\nERROR: 应用图标加载失败")
    else:
        print(f"\nOK: 应用图标加载成功")
        sizes = app_icon.availableSizes()
        print(f"  可用尺寸: {len(sizes)} 个")
    
    # 创建测试窗口
    app = QApplication(sys.argv)
    
    # 设置应用图标
    icon_manager.setup_app_icon(app)
    print("\n应用图标已设置")
    
    # 创建简单窗口
    window = QWidget()
    window.setWindowTitle("图标测试 - Foxmail邮件智能助手")
    icon_manager.setup_window_icon(window)
    
    layout = QVBoxLayout(window)
    
    info = QLabel(
        "图标集成测试成功！\n\n"
        "请查看:\n"
        "1. 窗口标题栏图标\n"
        "2. 任务栏图标\n"
        "3. Alt+Tab切换时的图标"
    )
    info.setAlignment(Qt.AlignCenter)
    info.setStyleSheet("font-size: 16px; padding: 30px;")
    layout.addWidget(info)
    
    window.resize(500, 350)
    window.show()
    
    print("\n测试窗口已显示")
    print("请检查窗口和任务栏的图标是否正确")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_icon()
