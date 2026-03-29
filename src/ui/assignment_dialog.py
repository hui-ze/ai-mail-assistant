# -*- coding: utf-8 -*-
"""
待办分配对话框
Phase 8: 待办分配与提醒功能
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTextEdit, QGroupBox,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..data.database import Database
from ..data.todo_repo import TodoRepo
from ..data.team_member_repo import TeamMemberRepo
from ..core.assignment_service import AssignmentService


class AssignmentDialog(QDialog):
    """待办分配对话框"""
    
    def __init__(self, db: Database, todo_id: int, member_id: int, parent=None):
        """
        初始化对话框
        
        Args:
            db: 数据库实例
            todo_id: 待办ID
            member_id: 当前成员ID(分配人)
            parent: 父窗口
        """
        super().__init__(parent)
        self.db = db
        self.todo_id = todo_id
        self.member_id = member_id
        self.logger = logging.getLogger(__name__)
        
        self.assignment_service = AssignmentService(db)
        self.todo_repo = TodoRepo(db)
        self.member_repo = TeamMemberRepo(db)
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("分配待办")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setFont(QFont("Microsoft YaHei", 10))
        
        layout = QVBoxLayout(self)
        
        # 待办信息
        todo_group = QGroupBox("待办信息")
        todo_layout = QVBoxLayout(todo_group)
        
        self.todo_title_label = QLabel()
        self.todo_title_label.setWordWrap(True)
        self.todo_title_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        todo_layout.addWidget(self.todo_title_label)
        
        layout.addWidget(todo_group)
        
        # 选择成员
        member_group = QGroupBox("选择团队成员")
        member_layout = QVBoxLayout(member_group)
        
        self.member_combo = QComboBox()
        self.member_combo.setFont(QFont("Microsoft YaHei", 10))
        member_layout.addWidget(self.member_combo)
        
        layout.addWidget(member_group)
        
        # 分配说明
        message_group = QGroupBox("分配说明")
        message_layout = QVBoxLayout(message_group)
        
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("请输入分配说明（可选）")
        self.message_edit.setMaximumHeight(100)
        message_layout.addWidget(self.message_edit)
        
        layout.addWidget(message_group)
        
        # 分配历史
        history_group = QGroupBox("分配历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(120)
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.assign_btn = QPushButton("确认分配")
        self.assign_btn.clicked.connect(self._assign_todo)
        btn_layout.addWidget(self.assign_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """加载数据"""
        # 加载待办信息
        todo = self.todo_repo.get_todo_by_id(self.todo_id)
        if todo:
            self.todo_title_label.setText(f"标题: {todo['content']}\n优先级: {todo['priority']}")
        
        # 加载团队成员
        member = self.member_repo.get_by_id(self.member_id)
        if member:
            members = self.member_repo.get_by_department(member.department_id)
            
            for m in members:
                if m.id != self.member_id:  # 排除自己
                    self.member_combo.addItem(
                        f"{m.name} ({m.role})",
                        m.id
                    )
        
        # 加载分配历史
        history = self.assignment_service.get_assignment_history(self.todo_id)
        for item in history:
            assignment = item['assignment']
            from_member = item['from_member']
            to_member = item['to_member']
            
            status_text = {
                'pending': '待处理',
                'accepted': '已接受',
                'rejected': '已拒绝',
                'completed': '已完成'
            }.get(assignment.status, assignment.status)
            
            self.history_list.addItem(
                f"{from_member.name} → {to_member.name} [{status_text}] {assignment.assigned_at}"
            )
    
    def _assign_todo(self):
        """分配待办"""
        if self.member_combo.count() == 0:
            QMessageBox.warning(self, "提示", "没有可分配的团队成员")
            return
        
        to_member_id = self.member_combo.currentData()
        message = self.message_edit.toPlainText().strip()
        
        result = self.assignment_service.assign_todo(
            self.todo_id, self.member_id, to_member_id, message
        )
        
        if result['success']:
            QMessageBox.information(self, "成功", result['message'])
            self.accept()
        else:
            QMessageBox.critical(self, "失败", result['message'])


class PendingAssignmentsDialog(QDialog):
    """待处理分配对话框"""
    
    def __init__(self, db: Database, member_id: int, parent=None):
        """
        初始化对话框
        
        Args:
            db: 数据库实例
            member_id: 当前成员ID
            parent: 父窗口
        """
        super().__init__(parent)
        self.db = db
        self.member_id = member_id
        self.logger = logging.getLogger(__name__)
        
        self.assignment_service = AssignmentService(db)
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("待处理的分配")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setFont(QFont("Microsoft YaHei", 10))
        
        layout = QVBoxLayout(self)
        
        # 分配列表
        list_group = QGroupBox("待处理分配")
        list_layout = QVBoxLayout(list_group)
        
        self.assignment_list = QListWidget()
        self.assignment_list.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.assignment_list)
        
        layout.addWidget(list_group)
        
        # 详情区域
        detail_group = QGroupBox("详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_label = QLabel("请选择一个分配")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        
        # 回复说明
        self.response_edit = QTextEdit()
        self.response_edit.setPlaceholderText("请输入回复说明（可选）")
        self.response_edit.setMaximumHeight(80)
        detail_layout.addWidget(self.response_edit)
        
        layout.addWidget(detail_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.accept_btn = QPushButton("接受")
        self.accept_btn.clicked.connect(self._accept_assignment)
        self.accept_btn.setEnabled(False)
        btn_layout.addWidget(self.accept_btn)
        
        self.reject_btn = QPushButton("拒绝")
        self.reject_btn.clicked.connect(self._reject_assignment)
        self.reject_btn.setEnabled(False)
        btn_layout.addWidget(self.reject_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        """加载数据"""
        self.assignments = self.assignment_service.get_pending_assignments(self.member_id)
        
        self.assignment_list.clear()
        for item in self.assignments:
            assignment = item['assignment']
            todo = item['todo']
            from_member = item['from_member']
            
            self.assignment_list.addItem(
                f"{todo['content']} - 来自 {from_member.name} ({assignment.assigned_at})"
            )
        
        if not self.assignments:
            self.detail_label.setText("暂无待处理的分配")
    
    def _on_selection_changed(self, row: int):
        """选择变化"""
        has_selection = row >= 0
        self.accept_btn.setEnabled(has_selection)
        self.reject_btn.setEnabled(has_selection)
        
        if has_selection and row < len(self.assignments):
            item = self.assignments[row]
            assignment = item['assignment']
            todo = item['todo']
            from_member = item['from_member']
            
            detail_text = f"""
