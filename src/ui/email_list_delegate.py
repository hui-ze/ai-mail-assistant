# -*- coding: utf-8 -*-
"""
邮件列表委托
自定义邮件列表项的渲染样式
"""

from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPainter

from ..core.imap_client import EmailData


class EmailListDelegate(QStyledItemDelegate):
    """邮件列表项委托"""

    # 邮件项高度
    ITEM_HEIGHT = 65

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_height = self.ITEM_HEIGHT

    def setItemHeight(self, height: int):
        """设置列表项高度"""
        self.item_height = height

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """返回列表项大小"""
        return QSize(option.rect.width(), self.item_height)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """绘制列表项
        
        Args:
            email_data: dict 格式的邮件数据（从 EmailRepo.get_emails_by_account 返回）
        """
        # 获取数据
        email_data = index.data(Qt.UserRole)
        
        # 保存原始画笔
        painter.save()
        
        # 提取邮件属性（兼容 dict 和 EmailData 对象）
        if isinstance(email_data, dict):
            is_read = email_data.get('is_read', True)
            has_attachments = email_data.get('has_attachments', False)
            priority = email_data.get('priority', 'normal')
            sender = email_data.get('sender', '未知发件人')
            subject = email_data.get('subject', '无主题')
            date_str = email_data.get('date', '')
            body = email_data.get('body', '')
        else:
            # 兼容旧的 EmailData 对象（如果有）
            is_read = getattr(email_data, 'is_read', True)
            has_attachments = getattr(email_data, 'has_attachments', False)
            priority = getattr(email_data, 'priority', 'normal')
            sender = getattr(email_data, 'sender', '未知发件人')
            subject = getattr(email_data, 'subject', '无主题')
            date_str = getattr(email_data, 'date', '')
            body = getattr(email_data, 'body', '')

        # 绘制背景
        if option.state & QStyle.State_Selected:
            # 选中状态 - 淡紫色背景
            painter.fillRect(option.rect, QColor("#E0E7FF"))
        elif option.state & QStyle.State_MouseOver:
            # 悬停状态
            painter.fillRect(option.rect, QColor("#F0F4FF"))
        elif not is_read:
            # 未读邮件 - 淡紫色背景高亮
            painter.fillRect(option.rect, QColor("#EEF2FF"))
            # 左侧强调线（3px宽的紫色竖线）
            painter.fillRect(
                option.rect.left(), option.rect.top(), 
                3, option.rect.height(), 
                QColor("#667eea")
            )
        else:
            # 已读邮件 - 交替行颜色
            if index.row() % 2 == 0:
                painter.fillRect(option.rect, QColor("#ffffff"))
            else:
                painter.fillRect(option.rect, QColor("#f8f8f8"))

        # 边距
        margin = 10
        rect = option.rect.adjusted(margin, 5, -margin, -5)
        
        # 左侧偏移（为未读标记留空间）
        left_offset = 8 if not is_read else 0

        # 发件人
        font_sender = QFont("Microsoft YaHei", 10, QFont.Bold if not is_read else QFont.Normal)
        painter.setFont(font_sender)
        sender_color = QColor("#000000") if not is_read else QColor("#333333")
        painter.setPen(sender_color)

        sender_text = sender[:20] + "..." if len(sender) > 20 else sender
        painter.drawText(rect.left() + left_offset, rect.top() + 15, sender_text)

        # 日期（右上角）
        font_date = QFont("Microsoft YaHei", 9)
        painter.setFont(font_date)
        date_color = QColor("#888888")
        painter.setPen(date_color)

        date_text = date_str.split(" ")[0] if date_str and len(date_str) > 10 else date_str
        painter.drawText(rect.right() - 70, rect.top() + 15, date_text)

        # 主题
        font_subject = QFont("Microsoft YaHei", 9)
        painter.setFont(font_subject)
        subject_color = QColor("#333333") if not is_read else QColor("#666666")
        painter.setPen(subject_color)

        subject_text = subject[:35] + "..." if len(subject) > 35 else subject
        painter.drawText(rect.left() + left_offset, rect.top() + 35, subject_text)

        # 预览文本（第二行）
        font_preview = QFont("Microsoft YaHei", 8)
        painter.setFont(font_preview)
        preview_color = QColor("#999999")
        painter.setPen(preview_color)

        preview_text = body[:50].replace("\n", " ").strip() + "..." if body else ""
        painter.drawText(rect.left() + left_offset, rect.top() + 52, preview_text)

        # 附件标记
        if has_attachments:
            font_icon = QFont("Segoe UI Emoji", 9)
            painter.setFont(font_icon)
            painter.setPen(QColor("#888888"))
            painter.drawText(rect.right() - 25, rect.top() + 15, "📎")

        # 优先级标记（右侧色条）
        if priority and priority != 'normal':
            priority_colors = {
                'high': '#EF4444',    # 红色
                'medium': '#F59E0B',  # 橙色
                'low': '#10B981'      # 绿色
            }
            color = priority_colors.get(priority, '#9CA3AF')
            painter.fillRect(
                option.rect.right() - 4, option.rect.top() + 10,
                3, option.rect.height() - 20,
                QColor(color)
            )

        # 恢复画笔
        painter.restore()


class EmailListWidget(QStyledItemDelegate):
    """
    邮件列表组件（带自定义委托）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_height = self.ITEM_HEIGHT

    def setItemHeight(self, height: int):
        """设置列表项高度"""
        self.item_height = height
