# -*- coding: utf-8 -*-
"""
摘要面板和待办面板组件
"""

import logging
from typing import List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QScrollArea, QCheckBox,
    QProgressBar, QTextBrowser
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPalette

from ..data.summary_repo import SummaryRepo, SummaryResult
from ..data.todo_repo import TodoRepo, TodoItem
from ..core.ai_bridge import AIBridge


class SummaryPanel(QWidget):
    """摘要面板 - 显示AI生成的邮件摘要"""

    regenerate_requested = pyqtSignal(int)  # 重新生成信号

    def __init__(self, summary_repo: SummaryRepo, parent=None):
        super().__init__(parent)
        self.summary_repo = summary_repo
        self.current_email_id: Optional[int] = None
        self.logger = logging.getLogger(__name__)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题栏
        header_layout = QHBoxLayout()
        title = QLabel("📝 AI摘要")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        # 重新生成按钮
        self.regenerate_btn = QPushButton("🔄 重新生成")
        self.regenerate_btn.clicked.connect(self._on_regenerate)
        self.regenerate_btn.setEnabled(False)
        header_layout.addWidget(self.regenerate_btn)

        layout.addLayout(header_layout)

        # 摘要内容
        self.summary_text = QTextBrowser()
        self.summary_text.setOpenExternalLinks(True)
        self.summary_text.setStyleSheet("""
            QTextBrowser {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.summary_text)

        # 加载状态
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # 无限循环
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)

        # 元信息
        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self.meta_label)

        # 初始提示
        self.summary_text.setHtml("""
            <div style="text-align: center; color: #999; padding: 50px;">
                <p>📋 选择一封邮件</p>
                <p style="font-size: 10pt;">AI将自动生成摘要</p>
            </div>
        """)

    def load_summary(self, email_id: int):
        """加载指定邮件的摘要"""
        self.current_email_id = email_id
        self.regenerate_btn.setEnabled(True)

        # 显示加载状态
        self.loading_bar.setVisible(True)
        self.summary_text.setHtml("""
            <div style="text-align: center; color: #666; padding: 50px;">
                <p>正在生成摘要...</p>
            </div>
        """)

        # 从数据库加载摘要
        summary = self.summary_repo.get_summary_by_email_id(email_id)

        if summary:
            self._display_summary(summary)
        else:
            # 没有摘要，提示生成
            self.summary_text.setHtml("""
                <div style="text-align: center; color: #666; padding: 50px;">
                    <p>暂无摘要</p>
                    <p style="font-size: 10pt;">点击"重新生成"按钮创建摘要</p>
                </div>
            """)

        self.loading_bar.setVisible(False)

    def _display_summary(self, summary: SummaryResult):
        """显示摘要"""
        html = f"""
        <div style="font-family: 'Microsoft YaHei', sans-serif;">
            <h4 style="color: #333; margin: 0 0 10px 0;">{summary.title}</h4>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="color: #555; line-height: 1.6;">{summary.summary_text}</p>
            <p style="color: #888; font-size: 9pt; margin-top: 15px;">
                生成时间: {summary.created_at}
            </p>
        </div>
        """
        self.summary_text.setHtml(html)
        self.meta_label.setText(f"摘要长度: {len(summary.summary_text)} 字符")

    def _on_regenerate(self):
        """重新生成"""
        if self.current_email_id:
            self.regenerate_requested.emit(self.current_email_id)

    def set_loading(self, loading: bool):
        """设置加载状态"""
        self.loading_bar.setVisible(loading)
        if loading:
            self.regenerate_btn.setEnabled(False)
        else:
            self.regenerate_btn.setEnabled(self.current_email_id is not None)


class TodoPanel(QWidget):
    """待办事项面板 - 显示从邮件中提取的待办"""

    todo_completed = pyqtSignal(int)  # 待办完成信号
    todo_deleted = pyqtSignal(int)  # 待办删除信号

    def __init__(self, todo_repo: TodoRepo, parent=None):
        super().__init__(parent)
        self.todo_repo = todo_repo
        self.logger = logging.getLogger(__name__)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题栏
        header_layout = QHBoxLayout()
        title = QLabel("✅ 待办事项")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        # 统计
        self.stats_label = QLabel("0 项待办")
        self.stats_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.stats_label)

        layout.addLayout(header_layout)

        # 待办列表
        self.todo_list = QListWidget()
        self.todo_list.setAlternatingRowColors(True)
        self.todo_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.todo_list)

        # 按钮栏
        button_layout = QHBoxLayout()

        complete_btn = QPushButton("✓ 标记完成")
        complete_btn.clicked.connect(self._on_mark_complete)
        button_layout.addWidget(complete_btn)

        delete_btn = QPushButton("🗑 删除")
        delete_btn.clicked.connect(self._on_delete)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        add_btn = QPushButton("+ 添加待办")
        add_btn.clicked.connect(self._on_add_todo)
        button_layout.addWidget(add_btn)

        layout.addLayout(button_layout)

    def load_todos(self, email_id: Optional[int] = None):
        """加载待办事项"""
        self.todo_list.clear()

        if email_id:
            todos = self.todo_repo.get_todos_by_email_id(email_id)
        else:
            todos = self.todo_repo.get_all_todos()

        for todo in todos:
            self._add_todo_item(todo)

        # 更新统计
        total = len(todos)
        completed = sum(1 for t in todos if t.is_completed)
        self.stats_label.setText(f"{completed}/{total} 已完成")

    def _add_todo_item(self, todo: TodoItem):
        """添加待办项"""
        item = QListWidgetItem()
        self.todo_list.addItem(item)

        # 创建自定义widget
        widget = TodoItemWidget(todo)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, todo)

        self.todo_list.setItemWidget(item, widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        """列表项点击"""
        todo = item.data(Qt.UserRole)
        if todo:
            # 切换完成状态
            new_status = not todo.is_completed
            self.todo_repo.update_todo_status(todo.id, new_status)
            self.load_todos()  # 重新加载

    def _on_mark_complete(self):
        """标记完成"""
        current_item = self.todo_list.currentItem()
        if current_item:
            todo = current_item.data(Qt.UserRole)
            if todo:
                self.todo_repo.update_todo_status(todo.id, True)
                self.load_todos()
                self.todo_completed.emit(todo.id)

    def _on_delete(self):
        """删除待办"""
        current_item = self.todo_list.currentItem()
        if current_item:
            todo = current_item.data(Qt.UserRole)
            if todo:
                self.todo_repo.delete_todo(todo.id)
                self.load_todos()
                self.todo_deleted.emit(todo.id)

    def _on_add_todo(self):
        """添加待办"""
        # TODO: 实现添加待办对话框
        pass


class TodoItemWidget(QWidget):
    """待办事项列表项组件"""

    def __init__(self, todo: TodoItem, parent=None):
        super().__init__(parent)
        self.todo = todo

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 复选框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.todo.is_completed)
        layout.addWidget(self.checkbox)

        # 内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # 标题
        title_label = QLabel(self.todo.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'#999' if self.todo.is_completed else '#333'};
                text-decoration: {'line-through' if self.todo.is_completed else 'none'};
                font-weight: bold;
            }}
        """)
        content_layout.addWidget(title_label)

        # 截止日期
        if self.todo.due_date:
            due_label = QLabel(f"截止: {self.todo.due_date}")
            due_label.setStyleSheet("color: #888; font-size: 9pt;")
            content_layout.addWidget(due_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        # 归属标记（Phase 6 新增）
        if self.todo.assign_type:
            assign_label = QLabel()
            tag_text = {
                'self': '我',
                'other': '其他',
                'team': '团队',
                'unknown': '未知'
            }.get(self.todo.assign_type, '未知')

            tag_color = {
                'self': '#4CAF50',    # 绿色
                'other': '#FF9800',   # 橙色
                'team': '#2196F3',    # 蓝色
                'unknown': '#9E9E9E'  # 灰色
            }.get(self.todo.assign_type, '#9E9E9E')

            assign_label.setText(tag_text)
            assign_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {tag_color};
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 9pt;
                    font-weight: bold;
                }}
            """)
            layout.addWidget(assign_label)

        # 优先级标记
        if self.todo.priority == 'high':
            priority_label = QLabel("🔴")
            layout.addWidget(priority_label)
        elif self.todo.priority == 'medium':
            priority_label = QLabel("🟡")
            layout.addWidget(priority_label)

    def sizeHint(self) -> QSize:
        """返回大小提示"""
        return QSize(200, 50)
