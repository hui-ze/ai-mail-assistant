# -*- coding: utf-8 -*-
"""
测试图标集成
"""

import sys
import io
from pathlib import Path

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

from src.utils.icon_manager import init_icon_manager, get_icon_manager


def test_icon_manager():
    """测试图标管理器"""
    print("=" * 50)
    print("测试图标管理器")
    print("=" * 50)
    
    # 初始化图标管理器
    icons_dir = project_root / "assets" / "icons"
    icon_manager = init_icon_manager(str(icons_dir))
    print(f"✓ 图标管理器初始化成功")
    print(f"  图标目录: {icons_dir}")
    print(f"  目录存在: {icons_dir.exists()}")
    
    # 检查图标文件
    print("\n检查图标文件:")
    for name, path in icon_manager.icon_paths.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {exists} {name}: {path}")
    
    # 测试加载图标
    print("\n测试加载图标:")
    app_icon = icon_manager.get_icon('app')
    if app_icon.isNull():
        print("  ✗ 应用图标加载失败")
    else:
        print(f"  ✓ 应用图标加载成功")
        print(f"    可用尺寸: {app_icon.availableSizes()}")
    
    # 测试不同尺寸
    sizes = [16, 32, 64, 128, 256]
    print("\n测试不同尺寸图标:")
    for size in sizes:
        icon = icon_manager.get_icon('app', size)
        status = "✓" if not icon.isNull() else "✗"
        print(f"  {status} {size}x{size}")
    
    # 创建测试窗口
    app = QApplication(sys.argv)
    
    # 设置应用图标
    icon_manager.setup_app_icon(app)
    print("\n✓ 应用图标已设置")
    
    # 创建简单窗口显示图标
    window = QWidget()
    window.setWindowTitle("图标测试")
    icon_manager.setup_window_icon(window)
    
    layout = QVBoxLayout(window)
    
    # 显示图标信息
    info_label = QLabel(
        "图标集成测试成功！\n\n"
        "✓ 图标管理器已初始化\n"
        "✓ 应用图标已设置\n"
        "✓ 窗口图标已设置\n\n"
        "请查看窗口标题栏和任务栏\n"
        "确认图标是否正确显示"
    )
    info_label.setAlignment(Qt.AlignCenter)
    info_label.setStyleSheet("font-size: 14px; padding: 20px;")
    layout.addWidget(info_label)
    
    window.resize(400, 300)
    window.show()
    
    print("\n" + "=" * 50)
    print("测试窗口已显示，请检查图标")
    print("=" * 50)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_icon_manager()
