# -*- coding: utf-8 -*-
"""
Toast提示组件 - 轻量级的操作反馈提示
支持成功、错误、警告、信息四种类型
"""

from PyQt5.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QFont


class Toast:
    """Toast提示管理器
    
    用法:
        Toast.success(parent, "保存成功")
        Toast.error(parent, "操作失败: 网络错误")
        Toast.warning(parent, "请注意检查输入")
        Toast.info(parent, "正在处理中...")
    """
    
    # 预设样式
    STYLES = {
        'success': {
            'bg': '#4CAF50',
            'icon': '✓',
        },
        'error': {
            'bg': '#F44336',
            'icon': '✗',
        },
        'warning': {
            'bg': '#FF9800',
            'icon': '⚠',
        },
        'info': {
            'bg': '#2196F3',
            'icon': 'ℹ',
        },
    }
    
    # 默认持续时间 (毫秒)
    DEFAULT_DURATION = 3000
    
    @classmethod
    def show(cls, parent: QWidget, message: str, 
             level: str = 'info', duration: int = None,
             position: str = 'bottom'):
        """显示Toast提示
        
        Args:
            parent: 父窗口
            message: 提示消息
            level: 级别 ('success', 'error', 'warning', 'info')
            duration: 显示时长 (毫秒)
            position: 位置 ('top', 'bottom', 'center')
            
        Returns:
            QLabel: Toast标签对象
        """
        if duration is None:
            duration = cls.DEFAULT_DURATION
            
        style = cls.STYLES.get(level, cls.STYLES['info'])
        
        # 创建标签
        toast = QLabel(f"{style['icon']}  {message}", parent)
        toast.setObjectName("toast")
        
        # 设置样式
        toast.setStyleSheet(f"""
            QLabel#toast {{
                background-color: {style['bg']};
                color: white;
                padding: 14px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
        """)
        
        toast.adjustSize()
        
        # 计算位置
        x = (parent.width() - toast.width()) // 2
        
        if position == 'top':
            y = 30
        elif position == 'center':
            y = (parent.height() - toast.height()) // 2
        else:  # bottom
            y = parent.height() - toast.height() - 30
            
        toast.move(x, y)
        
        # 设置透明度效果
        opacity_effect = QGraphicsOpacityEffect(toast)
        opacity_effect.setOpacity(0.0)
        toast.setGraphicsEffect(opacity_effect)
        
        # 显示
        toast.show()
        
        # 淡入动画
        fade_in = QPropertyAnimation(opacity_effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        fade_in.start()
        
        # 定时消失
        QTimer.singleShot(duration, lambda: cls._fade_out(toast, opacity_effect))
        
        # 保存动画引用，防止被回收
        toast._fade_in_animation = fade_in
        
        return toast
        
    @classmethod
    def _fade_out(cls, toast: QLabel, opacity_effect: QGraphicsOpacityEffect):
        """淡出动画"""
        fade_out = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(toast.deleteLater)
        fade_out.start()
        
        # 保存动画引用
        toast._fade_out_animation = fade_out
        
    @classmethod
    def success(cls, parent: QWidget, message: str, duration: int = None):
        """显示成功提示"""
        return cls.show(parent, message, 'success', duration)
        
    @classmethod
    def error(cls, parent: QWidget, message: str, duration: int = None):
        """显示错误提示"""
        return cls.show(parent, message, 'error', duration)
        
    @classmethod
    def warning(cls, parent: QWidget, message: str, duration: int = None):
        """显示警告提示"""
        return cls.show(parent, message, 'warning', duration)
        
    @classmethod
    def info(cls, parent: QWidget, message: str, duration: int = None):
        """显示信息提示"""
        return cls.show(parent, message, 'info', duration)


class ToastWidget(QWidget):
    """Toast容器组件 - 用于管理多个Toast"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._toasts = []
        self._spacing = 10
        
    def show_toast(self, message: str, level: str = 'info', duration: int = 3000):
        """显示Toast"""
        toast = Toast.show(self.parent(), message, level, duration)
        self._toasts.append(toast)
        
        # 清理已删除的toast
        self._toasts = [t for t in self._toasts if t.isVisible()]
        
        return toast
        
    def clear_all(self):
        """清除所有Toast"""
        for toast in self._toasts:
            if toast.isVisible():
                toast.deleteLater()
        self._toasts.clear()