待办: {todo['content']}
优先级: {todo['priority']}
截止日期: {todo.get('due_date', '未设置')}

分配人: {from_member.name} ({from_member.role})
分配时间: {assignment.assigned_at}

分配说明: {assignment.message or '无'}
            """.strip()
            
            self.detail_label.setText(detail_text)
    
    def _accept_assignment(self):
        """接受分配"""
        row = self.assignment_list.currentRow()
        if row < 0 or row >= len(self.assignments):
            return
        
        assignment_id = self.assignments[row]['assignment'].id
        response_message = self.response_edit.toPlainText().strip()
        
        if self.assignment_service.accept_assignment(assignment_id, response_message):
            QMessageBox.information(self, "成功", "已接受分配")
            self._load_data()
        else:
            QMessageBox.critical(self, "失败", "接受分配失败")
    
    def _reject_assignment(self):
        """拒绝分配"""
        row = self.assignment_list.currentRow()
        if row < 0 or row >= len(self.assignments):
            return
        
        assignment_id = self.assignments[row]['assignment'].id
        response_message = self.response_edit.toPlainText().strip()
        
        if not response_message:
            QMessageBox.warning(self, "提示", "拒绝分配时请填写理由")
            return
        
        if self.assignment_service.reject_assignment(assignment_id, response_message):
            QMessageBox.information(self, "成功", "已拒绝分配")
            self._load_data()
        else:
            QMessageBox.critical(self, "失败", "拒绝分配失败")
