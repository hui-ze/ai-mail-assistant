# -*- coding: utf-8 -*-
"""
邮件智能助手 - 主程序入口
"""

import sys
import logging
import json
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.ui.main_window import MainWindow
from src.ui.styles import init_theme_manager
from src.utils.logger import setup_logger, get_log_dir
from src.utils.icon_manager import init_icon_manager
from src.data.database import Database


def get_user_theme(db: Database) -> str:
    """从数据库获取用户主题偏好
    
    Returns:
        'light', 'dark', 或 'system'
    """
    try:
        result = db.query_one("SELECT value FROM settings WHERE id = 3")
        if result and result[0]:
            ui_settings = json.loads(result[0])
            theme_index = ui_settings.get('theme', 0)
            theme_map = {0: 'light', 1: 'dark', 2: 'system'}
            return theme_map.get(theme_index, 'light')
    except Exception:
        pass
    return 'light'


def main():
    """主函数"""
    # 设置日志
    logger = setup_logger("mail-assistant", get_log_dir())
    logger.info("=" * 50)
    logger.info("邮件智能助手启动")
    logger.info("=" * 50)

    # 设置Qt属性
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("邮件智能助手")
    app.setApplicationVersion("1.0.0")

    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # 设置基础样式
    app.setStyle("Fusion")

    # 初始化图标管理器并设置应用图标
    icons_dir = Path(__file__).parent / "assets" / "icons"
    icon_manager = init_icon_manager(str(icons_dir))
    icon_manager.setup_app_icon(app)
    logger.info("应用图标已设置")

    # 初始化数据库
    db_path = Path.home() / ".mail-assistant" / "data.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"数据库路径: {db_path}")

    try:
        db = Database(str(db_path))
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return 1

    # 初始化主题管理器并应用用户主题偏好
    theme_manager = init_theme_manager(app)
    user_theme = get_user_theme(db)
    theme_manager.apply_theme(user_theme)
    logger.info(f"已应用主题: {user_theme}")

    # 创建主窗口
    window = MainWindow(db)
    window.show()

    logger.info("主窗口已显示")

    # 运行应用
    exit_code = app.exec_()

    logger.info(f"应用退出，代码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
