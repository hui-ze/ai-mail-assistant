# -*- coding: utf-8 -*-
"""
部门卡片组件 - 用于卡片视图显示，支持高度拖拽调整
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizeGrip
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QCursor


class DepartmentCard(QWidget):
    """部门卡片组件 - 支持拖拽调整高度"""
    
    # 信号
    edit_clicked = pyqtSignal(int)      # 编辑信号（部门ID）
    sync_clicked = pyqtSignal(int)      # 同步信号（部门ID）
    delete_clicked = pyqtSignal(int)    # 删除信号（部门ID）
    card_clicked = pyqtSignal(int)      # 点击信号（部门ID）
    height_changed = pyqtSignal(int)    # 高度改变信号
    
    # 类变量：存储所有卡片共享的高度
    _shared_height = 150
    
    def __init__(self, dept, member_count: int = 0, parent=None):
        """
        初始化部门卡片
        
        Args:
            dept: 部门对象（有 id, name, share_path 属性）
            member_count: 成员数量
            parent: 父组件
        """
        super().__init__(parent)
        self.dept = dept
        self.member_count = member_count
        self.dept_id = dept.id
        self._dragging = False
        self._drag_start_pos = None
        self._start_height = None
        
        self._init_ui()
        self._apply_styles()
        
        # 应用共享高度
        self.setFixedHeight(DepartmentCard._shared_height)
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 8)
        main_layout.setSpacing(8)
        
        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # 左侧：图标 + 信息
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        
        # 部门图标
        self.icon_label = QLabel("🏢")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 24))
        self.icon_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.icon_label)
        
        # 部门名称
        self.name_label = QLabel(self.dept.name)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1A1A1A;")
        self.name_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.name_label)
        
        # 成员数量
        self.count_label = QLabel(f"👥 {self.member_count} 人")
        self.count_label.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        self.count_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.count_label)
        
        content_layout.addLayout(left_layout)
        content_layout.addStretch()
        
        # 右侧：操作按钮
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        
        # 编辑按钮
        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setFlat(True)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.dept_id))
        edit_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 6px 12px;
                color: #667eea;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #EEF2FF;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(edit_btn)
        
        # 同步按钮
        sync_btn = QPushButton("🔄 同步")
        sync_btn.setFlat(True)
        sync_btn.setCursor(Qt.PointingHandCursor)
        sync_btn.clicked.connect(lambda: self.sync_clicked.emit(self.dept_id))
        sync_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 6px 12px;
                color: #10B981;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #D1FAE5;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(sync_btn)
        
        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)
        
        # 底部拖拽调整区域
        resize_handle = QWidget()
        resize_handle.setFixedHeight(6)
        resize_handle.setCursor(QCursor(Qt.SizeVerCursor))
        resize_handle.setStyleSheet("""
            QWidget {
                background: transparent;
                border-radius: 3px;
            }
            QWidget:hover {
                background: #667eea;
            }
        """)
        resize_handle.installEventFilter(self)
        self._resize_handle = resize_handle
        main_layout.addWidget(resize_handle)
        
        # 设置尺寸范围
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self.setMinimumHeight(120)
        self.setMaximumHeight(300)
        
        # 设置鼠标悬停效果
        self.setCursor(Qt.PointingHandCursor)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理拖拽调整高度"""
        if obj == self._resize_handle:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._dragging = True
                    self._drag_start_pos = event.globalPos()
                    self._start_height = self.height()
                    self._resize_handle.setStyleSheet("""
                        QWidget {
                            background: #667eea;
                            border-radius: 3px;
                        }
                    """)
                    return True
            elif event.type() == event.MouseMove:
                if self._dragging:
                    delta = event.globalPos().y() - self._drag_start_pos.y()
                    new_height = max(120, min(300, self._start_height + delta))
                    self.setFixedHeight(new_height)
                    DepartmentCard._shared_height = new_height  # 更新共享高度
                    self.height_changed.emit(new_height)
                    return True
            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self._dragging:
                    self._dragging = False
                    self._resize_handle.setStyleSheet("""
                        QWidget {
                            background: transparent;
                            border-radius: 3px;
                        }
                        QWidget:hover {
                            background: #667eea;
                        }
                    """)
                    return True
        return super().eventFilter(obj, event)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            DepartmentCard {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            DepartmentCard:hover {
                border-color: #667eea;
                background: #FAFAFA;
            }
        """)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.dept_id)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setStyleSheet("""
            DepartmentCard {
                background: white;
                border: 2px solid #667eea;
                border-radius: 8px;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._apply_styles()
        super().leaveEvent(event)
    
    @classmethod
    def get_shared_height(cls):
        """获取共享高度"""
        return cls._shared_height
    
    @classmethod
    def set_shared_height(cls, height):
        """设置共享高度"""
        cls._shared_height = height
