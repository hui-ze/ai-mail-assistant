# -*- coding: utf-8 -*-
"""
添加账号对话框
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QComboBox,
    QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..data.database import Database


class AddAccountDialog(QDialog):
    """添加邮件账号对话框"""

    # 常用邮箱服务器配置
    PRESET_SERVERS = {
        'QQ邮箱': ('imap.qq.com', 993),
        '163邮箱': ('imap.163.com', 993),
        'Gmail': ('imap.gmail.com', 993),
        'Outlook': ('imap-mail.outlook.com', 993),
        '企业邮箱': ('imap.exmail.qq.com', 993),
    }

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.logger = logging.getLogger(__name__)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("添加邮件账号")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setFont(QFont("Microsoft YaHei", 10))

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 提示信息
        hint = QLabel("💡 请输入您的邮箱账号和授权码")
        hint.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(hint)

        # 邮箱选择/输入
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(10)

        # 邮箱类型预设
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['手动输入'] + list(self.PRESET_SERVERS.keys()))
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form_layout.addRow("邮箱类型:", self.preset_combo)

        # 邮箱地址
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your-email@example.com")
        form_layout.addRow("邮箱地址:", self.email_input)

        # IMAP服务器
        server_layout = QHBoxLayout()
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("imap.example.com")
        server_layout.addWidget(self.server_input)

        # 端口
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("993")
        self.port_input.setMaximumWidth(80)
        server_layout.addWidget(QLabel(" : "))
        server_layout.addWidget(self.port_input)

        form_layout.addRow("服务器:", server_layout)

        # 授权码
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("授权码/密码")
        self.auth_code_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("授权码:", self.auth_code_input)

        layout.addLayout(form_layout)

        # 帮助信息
        help_group = QGroupBox("如何获取授权码？")
        help_layout = QVBoxLayout(help_group)

        help_text = QLabel("""
        <b>QQ邮箱:</b> 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 → 开启IMAP/SMTP服务<br>
        <b>163邮箱:</b> 设置 → POP/SMTP/IMAP → 开启IMAP/SMTP服务<br>
        <b>Gmail:</b> 设置 → 转发和POP/IMAP → 启用IMAP
        """)
        help_text.setStyleSheet("color: #555; background: #f5f5f5; padding: 10px; border-radius: 5px;")
        help_layout.addWidget(help_text)
        layout.addWidget(help_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_account)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _test_connection(self):
        """测试 IMAP 连接"""
        email = self.email_input.text().strip()
        server = self.server_input.text().strip()
        port_text = self.port_input.text().strip()
        auth_code = self.auth_code_input.text().strip()

        # 验证输入
        if not email or '@' not in email:
            QMessageBox.warning(self, '错误', '请输入正确的邮箱地址')
            return

        if not server:
            QMessageBox.warning(self, '错误', '请输入 IMAP 服务器地址')
            return

        if not auth_code:
            QMessageBox.warning(self, '错误', '请输入授权码')
            return

        try:
            port = int(port_text) if port_text else 993
        except ValueError:
            QMessageBox.warning(self, '错误', '端口必须是数字')
            return

        # 执行连接测试
        import socket
        import imaplib
        from PyQt5.QtWidgets import QApplication

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            socket.setdefaulttimeout(15)
            conn = imaplib.IMAP4_SSL(server, port)
            result = conn.login(email, auth_code)
            conn.logout()
            
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, '成功', f'✅ 连接成功！\n\n登录响应: {result[1][0].decode()}')
            
        except socket.timeout:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, '失败', '❌ 连接超时，请检查网络或服务器地址')
        except imaplib.IMAP4.error as e:
            QApplication.restoreOverrideCursor()
            error_msg = str(e) if not isinstance(e, bytes) else e.decode('utf-8', errors='ignore')
            QMessageBox.critical(self, '失败', f'❌ 登录失败：授权码错误或 IMAP 服务未开启\n\n{error_msg}')
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, '失败', f'❌ 连接失败: {type(e).__name__}: {e}')

    def _on_preset_changed(self, index: int):
        """预设变更"""
        if index == 0:  # 手动输入
            self.server_input.clear()
            self.port_input.clear()
            self.email_input.setFocus()
        else:
            preset_name = self.preset_combo.currentText()
            server, port = self.PRESET_SERVERS[preset_name]
            self.server_input.setText(server)
            self.port_input.setText(str(port))

            # 尝试填充邮箱后缀
            if '@' not in self.email_input.text():
                domain_map = {
                    'QQ邮箱': '@qq.com',
                    '163邮箱': '@163.com',
                    'Gmail': '@gmail.com',
                    'Outlook': '@outlook.com',
                    '企业邮箱': '',
                }
                suffix = domain_map.get(preset_name, '')
                if suffix:
                    # 添加一个占位符邮箱前缀
                    self.email_input.setPlaceholderText(f"输入账号{suffix}")

    def save_account(self):
        """保存账号"""
        email = self.email_input.text().strip()
        server = self.server_input.text().strip()
        port_text = self.port_input.text().strip()
        auth_code = self.auth_code_input.text().strip()

        # 验证输入
        if not email:
            QMessageBox.warning(self, '错误', '请输入邮箱地址')
            self.email_input.setFocus()
            return

        if '@' not in email:
            QMessageBox.warning(self, '错误', '邮箱格式不正确')
            self.email_input.setFocus()
            return

        if not server:
            QMessageBox.warning(self, '错误', '请输入IMAP服务器地址')
            self.server_input.setFocus()
            return

        if not auth_code:
            QMessageBox.warning(self, '错误', '请输入授权码')
            self.auth_code_input.setFocus()
            return

        # 端口处理
        try:
            port = int(port_text) if port_text else 993
        except ValueError:
            QMessageBox.warning(self, '错误', '端口必须是数字')
            self.port_input.setFocus()
            return

        try:
            # 保存到数据库
            sql = '''
                INSERT INTO accounts 
                (email_address, imap_server, imap_port, auth_code_encrypted, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            '''
            self.db.execute(sql, (email, server, port, auth_code))

            self.logger.info(f"Account added: {email}")
            QMessageBox.information(self, '成功', f'账号 {email} 添加成功！')
            self.accept()

        except Exception as e:
            self.logger.error(f"Failed to save account: {e}")
            if 'UNIQUE constraint' in str(e):
                QMessageBox.warning(self, '错误', '该账号已存在')
            else:
                QMessageBox.warning(self, '错误', f'保存失败: {str(e)}')
