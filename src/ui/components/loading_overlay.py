# -*- coding: utf-8 -*-
"""
加载遮罩组件 - 提供操作进度反馈
显示半透明遮罩层，带进度条和状态文字
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen


class LoadingOverlay(QWidget):
    """加载遮罩层
    
    用法:
        overlay = LoadingOverlay(parent_widget)
        overlay.show("正在处理...")
        overlay.update_progress(50, "正在分析...")
        overlay.hide()
    """
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._is_visible = False
        
    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 遮罩背景色
        self._bg_color = QColor(0, 0, 0, 140)
        
        # 内容容器
        self.container = QFrame()
        self.container.setObjectName("loadingContainer")
        self.container.setStyleSheet("""
            #loadingContainer {
                background-color: rgba(255, 255, 255, 250);
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        self.container.setMinimumWidth(320)
        self.container.setMaximumWidth(400)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(30, 30, 30, 24)
        
        # 加载动画标签
        self.animation_label = QLabel("⏳")
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setStyleSheet("font-size: 48px; background: transparent;")
        container_layout.addWidget(self.animation_label)
        
        # 状态文字
        self.status_label = QLabel("正在处理...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 15px; 
            font-weight: bold;
            color: #333;
            background: transparent;
        """)
        container_layout.addWidget(self.status_label)
        
        # 详细信息
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("""
            font-size: 12px;
            color: #888;
            background: transparent;
        """)
        self.detail_label.setWordWrap(True)
        container_layout.addWidget(self.detail_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E8E8E8;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        # 按钮区域
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        container_layout.addLayout(self.button_layout)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #666;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.button_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(self.container)
        
        # 动画定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self._animation_frames = ["⏳", "⌛"]
        self._animation_index = 0
        
        # 淡入动画
        self._opacity = 0.0
        self._fade_animation = None
        
    def show(self, status: str = "正在处理...", detail: str = "", 
             cancellable: bool = True, show_progress: bool = True):
        """显示遮罩
        
        Args:
            status: 主状态文字
            detail: 详细说明文字
            cancellable: 是否显示取消按钮
            show_progress: 是否显示进度条
        """
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        self.detail_label.setVisible(bool(detail))
        self.cancel_btn.setVisible(cancellable)
        self.progress_bar.setVisible(show_progress)
        
        # 调整大小以适应父窗口
        if self.parent():
            self.setGeometry(self.parent().rect())
        
        # 开始动画
        self.animation_timer.start(500)
        self._is_visible = True
        
        # 显示
        super().show()
        
    def hide(self):
        """隐藏遮罩"""
        self.animation_timer.stop()
        self._is_visible = False
        self._animation_index = 0
        self.progress_bar.setValue(0)
        super().hide()
        
    def update_progress(self, value: int, status: str = None, detail: str = None):
        """更新进度
        
        Args:
            value: 进度值 (0-100)
            status: 新的状态文字 (可选)
            detail: 新的详细说明 (可选)
        """
        self.progress_bar.setValue(min(100, max(0, value)))
        if status:
            self.status_label.setText(status)
        if detail is not None:
            self.detail_label.setText(detail)
            self.detail_label.setVisible(bool(detail))
            
    def set_indeterminate(self, enabled: bool = True):
        """设置无限进度模式
        
        Args:
            enabled: 是否启用无限进度模式
        """
        if enabled:
            self.progress_bar.setRange(0, 0)  # 无限进度
        else:
            self.progress_bar.setRange(0, 100)
            
    def _update_animation(self):
        """更新加载动画"""
        if not self._is_visible:
            return
        self._animation_index = (self._animation_index + 1) % len(self._animation_frames)
        self.animation_label.setText(self._animation_frames[self._animation_index])
        
    def _on_cancel(self):
        """取消操作"""
        self.cancelled.emit()
        self.hide()
        
    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明遮罩
        painter.fillRect(self.rect(), self._bg_color)
        
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 确保在父窗口之上
        if self.parent():
            self.setGeometry(self.parent().rect())
            
    def isVisible(self) -> bool:
        """是否可见"""
        return self._is_visible


class AsyncOperation:
    """异步操作辅助类
    
    用于简化异步操作的进度反馈
    """
    
    def __init__(self, overlay: LoadingOverlay, 
                 start_message: str = "开始处理...",
                 success_message: str = "处理完成",
                 error_message: str = "处理失败"):
        self.overlay = overlay
        self.start_message = start_message
        self.success_message = success_message
        self.error_message = error_message
        self._steps = []
        self._current_step = 0
        
    def add_step(self, message: str, weight: int = 1):
        """添加步骤
        
        Args:
            message: 步骤描述
            weight: 权重 (用于计算进度比例)
        """
        self._steps.append((message, weight))
        
    def start(self):
        """开始操作"""
        self._current_step = 0
        self.overlay.show(self.start_message, show_progress=bool(self._steps))
        self._update_progress()
        
    def next_step(self):
        """进入下一步"""
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._update_progress()
            
    def complete(self):
        """完成操作"""
        self.overlay.update_progress(100, self.success_message)
        QTimer.singleShot(800, self.overlay.hide)
        
    def fail(self, error: str = None):
        """失败"""
        message = f"{self.error_message}: {error}" if error else self.error_message
        self.overlay.update_progress(0, message)
        QTimer.singleShot(2000, self.overlay.hide)
        
    def _update_progress(self):
        """更新进度"""
        if not self._steps:
            return
            
        total_weight = sum(w for _, w in self._steps)
        completed_weight = sum(w for _, w in self._steps[:self._current_step])
        current_weight = self._steps[self._current_step][1]
        
        # 计算当前进度 (完成部分 + 当前进度的一半)
        progress = int((completed_weight + current_weight / 2) / total_weight * 100)
        
        self.overlay.update_progress(progress, self._steps[self._current_step][0])
