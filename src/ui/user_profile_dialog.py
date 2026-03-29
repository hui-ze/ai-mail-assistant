# -*- coding: utf-8 -*-
"""
用户画像引导对话框
首次启动时引导用户填写画像信息
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QFormLayout
)
from PyQt5.QtCore import Qt

from ..data.user_profile_repo import UserProfileRepo
from ..utils.icon_manager import get_icon_manager


class UserProfileDialog(QDialog):
    """用户画像引导对话框"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.profile_repo = UserProfileRepo(db)
        self.logger = logging.getLogger(__name__)
        
        self._init_ui()
        self._load_existing_profile()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("欢迎使用 Foxmail 邮件智能助手")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # 设置窗口图标
        try:
            icon_manager = get_icon_manager()
            icon_manager.setup_window_icon(self)
        except Exception:
            pass  # 图标设置失败不影响功能
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 欢迎信息
        welcome_label = QLabel(
            "👋 为了更好地为您分析待办事项，请填写以下信息："
        )
        welcome_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 姓名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("您的姓名")
        self.name_edit.setMaximumHeight(30)
        form_layout.addRow("姓名：", self.name_edit)
        
        # 部门
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("例如：产品部、技术部")
        self.department_edit.setMaximumHeight(30)
        form_layout.addRow("部门：", self.department_edit)
        
        # 职位
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("例如：产品经理、开发工程师")
        self.role_edit.setMaximumHeight(30)
        form_layout.addRow("职位：", self.role_edit)
        
        # 工作描述
        self.work_desc_edit = QTextEdit()
        self.work_desc_edit.setPlaceholderText(
            "请简要描述您的工作职责，有助于AI更准确地判断待办归属。\n"
            "例如：负责用户增长、数据分析、产品规划"
        )
        self.work_desc_edit.setMaximumHeight(100)
        form_layout.addRow("工作描述：", self.work_desc_edit)
        
        layout.addLayout(form_layout)
        
        # 说明文字
        note_label = QLabel(
            "💡 提示：这些信息将帮助AI更准确地判断邮件中的待办事项是否属于您。"
        )
        note_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        skip_btn = QPushButton("跳过")
        skip_btn.setMaximumWidth(80)
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)
        
        save_btn = QPushButton("保存并继续")
        save_btn.setMaximumWidth(120)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_and_accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_existing_profile(self):
        """加载现有画像"""
        profile = self.profile_repo.get_profile()
        
        if profile.get('name'):
            self.name_edit.setText(profile['name'])
        if profile.get('department'):
            self.department_edit.setText(profile['department'])
        if profile.get('role'):
            self.role_edit.setText(profile['role'])
        if profile.get('work_description'):
            self.work_desc_edit.setPlainText(profile['work_description'])
    
    def _save_and_accept(self):
        """保存并接受"""
        name = self.name_edit.text().strip()
        department = self.department_edit.text().strip()
        role = self.role_edit.text().strip()
        work_description = self.work_desc_edit.toPlainText().strip()
        
        # 保存到数据库
        self.profile_repo.update_profile(
            name=name,
            department=department,
            role=role,
            work_description=work_description
        )
        
        self.logger.info(f"用户画像已保存: {name}, {department}, {role}")
        self.accept()
    
    def get_profile(self):
        """获取当前输入的画像"""
        return {
            'name': self.name_edit.text().strip(),
            'department': self.department_edit.text().strip(),
            'role': self.role_edit.text().strip(),
            'work_description': self.work_desc_edit.toPlainText().strip()
        }
