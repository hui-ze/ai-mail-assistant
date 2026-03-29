# -*- coding: utf-8 -*-
"""
主题管理系统 - 支持浅色/深色/跟随系统
提供完整的QSS样式表和颜色变量
"""

from PyQt5.QtCore import Qt
from typing import Dict, Optional
import logging


class ThemeColors:
    """主题颜色定义"""
    
    # 浅色主题
    LIGHT = {
        # 背景色
        'bg_primary': '#FFFFFF',
        'bg_secondary': '#F8F9FA',
        'bg_tertiary': '#F0F0F0',
        'bg_hover': '#E8E8E8',
        
        # 文字颜色
        'text_primary': '#1A1A1A',
        'text_secondary': '#666666',
        'text_tertiary': '#999999',
        'text_disabled': '#BBBBBB',
        
        # 边框颜色
        'border_color': '#E0E0E0',
        'border_focus': '#667eea',
        
        # 强调色（紫色渐变）
        'accent_primary': '#667eea',
        'accent_secondary': '#764ba2',
        'accent_light': '#8B9FEF',
        
        # 状态颜色
        'success': '#4CAF50',
        'success_bg': '#E8F5E9',
        'warning': '#FF9800',
        'warning_bg': '#FFF3E0',
        'error': '#F44336',
        'error_bg': '#FFEBEE',
        'info': '#2196F3',
        'info_bg': '#E3F2FD',
        
        # 卡片
        'card_bg': '#FFFFFF',
        'card_border': '#E0E0E0',
        'card_shadow': 'rgba(0,0,0,0.08)',
        
        # 滚动条
        'scrollbar_bg': '#F0F0F0',
        'scrollbar_handle': '#C0C0C0',
        'scrollbar_handle_hover': '#A0A0A0',
    }
    
    # 深色主题
    DARK = {
        # 背景色
        'bg_primary': '#1E1E1E',
        'bg_secondary': '#252526',
        'bg_tertiary': '#2D2D30',
        'bg_hover': '#3E3E42',
        
        # 文字颜色
        'text_primary': '#E0E0E0',
        'text_secondary': '#B0B0B0',
        'text_tertiary': '#808080',
        'text_disabled': '#505050',
        
        # 边框颜色
        'border_color': '#3C3C3C',
        'border_focus': '#7C8AEF',
        
        # 强调色（深色模式下略微调亮）
        'accent_primary': '#7C8AEF',
        'accent_secondary': '#9B6FC6',
        'accent_light': '#A0B0F5',
        
        # 状态颜色
        'success': '#66BB6A',
        'success_bg': '#1B3D1F',
        'warning': '#FFA726',
        'warning_bg': '#3D2F1B',
        'error': '#EF5350',
        'error_bg': '#3D1B1B',
        'info': '#42A5F5',
        'info_bg': '#1B2D3D',
        
        # 卡片
        'card_bg': '#2D2D30',
        'card_border': '#3C3C3C',
        'card_shadow': 'rgba(0,0,0,0.3)',
        
        # 滚动条
        'scrollbar_bg': '#2D2D30',
        'scrollbar_handle': '#505050',
        'scrollbar_handle_hover': '#606060',
    }
    
    @classmethod
    def get_colors(cls, theme: str) -> Dict[str, str]:
        """获取指定主题的颜色配置"""
        if theme == 'dark':
            return cls.DARK.copy()
        return cls.LIGHT.copy()
    
    @classmethod
    def get_color(cls, theme: str, name: str) -> str:
        """获取指定主题的某个颜色值"""
        colors = cls.get_colors(theme)
        return colors.get(name, '#000000')


