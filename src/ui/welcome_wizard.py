# -*- coding: utf-8 -*-
"""
首次使用引导向导
新用户初次启动时，引导完成邮箱配置和基本设置
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QWidget, QLineEdit,
    QFormLayout, QComboBox, QGroupBox, QProgressBar,
    QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush

from ..data.database import Database


class WelcomeWizard(QDialog):
    """首次使用引导向导 - 分步骤引导用户完成配置"""

    PRESET_SERVERS = {
        'QQ邮箱': ('imap.qq.com', 993, '@qq.com'),
        '163邮箱': ('imap.163.com', 993, '@163.com'),
        '126邮箱': ('imap.126.com', 993, '@126.com'),
        'Gmail': ('imap.gmail.com', 993, '@gmail.com'),
        'Outlook': ('imap-mail.outlook.com', 993, '@outlook.com'),
        '企业邮箱(腾讯)': ('imap.exmail.qq.com', 993, ''),
        '手动输入': ('', 993, ''),
    }

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.current_step = 0
        self.total_steps = 3

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("欢迎使用 Foxmail 邮件智能助手")
        self.setModal(True)
        self.setMinimumSize(560, 520)
        self.setFont(QFont("Microsoft YaHei", 10))
        self.setStyleSheet("""
            QDialog {
                background: #f8f9fa;
            }
            QPushButton {
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton#primaryBtn {
                background: #667eea;
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background: #5a6fd6;
            }
            QPushButton#secondaryBtn {
                background: white;
                color: #555;
                border: 1px solid #ddd;
            }
            QPushButton#secondaryBtn:hover {
                background: #f0f0f0;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                background: white;
            }
            QGroupBox::title {
                color: #555;
                subcontrol-origin: margin;
                left: 12px;
                top: -8px;
                background: white;
                padding: 0 4px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏（带渐变）
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)

        title_label = QLabel("✉️  Foxmail 邮件智能助手")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("让 AI 帮您智能处理邮件，提取待办，高效工作")
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 12px;")
        header_layout.addWidget(subtitle_label)

        main_layout.addWidget(header)

        # 步骤进度条
        progress_container = QWidget()
        progress_container.setStyleSheet("background: white; border-bottom: 1px solid #eee;")
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(30, 10, 30, 10)

        self.step_labels = []
        step_names = ["👤 个人信息", "📧 配置邮箱", "🤖 AI设置"]
        for i, name in enumerate(step_names):
            step_btn = QLabel(f"  {i+1}. {name}  ")
            step_btn.setAlignment(Qt.AlignCenter)
            step_btn.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px 8px; border-radius: 12px;")
            self.step_labels.append(step_btn)
            progress_layout.addWidget(step_btn)
            if i < len(step_names) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #ccc;")
                progress_layout.addWidget(arrow)

        main_layout.addWidget(progress_container)

        # 内容区域（StackedWidget 切换步骤）
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background: #f8f9fa;")
        self.stacked.addWidget(self._create_step1_profile())
        self.stacked.addWidget(self._create_step2_email())
        self.stacked.addWidget(self._create_step3_ai())
        main_layout.addWidget(self.stacked, 1)

        # 底部按钮区
        footer = QWidget()
        footer.setStyleSheet("background: white; border-top: 1px solid #eee;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 12, 25, 12)

        self.skip_btn = QPushButton("跳过此步")
        self.skip_btn.setObjectName("secondaryBtn")
        self.skip_btn.clicked.connect(self._on_skip)
        footer_layout.addWidget(self.skip_btn)

        footer_layout.addStretch()

        self.back_btn = QPushButton("← 上一步")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.clicked.connect(self._on_back)
        self.back_btn.setVisible(False)
        footer_layout.addWidget(self.back_btn)

        self.next_btn = QPushButton("下一步 →")
        self.next_btn.setObjectName("primaryBtn")
        self.next_btn.clicked.connect(self._on_next)
        footer_layout.addWidget(self.next_btn)

        main_layout.addWidget(footer)

        # 初始化步骤高亮
        self._update_step_highlight()

    # =================== Step 1: 个人信息 ===================
    def _create_step1_profile(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 10)
        layout.setSpacing(12)

        intro = QLabel("告诉我们一些关于您的信息，帮助 AI 更准确地判断待办归属")
        intro.setStyleSheet("color: #666; font-size: 12px;")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        group = QGroupBox("个人信息（可选，稍后在设置中修改）")
        form = QFormLayout(group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.p_name = QLineEdit()
        self.p_name.setPlaceholderText("例如：张三")
        form.addRow("姓名:", self.p_name)

        self.p_dept = QLineEdit()
        self.p_dept.setPlaceholderText("例如：研发部、市场部")
        form.addRow("部门:", self.p_dept)

        self.p_role = QLineEdit()
        self.p_role.setPlaceholderText("例如：工程师、产品经理、总监")
        form.addRow("职位:", self.p_role)

        self.p_desc = QTextEdit()
        self.p_desc.setPlaceholderText("简述您的工作内容，帮助 AI 判断哪些待办属于您...\n例如：负责后端开发，处理客户需求，撰写技术方案")
        self.p_desc.setMaximumHeight(80)
        form.addRow("工作描述:", self.p_desc)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    # =================== Step 2: 邮箱配置 ===================
    def _create_step2_email(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 10)
        layout.setSpacing(12)

        intro = QLabel("添加您的邮箱账号，应用将通过 IMAP 协议安全获取邮件")
        intro.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(intro)

        group = QGroupBox("邮箱账号配置")
        form = QFormLayout(group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.e_type = QComboBox()
        self.e_type.addItems(list(self.PRESET_SERVERS.keys()))
        self.e_type.currentIndexChanged.connect(self._on_email_type_changed)
        form.addRow("邮箱类型:", self.e_type)

        self.e_email = QLineEdit()
        self.e_email.setPlaceholderText("your-email@qq.com")
        form.addRow("邮箱地址:", self.e_email)

        server_row = QHBoxLayout()
        self.e_server = QLineEdit()
        self.e_server.setPlaceholderText("imap.qq.com")
        server_row.addWidget(self.e_server)
        server_row.addWidget(QLabel(":"))
        self.e_port = QLineEdit("993")
        self.e_port.setMaximumWidth(70)
        server_row.addWidget(self.e_port)
        form.addRow("服务器:", server_row)

        self.e_auth = QLineEdit()
        self.e_auth.setEchoMode(QLineEdit.Password)
        self.e_auth.setPlaceholderText("邮箱授权码（非登录密码）")
        form.addRow("授权码:", self.e_auth)

        layout.addWidget(group)

        # 如何获取授权码提示
        hint_group = QGroupBox("如何获取授权码？")
        hint_layout = QVBoxLayout(hint_group)
        hint = QLabel(
            "<b>QQ邮箱:</b> 邮箱设置 → 账户 → 开启 IMAP/SMTP 服务 → 生成授权码<br>"
            "<b>163邮箱:</b> 设置 → POP/SMTP/IMAP → 开启 IMAP 服务 → 获取授权密码<br>"
            "<b>Gmail:</b> Google账户安全 → 两步验证 → 应用专用密码"
        )
        hint.setStyleSheet("color: #666; font-size: 11px; line-height: 1.6;")
        hint.setWordWrap(True)
        hint_layout.addWidget(hint)
        layout.addWidget(hint_group)
        layout.addStretch()

        # 初始化第一个预设
        self._on_email_type_changed(0)
        return widget

    def _on_email_type_changed(self, index):
        preset_name = self.e_type.currentText()
        server, port, suffix = self.PRESET_SERVERS[preset_name]
        self.e_server.setText(server)
        self.e_port.setText(str(port))
        if suffix and '@' not in self.e_email.text():
            self.e_email.setPlaceholderText(f"账号{suffix}")

    # =================== Step 3: AI 设置 ===================
    def _create_step3_ai(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 10)
        layout.setSpacing(12)

        intro = QLabel("选择 AI 模型来驱动邮件摘要和待办提取功能")
        intro.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(intro)

        # 本地模型选项
        local_group = QGroupBox("🔒 本地模型（免费，隐私保护）")
        local_layout = QVBoxLayout(local_group)
        local_desc = QLabel(
            "使用 <b>Ollama</b> 在本机运行 AI 模型，邮件内容完全不上传到任何服务器。<br>"
            "需要先安装 Ollama 并下载模型（推荐: qwen3:8b 约 5GB）"
        )
        local_desc.setStyleSheet("color: #555; font-size: 11px;")
        local_desc.setWordWrap(True)
        local_layout.addWidget(local_desc)

        ollama_row = QHBoxLayout()
        ollama_row.addWidget(QLabel("Ollama 地址:"))
        self.ai_ollama_url = QLineEdit("http://localhost:11434")
        ollama_row.addWidget(self.ai_ollama_url)
        local_layout.addLayout(ollama_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("模型名称:"))
        self.ai_model = QLineEdit("qwen3:8b")
        model_row.addWidget(self.ai_model)
        local_layout.addLayout(model_row)

        layout.addWidget(local_group)

        # 云端模型选项
        cloud_group = QGroupBox("☁️ 云端 API（付费，效果更好）")
        cloud_layout = QVBoxLayout(cloud_group)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("服务商:"))
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["Ollama（本地）", "DeepSeek", "通义千问", "文心一言"])
        provider_row.addWidget(self.ai_provider)
        cloud_layout.addLayout(provider_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self.ai_key = QLineEdit()
        self.ai_key.setEchoMode(QLineEdit.Password)
        self.ai_key.setPlaceholderText("如选择云端服务，在此填入 API Key")
        key_row.addWidget(self.ai_key)
        cloud_layout.addLayout(key_row)

        layout.addWidget(cloud_group)

        finish_hint = QLabel('✅ 完成设置后即可开始使用！设置可随时在"设置"中修改。')
        finish_hint.setStyleSheet(
            "color: #4caf50; font-size: 12px; padding: 8px 12px; "
            "background: #e8f5e9; border-radius: 6px;"
        )
        finish_hint.setWordWrap(True)
        layout.addWidget(finish_hint)
        layout.addStretch()
        return widget

    # =================== 导航逻辑 ===================
    def _update_step_highlight(self):
        for i, label in enumerate(self.step_labels):
            if i == self.current_step:
                label.setStyleSheet(
                    "color: white; font-size: 11px; padding: 4px 8px; "
                    "border-radius: 12px; background: #667eea;"
                )
            elif i < self.current_step:
                label.setStyleSheet(
                    "color: #4caf50; font-size: 11px; padding: 4px 8px; "
                    "border-radius: 12px; background: #e8f5e9;"
                )
            else:
                label.setStyleSheet(
                    "color: #aaa; font-size: 11px; padding: 4px 8px; "
                    "border-radius: 12px;"
                )

        self.back_btn.setVisible(self.current_step > 0)
        is_last = self.current_step == self.total_steps - 1
        self.next_btn.setText("完成设置 ✓" if is_last else "下一步 →")
        self.skip_btn.setVisible(self.current_step < self.total_steps - 1)

    def _on_next(self):
        if self.current_step == 0:
            self._save_step1()
        elif self.current_step == 1:
            if not self._save_step2():
                return  # 验证失败，不跳转
        elif self.current_step == 2:
            self._save_step3()
            self.accept()
            return

        self.current_step += 1
        self.stacked.setCurrentIndex(self.current_step)
        self._update_step_highlight()

    def _on_back(self):
        self.current_step -= 1
        self.stacked.setCurrentIndex(self.current_step)
        self._update_step_highlight()

    def _on_skip(self):
        """跳过当前步骤"""
        self.current_step += 1
        if self.current_step >= self.total_steps:
            self.accept()
            return
        self.stacked.setCurrentIndex(self.current_step)
        self._update_step_highlight()

    # =================== 保存逻辑 ===================
    def _save_step1(self):
        """保存个人信息"""
        name = self.p_name.text().strip()
        dept = self.p_dept.text().strip()
        role = self.p_role.text().strip()
        desc = self.p_desc.toPlainText().strip()

        if any([name, dept, role, desc]):
            try:
                from ..data.user_profile_repo import UserProfileRepo
                repo = UserProfileRepo(self.db)
                repo.update_profile(name=name, department=dept, role=role, work_description=desc)
                self.logger.info("用户画像已保存")
            except Exception as e:
                self.logger.warning(f"保存用户画像失败: {e}")

    def _save_step2(self) -> bool:
        """保存邮箱配置，返回是否成功"""
        email = self.e_email.text().strip()
        server = self.e_server.text().strip()
        port_text = self.e_port.text().strip()
        auth_code = self.e_auth.text().strip()

        # 如果全为空，说明用户跳过
        if not any([email, auth_code]):
            return True

        if not email or '@' not in email:
            QMessageBox.warning(self, "提示", "请输入正确的邮箱地址，或点击「跳过此步」")
            self.e_email.setFocus()
            return False

        if not server:
            QMessageBox.warning(self, "提示", "请填写 IMAP 服务器地址")
            self.e_server.setFocus()
            return False

        if not auth_code:
            QMessageBox.warning(self, "提示", "请填写授权码，或点击「跳过此步」")
            self.e_auth.setFocus()
            return False

        try:
            port = int(port_text) if port_text else 993
        except ValueError:
            QMessageBox.warning(self, "提示", "端口必须是数字")
            return False

        try:
            sql = '''
                INSERT OR IGNORE INTO accounts 
                (email_address, imap_server, imap_port, auth_code_encrypted, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            '''
            self.db.execute(sql, (email, server, port, auth_code))
            self.logger.info(f"引导向导添加账号: {email}")
        except Exception as e:
            self.logger.error(f"保存账号失败: {e}")
            QMessageBox.warning(self, "错误", f"保存账号失败: {e}")
            return False

        return True

    def _save_step3(self):
        """保存 AI 设置"""
        try:
            ollama_url = self.ai_ollama_url.text().strip() or 'http://localhost:11434'
            model = self.ai_model.text().strip() or 'qwen3:8b'
            provider_idx = self.ai_provider.currentIndex()
            provider_map = {0: 'ollama', 1: 'deepseek', 2: 'qianwen', 3: 'wenxin'}
            provider = provider_map.get(provider_idx, 'ollama')

            sql = '''
                UPDATE settings SET
                ai_provider = ?,
                ollama_url = ?,
                ollama_model = ?
                WHERE id = 1
            '''
            self.db.execute(sql, (provider, ollama_url, model))

            api_key = self.ai_key.text().strip()
            if api_key and provider != 'ollama':
                self.db.execute(
                    "UPDATE settings SET cloud_api_key_encrypted = ? WHERE id = 1",
                    (api_key,)
                )

            self.logger.info(f"AI设置已保存: provider={provider}, model={model}")
        except Exception as e:
            self.logger.warning(f"保存AI设置失败: {e}")
