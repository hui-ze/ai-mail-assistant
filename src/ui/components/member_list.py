# -*- coding: utf-8 -*-
"""
成员列表组件 - 支持调整行高
"""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont


class MemberListWidget(QListWidget):
    """成员列表组件 - 支持拖拽调整行高"""
    
    # 类变量：存储共享的行高
    _shared_item_height = 32  # 默认较小的行高
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_start_y = 0
        self._start_height = 0
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background: #F0F4FF;
            }
            QListWidget::item:selected {
                background: #E0E7FF;
                color: #667eea;
            }
        """)
        
        # 安装事件过滤器
        self.viewport().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理拖拽调整行高"""
        if obj == self.viewport():
            # 检查是否在底部边缘
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    viewport_height = self.viewport().height()
                    y = event.pos().y()
                    # 检查是否在底部 10 像素范围内
                    if viewport_height - y < 10:
                        self._dragging = True
                        self._drag_start_y = event.globalY()
                        self._start_height = MemberListWidget._shared_item_height
                        self.viewport().setCursor(Qt.SizeVerCursor)
                        return True
            
            elif event.type() == event.MouseMove:
                if self._dragging:
                    delta = event.globalY() - self._drag_start_y
                    new_height = max(24, min(60, self._start_height + delta // 3))
                    MemberListWidget._shared_item_height = new_height
                    self._update_all_items_height()
                    return True
                else:
                    # 更新光标
                    viewport_height = self.viewport().height()
                    y = event.pos().y()
                    if viewport_height - y < 10:
                        self.viewport().setCursor(Qt.SizeVerCursor)
                    else:
                        self.viewport().setCursor(Qt.ArrowCursor)
            
            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self._dragging:
                    self._dragging = False
                    self.viewport().setCursor(Qt.ArrowCursor)
                    return True
        
        return super().eventFilter(obj, event)
    
    def _update_all_items_height(self):
        """更新所有项的高度"""
        height = MemberListWidget._shared_item_height
        for i in range(self.count()):
            item = self.item(i)
            item.setSizeHint(QSize(0, height))
    
    def addMemberItem(self, member_id: int, display_text: str, is_leader: bool = False):
        """
        添加成员项
        
        Args:
            member_id: 成员ID
            display_text: 显示文本
            is_leader: 是否为团队负责人
        """
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, member_id)
        item.setSizeHint(QSize(0, MemberListWidget._shared_item_height))
        
        if is_leader:
            item.setForeground(Qt.darkBlue)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        
        self.addItem(item)
        return item
    
    @classmethod
    def get_shared_height(cls):
        """获取共享行高"""
        return cls._shared_item_height
    
    @classmethod
    def set_shared_height(cls, height):
        """设置共享行高"""
        cls._shared_item_height = height