class ThemeManager:
    """主题管理器"""
    
    def __init__(self, app):
        self.app = app
        self.current_theme = 'light'
        self.colors = ThemeColors.LIGHT.copy()
        self.logger = logging.getLogger(__name__)
        
    def apply_theme(self, theme: str):
        """应用主题
        
        Args:
            theme: 'light', 'dark', 或 'system'
        """
        # 如果是系统主题，检测系统设置
        if theme == 'system':
            theme = self._detect_system_theme()
            
        self.current_theme = theme
        self.colors = ThemeColors.get_colors(theme)
        
        # 生成并应用样式表
        qss = self._generate_stylesheet()
        self.app.setStyleSheet(qss)
        
        self.logger.info(f"已应用主题: {theme}")
        
    def _detect_system_theme(self) -> str:
        """检测系统主题（Windows）"""
        try:
            import ctypes
            value = ctypes.c_int()
            # 读取Windows注册表判断系统主题
            result = ctypes.windll.advapi32.RegGetValueW(
                -2147483647,  # HKEY_CURRENT_USER
                "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                "AppsUseLightTheme",
                2, None, ctypes.byref(value), None
            )
            # result == 0 表示成功，value.value == 1 表示浅色主题
            if result == 0:
                return 'light' if value.value == 1 else 'dark'
        except Exception as e:
            self.logger.debug(f"检测系统主题失败: {e}")
            
        # 默认返回浅色主题
        return 'light'
    
    def _generate_stylesheet(self) -> str:
        """生成完整的QSS样式表"""
        c = self.colors
        
        return f'''
        /* ========== 全局样式 ========== */
        QMainWindow {{
            background-color: {c['bg_primary']};
        }}
        
        QWidget {{
            background-color: {c['bg_primary']};
            color: {c['text_primary']};
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            font-size: 13px;
        }}
        
        /* ========== 输入框 ========== */
        QLineEdit {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 8px 12px;
            color: {c['text_primary']};
            selection-background-color: {c['accent_primary']};
            selection-color: white;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {c['accent_primary']};
            padding: 7px 11px;
        }}
        
        QLineEdit:disabled {{
            background-color: {c['bg_tertiary']};
            color: {c['text_disabled']};
            border-color: {c['border_color']};
        }}
        
        QLineEdit[echoMode="2"] {{
            lineedit-password-character: 9679;
        }}
        
        QTextEdit {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 8px;
            color: {c['text_primary']};
            selection-background-color: {c['accent_primary']};
            selection-color: white;
        }}
        
        QTextEdit:focus {{
            border: 2px solid {c['accent_primary']};
        }}
        
        QPlainTextEdit {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 8px;
            color: {c['text_primary']};
        }}
        
        QPlainTextEdit:focus {{
            border: 2px solid {c['accent_primary']};
        }}
        
        /* ========== 按钮 ========== */
        QPushButton {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 8px 16px;
            color: {c['text_primary']};
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {c['bg_hover']};
            border-color: {c['accent_primary']};
        }}
        
        QPushButton:pressed {{
            background-color: {c['accent_primary']};
            color: white;
        }}
        
        QPushButton:disabled {{
            background-color: {c['bg_tertiary']};
            color: {c['text_disabled']};
            border-color: {c['border_color']};
        }}
        
        QPushButton#primaryBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
            color: white;
            border: none;
            font-weight: bold;
        }}
        
        QPushButton#primaryBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent_light']}, stop:1 {c['accent_secondary']});
        }}
        
        QPushButton#primaryBtn:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent_secondary']}, stop:1 {c['accent_primary']});
        }}
        
        QPushButton#primaryBtn:disabled {{
            background: {c['bg_tertiary']};
            color: {c['text_disabled']};
        }}
        
        QPushButton#secondaryBtn {{
            background-color: {c['bg_secondary']};
            color: {c['text_secondary']};
            border: 1px solid {c['border_color']};
        }}
        
        QPushButton#secondaryBtn:hover {{
            background-color: {c['bg_hover']};
        }}
        
        /* ========== 列表 ========== */
        QListWidget {{
            background-color: {c['bg_primary']};
            border: 1px solid {c['border_color']};
            border-radius: 8px;
            outline: none;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 10px 8px;
            border-bottom: 1px solid {c['border_color']};
            border-radius: 4px;
            margin: 2px 0;
        }}
        
        QListWidget::item:hover {{
            background-color: {c['bg_hover']};
        }}
        
        QListWidget::item:selected {{
            background-color: {c['accent_primary']};
            color: white;
        }}
        
        QListWidget::item:selected:!active {{
            background-color: {c['accent_light']};
        }}
        
        QListWidget::item:last {{
            border-bottom: none;
        }}
        
        /* ========== 滚动条 ========== */
        QScrollBar:vertical {{
            background-color: {c['scrollbar_bg']};
            width: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['scrollbar_handle']};
            min-height: 30px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['scrollbar_handle_hover']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['scrollbar_bg']};
            height: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['scrollbar_handle']};
            min-width: 30px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['scrollbar_handle_hover']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* ========== 分组框 ========== */
        QGroupBox {{
            border: 1px solid {c['border_color']};
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            padding-top: 24px;
            background-color: {c['card_bg']};
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            color: {c['text_secondary']};
            subcontrol-origin: margin;
            left: 12px;
            top: 4px;
            background-color: {c['card_bg']};
            padding: 0 6px;
        }}
        
        /* ========== 标签页 ========== */
        QTabWidget::pane {{
            border: 1px solid {c['border_color']};
            border-radius: 8px;
            background-color: {c['bg_primary']};
            border-top-left-radius: 0;
        }}
        
        QTabBar::tab {{
            background-color: {c['bg_secondary']};
            color: {c['text_secondary']};
            padding: 10px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
            border: 1px solid {c['border_color']};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['bg_primary']};
            color: {c['accent_primary']};
            font-weight: bold;
            border-bottom: 2px solid {c['bg_primary']};
            margin-bottom: -1px;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c['bg_hover']};
        }}
        
        QTabBar::tab:!selected {{
            margin-top: 2px;
        }}
        
        /* ========== 下拉框 ========== */
        QComboBox {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 6px 12px;
            padding-right: 30px;
            color: {c['text_primary']};
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {c['accent_primary']};
        }}
        
        QComboBox:focus {{
            border: 2px solid {c['accent_primary']};
            padding: 5px 11px;
            padding-right: 29px;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            subcontrol-position: center right;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {c['text_secondary']};
            margin-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c['bg_primary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            selection-background-color: {c['accent_primary']};
            selection-color: white;
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            min-height: 24px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c['bg_hover']};
        }}
        
        /* ========== 复选框 ========== */
        QCheckBox {{
            spacing: 8px;
            color: {c['text_primary']};
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {c['border_color']};
            background-color: {c['bg_secondary']};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {c['accent_primary']};
        }}
        
        QCheckBox::indicator:focus {{
            border-color: {c['accent_primary']};
            border-width: 2px;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {c['accent_primary']};
            border-color: {c['accent_primary']};
        }}
        
        QCheckBox::indicator:disabled {{
            background-color: {c['bg_tertiary']};
            border-color: {c['border_color']};
        }}
        
        /* ========== 单选框 ========== */
        QRadioButton {{
            spacing: 8px;
            color: {c['text_primary']};
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {c['border_color']};
            background-color: {c['bg_secondary']};
        }}
        
        QRadioButton::indicator:hover {{
            border-color: {c['accent_primary']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {c['bg_secondary']};
            border: 6px solid {c['accent_primary']};
        }}
        
        /* ========== 进度条 ========== */
        QProgressBar {{
            background-color: {c['bg_secondary']};
            border: none;
            border-radius: 4px;
            height: 8px;
            text-align: center;
            color: transparent;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
            border-radius: 4px;
        }}
        
        /* ========== 微调框 ========== */
        QSpinBox, QDoubleSpinBox {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 6px 12px;
            padding-right: 20px;
            color: {c['text_primary']};
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {c['accent_primary']};
            padding: 5px 11px;
            padding-right: 19px;
        }}
        
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background-color: transparent;
            border: none;
            width: 16px;
        }}
        
        QSpinBox::up-arrow, QSpinBox::down-arrow,
        QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {{
            width: 10px;
            height: 10px;
        }}
        
        /* ========== 日期时间选择器 ========== */
        QDateTimeEdit {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 6px 12px;
            color: {c['text_primary']};
        }}
        
        QDateTimeEdit:focus {{
            border: 2px solid {c['accent_primary']};
        }}
        
        QDateTimeEdit::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QCalendarWidget {{
            background-color: {c['bg_primary']};
            border: 1px solid {c['border_color']};
            border-radius: 8px;
        }}
        
        QCalendarWidget QToolButton {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            border-radius: 4px;
            padding: 4px 8px;
        }}
        
        QCalendarWidget QToolButton:hover {{
            background-color: {c['bg_hover']};
        }}
        
        /* ========== 工具栏 ========== */
        QToolBar {{
            background-color: {c['bg_secondary']};
            border-bottom: 1px solid {c['border_color']};
            spacing: 6px;
            padding: 4px 8px;
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px 12px;
            color: {c['text_primary']};
        }}
        
        QToolBar QToolButton:hover {{
            background-color: {c['bg_hover']};
            border-color: {c['border_color']};
        }}
        
        QToolBar QToolButton:pressed {{
            background-color: {c['accent_primary']};
            color: white;
        }}
        
        QToolBar::separator {{
            background-color: {c['border_color']};
            width: 1px;
            margin: 4px 8px;
        }}
        
        /* ========== 状态栏 ========== */
        QStatusBar {{
            background-color: {c['bg_secondary']};
            border-top: 1px solid {c['border_color']};
            color: {c['text_secondary']};
            font-size: 12px;
            padding: 4px 8px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* ========== 分割器 ========== */
        QSplitter::handle {{
            background-color: {c['border_color']};
        }}
        
        QSplitter::handle:hover {{
            background-color: {c['accent_primary']};
        }}
        
        QSplitter::handle:vertical {{
            height: 4px;
        }}
        
        QSplitter::handle:horizontal {{
            width: 4px;
        }}
        
        /* ========== 消息框 ========== */
        QMessageBox {{
            background-color: {c['bg_primary']};
        }}
        
        QMessageBox QLabel {{
            color: {c['text_primary']};
            font-size: 13px;
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
        }}
        
        /* ========== 对话框按钮盒 ========== */
        QDialogButtonBox {{
            button-layout: 2;
        }}
        
        QDialogButtonBox QPushButton {{
            min-width: 80px;
        }}
        
        /* ========== 提示框 ========== */
        QToolTip {{
            background-color: {c['bg_tertiary']};
            color: {c['text_primary']};
            border: 1px solid {c['border_color']};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        
        /* ========== 框架 ========== */
        QFrame {{
            border: none;
        }}
        
        QFrame[frameShape="4"] {{ /* HLine */
            background-color: {c['border_color']};
            max-height: 1px;
        }}
        
        QFrame[frameShape="5"] {{ /* VLine */
            background-color: {c['border_color']};
            max-width: 1px;
        }}
        
        /* ========== 标签 ========== */
        QLabel {{
            background-color: transparent;
            color: {c['text_primary']};
        }}
        
        QLabel#title {{
            font-size: 16px;
            font-weight: bold;
            color: {c['text_primary']};
        }}
        
        QLabel#subtitle {{
            font-size: 12px;
            color: {c['text_secondary']};
        }}
        
        /* ========== 菜单 ========== */
        QMenu {{
            background-color: {c['bg_primary']};
            border: 1px solid {c['border_color']};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {c['accent_primary']};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {c['border_color']};
            margin: 4px 8px;
        }}
        
        QMenuBar {{
            background-color: {c['bg_secondary']};
            border-bottom: 1px solid {c['border_color']};
        }}
        
        QMenuBar::item {{
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {c['bg_hover']};
        }}
        
        /* ========== 表单布局 ========== */
        QFormLayout {{
            spacing: 12px;
        }}
        
        /* ========== 滑块 ========== */
        QSlider::groove:horizontal {{
            background-color: {c['bg_tertiary']};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {c['accent_primary']};
            width: 18px;
            height: 18px;
            border-radius: 9px;
            margin: -6px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {c['accent_light']};
        }}
        
        QSlider::sub-page:horizontal {{
            background-color: {c['accent_primary']};
            border-radius: 3px;
        }}
        '''
    
    def get_color(self, name: str) -> str:
        """获取指定颜色值"""
        return self.colors.get(name, '#000000')
    
    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self.current_theme


# 全局主题管理器实例
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> Optional[ThemeManager]:
    """获取全局主题管理器实例"""
    return _theme_manager


def init_theme_manager(app) -> ThemeManager:
    """初始化全局主题管理器"""
    global _theme_manager
    _theme_manager = ThemeManager(app)
    return _theme_manager
