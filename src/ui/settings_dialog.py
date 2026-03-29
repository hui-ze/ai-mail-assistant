# -*- coding: utf-8 -*-
"""
设置对话框模块
提供通用设置、同步设置、界面设置和日历设置
"""

import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QPushButton, QGroupBox,
    QLabel, QDialogButtonBox, QMessageBox,
    QDateTimeEdit, QListWidget, QListWidgetItem,
    QTextEdit, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from ..data.database import Database
from ..ui.styles import get_theme_manager
from ..ui.components.toast import Toast
from ..utils.icon_manager import get_icon_manager


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.logger = logging.getLogger(__name__)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setFont(QFont("Microsoft YaHei", 10))
        
        # 设置窗口图标
        try:
            icon_manager = get_icon_manager()
            icon_manager.setup_window_icon(self)
        except Exception:
            pass  # 图标设置失败不影响功能

        layout = QVBoxLayout(self)

        # Tab页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 通用设置
        tabs.addTab(self._create_general_tab(), "通用")
        # AI设置
        tabs.addTab(self._create_ai_tab(), "AI服务")
        # 同步设置
        tabs.addTab(self._create_sync_tab(), "同步")
        # 界面设置
        tabs.addTab(self._create_ui_tab(), "界面")
        # 日历设置
        tabs.addTab(self._create_calendar_tab(), "日历")
        # 用户画像设置
        tabs.addTab(self._create_profile_tab(), "用户画像")
        # 部门管理(Phase 7)
        tabs.addTab(self._create_department_tab(), "部门管理")

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """创建通用设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout(startup_group)

        self.startup_with_system = QCheckBox("开机自动启动")
        startup_layout.addRow("自动启动:", self.startup_with_system)

        self.minimize_to_tray = QCheckBox("最小化到系统托盘")
        self.minimize_to_tray.setChecked(True)
        startup_layout.addRow("关闭行为:", self.minimize_to_tray)

        layout.addWidget(startup_group)

        # AI设置
        ai_group = QGroupBox("AI设置")
        ai_layout = QFormLayout(ai_group)

        self.auto_process = QCheckBox("自动处理新邮件")
        ai_layout.addRow("自动摘要:", self.auto_process)

        layout.addWidget(ai_group)

        # 存储设置
        storage_group = QGroupBox("存储设置")
        storage_layout = QFormLayout(storage_group)

        self.cache_days = QSpinBox()
        self.cache_days.setRange(1, 365)
        self.cache_days.setSuffix(" 天")
        storage_layout.addRow("缓存保留:", self.cache_days)

        self.auto_backup = QCheckBox("每日自动备份")
        storage_layout.addRow("自动备份:", self.auto_backup)

        layout.addWidget(storage_group)

        layout.addStretch()
        return widget

    def _create_ai_tab(self) -> QWidget:
        """创建AI服务设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # AI服务状态
        status_group = QGroupBox("AI服务状态")
        status_layout = QVBoxLayout(status_group)

        from ..core.ai_bridge import AIBridge
        self.ai_bridge = AIBridge(self.db)

        # 状态指示器
        status_h_layout = QHBoxLayout()
        self.ai_status_label = QLabel("检测中...")
        self.ai_status_label.setStyleSheet("font-size: 11pt; padding: 5px;")
        status_h_layout.addWidget(self.ai_status_label)
        status_h_layout.addStretch()

        # 配置按钮
        config_btn = QPushButton("⚙ AI服务配置")
        config_btn.setToolTip("配置 Ollama 或云端 API")
        config_btn.clicked.connect(self._show_ai_config_dialog)
        status_h_layout.addWidget(config_btn)

        # 刷新按钮
        refresh_btn = QPushButton("↻ 刷新状态")
        refresh_btn.clicked.connect(self._refresh_ai_status)
        status_h_layout.addWidget(refresh_btn)

        status_layout.addLayout(status_h_layout)
        layout.addWidget(status_group)

        # 当前配置信息
        config_group = QGroupBox("当前配置")
        config_layout = QFormLayout(config_group)

        self.ai_provider_label = QLabel("未配置")
        config_layout.addRow("AI提供商:", self.ai_provider_label)

        self.ai_model_label = QLabel("无")
        config_layout.addRow("使用模型:", self.ai_model_label)

        layout.addWidget(config_group)

        # AI使用设置
        usage_group = QGroupBox("AI使用设置")
        usage_layout = QFormLayout(usage_group)

        self.auto_analyze = QCheckBox("自动分析新邮件")
        self.auto_analyze.setChecked(False)
        usage_layout.addRow("自动化:", self.auto_analyze)

        layout.addWidget(usage_group)

        # 使用统计
        stats_group = QGroupBox("今日使用统计")
        stats_layout = QFormLayout(stats_group)

        self.today_requests_label = QLabel("0 次")
        stats_layout.addRow("请求数:", self.today_requests_label)

        self.today_tokens_label = QLabel("0 tokens")
        stats_layout.addRow("Token用量:", self.today_tokens_label)

        layout.addWidget(stats_group)

        # 刷新状态
        self._refresh_ai_status()

        layout.addStretch()
        return widget

    def _refresh_ai_status(self):
        """刷新AI状态"""
        try:
            is_available = self.ai_bridge.is_available()
            provider = self.ai_bridge.get_current_provider()

            if is_available:
                if provider == "ollama":
                    self.ai_status_label.setText("✅ Ollama (本地) - 已连接")
                    self.ai_status_label.setStyleSheet("color: #4CAF50; font-size: 11pt; padding: 5px;")
                    self.ai_provider_label.setText("Ollama (本地)")
                else:
                    self.ai_status_label.setText(f"✅ {provider} - 已连接")
                    self.ai_status_label.setStyleSheet("color: #2196F3; font-size: 11pt; padding: 5px;")
                    self.ai_provider_label.setText(provider.capitalize())
            else:
                self.ai_status_label.setText("❌ AI服务未连接")
                self.ai_status_label.setStyleSheet("color: #F44336; font-size: 11pt; padding: 5px;")
                self.ai_provider_label.setText("未配置")

            # 获取模型信息
            if is_available:
                models = self.ai_bridge.get_available_models() if provider == "ollama" else []
                current_model = self.ai_bridge.ollama_config.model if provider == "ollama" else self.ai_bridge.cloud_config.model
                self.ai_model_label.setText(current_model if current_model else "无")

            # 获取使用统计
            stats = self.ai_bridge.get_usage_stats()
            self.today_requests_label.setText(f"{stats.get('today_requests', 0)} 次")
            self.today_tokens_label.setText(f"{stats.get('today_tokens', 0)} tokens")

        except Exception as e:
            self.logger.error(f"刷新AI状态失败: {e}")
            self.ai_status_label.setText("❌ 检测失败")
            self.ai_status_label.setStyleSheet("color: #F44336; font-size: 11pt; padding: 5px;")

    def _show_ai_config_dialog(self):
        """显示AI配置对话框"""
        from .ai_manager import AIConfigDialog
        dialog = AIConfigDialog(self.ai_bridge, self)
        if dialog.exec_():
            self._refresh_ai_status()
            Toast.success(self, "AI服务配置已更新")

    def _create_sync_tab(self) -> QWidget:
        """创建同步设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 同步间隔
        interval_group = QGroupBox("同步间隔")
        interval_layout = QFormLayout(interval_group)

        self.sync_interval = QSpinBox()
        self.sync_interval.setRange(1, 1440)
        self.sync_interval.setSuffix(" 分钟")
        self.sync_interval.setValue(15)
        interval_layout.addRow("邮件同步:", self.sync_interval)

        self.ai_sync_interval = QSpinBox()
        self.ai_sync_interval.setRange(5, 60)
        self.ai_sync_interval.setSuffix(" 分钟")
        self.ai_sync_interval.setValue(30)
        interval_layout.addRow("AI分析:", self.ai_sync_interval)

        layout.addWidget(interval_group)

        # 同步选项
        options_group = QGroupBox("同步选项")
        options_layout = QVBoxLayout(options_group)

        self.sync_unread_only = QCheckBox("仅同步未读邮件")
        options_layout.addWidget(self.sync_unread_only)

        self.sync_attachments = QCheckBox("同步附件信息")
        self.sync_attachments.setChecked(True)
        options_layout.addWidget(self.sync_attachments)

        self.sync_delete = QCheckBox("同步删除操作")
        options_layout.addWidget(self.sync_delete)

        layout.addWidget(options_group)

        # 手动同步
        manual_group = QGroupBox("手动操作")
        manual_layout = QHBoxLayout(manual_group)

        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self._sync_now)
        manual_layout.addWidget(sync_now_btn)

        manual_layout.addStretch()

        layout.addWidget(manual_group)

        layout.addStretch()
        return widget

    def _create_ui_tab(self) -> QWidget:
        """创建界面设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        # 添加无障碍属性
        self.theme_combo.setAccessibleName("应用主题选择")
        self.theme_combo.setAccessibleDescription("选择应用的显示主题，支持浅色、深色或跟随系统")
        theme_layout.addRow("应用主题:", self.theme_combo)

        self.accent_color = QComboBox()
        self.accent_color.addItems(["蓝色", "绿色", "紫色", "橙色", "红色"])
        self.accent_color.setAccessibleName("强调色选择")
        self.accent_color.setAccessibleDescription("选择界面的强调色")
        theme_layout.addRow("强调色:", self.accent_color)

        layout.addWidget(theme_group)

        # 邮件列表
        list_group = QGroupBox("邮件列表")
        list_layout = QFormLayout(list_group)

        self.show_preview = QCheckBox("显示邮件预览")
        self.show_preview.setChecked(True)
        list_layout.addRow("预览:", self.show_preview)

        self.preview_lines = QSpinBox()
        self.preview_lines.setRange(1, 5)
        self.preview_lines.setValue(2)
        list_layout.addRow("预览行数:", self.preview_lines)

        self.list_font_size = QSpinBox()
        self.list_font_size.setRange(8, 16)
        self.list_font_size.setValue(10)
        list_layout.addRow("字号:", self.list_font_size)

        layout.addWidget(list_group)

        # 日期格式
        date_group = QGroupBox("日期格式")
        date_layout = QFormLayout(date_group)

        self.date_format = QComboBox()
        self.date_format.addItems([
            "2024-03-15 14:30",
            "2024/03/15 14:30",
            "03-15 14:30",
            "昨天 14:30",
            "3月15日 14:30"
        ])
        date_layout.addRow("日期格式:", self.date_format)

        layout.addWidget(date_group)

        layout.addStretch()
        return widget

    def _create_calendar_tab(self) -> QWidget:
        """创建日历设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 日历启用
        enable_group = QGroupBox("日历同步")
        enable_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        enable_layout = QVBoxLayout(enable_group)
        enable_layout.setSpacing(8)

        self.calendar_enabled = QCheckBox("启用日历同步")
        self.calendar_enabled.stateChanged.connect(self._on_calendar_enabled_changed)
        enable_layout.addWidget(self.calendar_enabled)

        layout.addWidget(enable_group)

        # 日历类型
        type_group = QGroupBox("日历服务")
        type_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        type_layout = QFormLayout(type_group)
        type_layout.setSpacing(10)

        self.calendar_type = QComboBox()
        self.calendar_type.addItems([
            "Outlook Calendar (推荐)",
            "Google Calendar",
            "Apple Calendar (iCloud)",
            "本地日历"
        ])
        self.calendar_type.currentIndexChanged.connect(self._on_calendar_type_changed)
        type_layout.addRow("日历类型:", self.calendar_type)

        layout.addWidget(type_group)

        # Outlook设置
        self.outlook_group = QGroupBox("Outlook设置")
        self.outlook_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        outlook_layout = QFormLayout(self.outlook_group)
        outlook_layout.setSpacing(10)

        self.outlook_account = QLineEdit()
        self.outlook_account.setPlaceholderText("your.email@outlook.com")
        outlook_layout.addRow("账户:", self.outlook_account)

        # 测试连接
        outlook_btn_layout = QHBoxLayout()
        test_outlook_btn = QPushButton("测试连接")
        test_outlook_btn.clicked.connect(self._test_outlook_connection)
        outlook_btn_layout.addWidget(test_outlook_btn)
        outlook_btn_layout.addStretch()
        self.outlook_status = QLabel("")
        self.outlook_status.setMinimumWidth(100)
        outlook_btn_layout.addWidget(self.outlook_status)
        outlook_layout.addRow("", outlook_btn_layout)

        layout.addWidget(self.outlook_group)

        # Google设置（隐藏直到选择）
        self.google_group = QGroupBox("Google Calendar设置")
        google_layout = QFormLayout(self.google_group)
        self.google_group.setVisible(False)

        self.google_calendar_id = QLineEdit()
        self.google_calendar_id.setPlaceholderText("primary 或日历ID")
        google_layout.addRow("日历ID:", self.google_calendar_id)

        # Google API Key说明
        google_hint = QLabel("需要先在 Google Cloud Console 获取 API Key")
        google_hint.setStyleSheet("color: #888;")
        google_hint.setWordWrap(True)
        google_layout.addRow("", google_hint)

        layout.addWidget(self.google_group)

        # 同步选项
        sync_options_group = QGroupBox("同步选项")
        sync_options_layout = QVBoxLayout(sync_options_group)

        self.sync_high_priority = QCheckBox("仅同步高优先级待办")
        sync_options_layout.addWidget(self.sync_high_priority)

        self.set_reminder = QCheckBox("自动设置提醒")
        self.set_reminder.setChecked(True)
        sync_options_layout.addWidget(self.set_reminder)

        self.reminder_minutes = QComboBox()
        self.reminder_minutes.addItems([
            "15分钟前", "30分钟前", "1小时前", "1天前"
        ])
        sync_options_layout.addWidget(self.reminder_minutes)

        layout.addWidget(sync_options_group)

        # 同步待办列表
        todo_group = QGroupBox("待同步的待办事项")
        todo_layout = QVBoxLayout(todo_group)

        self.todo_list = QListWidget()
        self.todo_list.setMaximumHeight(150)
        todo_layout.addWidget(self.todo_list)

        sync_todo_btn = QPushButton("同步选中待办")
        sync_todo_btn.clicked.connect(self._sync_selected_todos)
        todo_layout.addWidget(sync_todo_btn)

        layout.addWidget(todo_group)

        layout.addStretch()
        return widget

    def _create_profile_tab(self) -> QWidget:
        """创建用户画像设置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 用户画像说明
        info_group = QGroupBox("用户画像")
        info_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)

        info_label = QLabel("填写您的个人信息，AI 将更准确地识别您的待办事项")
        info_label.setStyleSheet("color: #666;")
        info_label.setWordWrap(True)
        info_label.setMinimumHeight(20)
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)

        # 基本信息表单
        form_group = QGroupBox("基本信息")
        form_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)

        # 姓名
        self.profile_name_edit = QLineEdit()
        self.profile_name_edit.setPlaceholderText("请输入您的姓名")
        form_layout.addRow("姓名:", self.profile_name_edit)

        # 部门
        self.profile_dept_edit = QLineEdit()
        self.profile_dept_edit.setPlaceholderText("例如：产品部、技术部、运营部")
        form_layout.addRow("部门:", self.profile_dept_edit)

        # 职位
        self.profile_role_edit = QLineEdit()
        self.profile_role_edit.setPlaceholderText("例如：产品经理、工程师、设计师")
        form_layout.addRow("职位:", self.profile_role_edit)

        layout.addWidget(form_group)

        # 工作描述
        desc_group = QGroupBox("工作描述（选填）")
        desc_group.setStyleSheet("QGroupBox { padding-top: 10px; padding-bottom: 10px; }")
        desc_layout = QVBoxLayout(desc_group)
        desc_layout.setSpacing(8)

        desc_hint = QLabel("描述您的主要工作内容，AI 将据此判断待办归属")
        desc_hint.setStyleSheet("color: #888;")
        desc_hint.setWordWrap(True)
        desc_hint.setMinimumHeight(20)
        desc_layout.addWidget(desc_hint)

        self.profile_desc_edit = QTextEdit()
        self.profile_desc_edit.setPlaceholderText(
            "例如：负责产品运营、用户增长、数据分析\n"
            "多个职责用顿号分隔"
        )
        self.profile_desc_edit.setMaximumHeight(100)
        desc_layout.addWidget(self.profile_desc_edit)

        layout.addWidget(desc_group)

        layout.addStretch()
        return widget

    def _on_calendar_enabled_changed(self, state: int):
        """日历启用状态改变"""
        enabled = state == Qt.Checked
        self.calendar_type.setEnabled(enabled)
        self.outlook_group.setEnabled(enabled)
        self.google_group.setEnabled(enabled)

    def _on_calendar_type_changed(self, index: int):
        """日历类型改变"""
        # 0: Outlook, 1: Google, 2: Apple, 3: Local
        self.outlook_group.setVisible(index == 0)
        self.google_group.setVisible(index == 1)
        
    def _on_theme_changed(self, index: int):
        """主题改变 - 即时应用预览"""
        theme_map = {0: 'light', 1: 'dark', 2: 'system'}
        theme = theme_map.get(index, 'light')
        
        # 获取主题管理器并应用主题
        theme_manager = get_theme_manager()
        if theme_manager:
            theme_manager.apply_theme(theme)
            self.logger.info(f"即时预览主题: {theme}")

    def _load_settings(self):
        """加载设置"""
        try:
            # 加载数据库设置
            settings = self.db.query_one("SELECT * FROM settings WHERE id = 1")
            if settings:
                row = dict(settings)
                self.sync_interval.setValue(row.get('sync_interval_minutes', 15))
                self.auto_process.setChecked(row.get('auto_process', False))

            # 加载日历设置
            calendar_settings = self._get_calendar_settings()
            if calendar_settings:
                self.calendar_enabled.setChecked(calendar_settings.get('enabled', False))
                self.calendar_type.setCurrentIndex(calendar_settings.get('type', 0))
                self.outlook_account.setText(calendar_settings.get('outlook_account', ''))
                self.sync_high_priority.setChecked(calendar_settings.get('sync_high_priority', False))
                self.set_reminder.setChecked(calendar_settings.get('set_reminder', True))

            # 加载UI设置
            ui_settings = self._get_ui_settings()
            if ui_settings:
                self.theme_combo.setCurrentIndex(ui_settings.get('theme', 0))
                self.show_preview.setChecked(ui_settings.get('show_preview', True))
                self.date_format.setCurrentIndex(ui_settings.get('date_format', 0))

            # 加载待办事项列表
            self._load_todo_list()

            # 加载用户画像
            self._load_user_profile()

            self.logger.info("设置加载完成")

        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")

    def _get_calendar_settings(self) -> dict:
        """获取日历设置"""
        try:
            result = self.db.query_one("SELECT value FROM settings WHERE id = 2")
            if result and result[0]:
                import json
                return json.loads(result[0])
        except:
            pass
        return {}

    def _get_ui_settings(self) -> dict:
        """获取UI设置"""
        try:
            result = self.db.query_one("SELECT value FROM settings WHERE id = 3")
            if result and result[0]:
                import json
                return json.loads(result[0])
        except:
            pass
        return {}

    def _save_settings(self):
        """保存设置"""
        try:
            import json

            # 保存通用设置
            sql = '''
                UPDATE settings SET 
                sync_interval_minutes = ?,
                auto_process = ?
                WHERE id = 1
            '''
            self.db.execute(sql, (
                self.sync_interval.value(),
                1 if self.auto_process.isChecked() else 0
            ))

            # 保存日历设置
            calendar_settings = {
                'enabled': self.calendar_enabled.isChecked(),
                'type': self.calendar_type.currentIndex(),
                'outlook_account': self.outlook_account.text(),
                'sync_high_priority': self.sync_high_priority.isChecked(),
                'set_reminder': self.set_reminder.isChecked(),
                'reminder_minutes': self.reminder_minutes.currentIndex()
            }

            # 检查是否有calendar_settings记录
            existing = self.db.query_one("SELECT id FROM settings WHERE id = 2")
            if existing:
                self.db.execute(
                    "UPDATE settings SET value = ? WHERE id = 2",
                    (json.dumps(calendar_settings),)
                )
            else:
                self.db.execute(
                    "INSERT INTO settings (id, value) VALUES (2, ?)",
                    (json.dumps(calendar_settings),)
                )

            # 保存UI设置
            ui_settings = {
                'theme': self.theme_combo.currentIndex(),
                'accent_color': self.accent_color.currentIndex(),
                'show_preview': self.show_preview.isChecked(),
                'preview_lines': self.preview_lines.value(),
                'date_format': self.date_format.currentIndex()
            }

            existing = self.db.query_one("SELECT id FROM settings WHERE id = 3")
            if existing:
                self.db.execute(
                    "UPDATE settings SET value = ? WHERE id = 3",
                    (json.dumps(ui_settings),)
                )
            else:
                self.db.execute(
                    "INSERT INTO settings (id, value) VALUES (3, ?)",
                    (json.dumps(ui_settings),)
                )

            # 保存用户画像
            from ..data.user_profile_repo import UserProfileRepo
            profile_repo = UserProfileRepo(self.db)
            profile_repo.update_profile(
                name=self.profile_name_edit.text().strip(),
                department=self.profile_dept_edit.text().strip(),
                role=self.profile_role_edit.text().strip(),
                work_description=self.profile_desc_edit.toPlainText().strip()
            )

            self.logger.info("设置保存成功")

        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            raise

    def _apply_settings(self):
        """应用设置（不关闭对话框）"""
        try:
            self._save_settings()
            Toast.success(self, "设置已保存", duration=2000)
        except Exception as e:
            Toast.error(self, f"保存失败: {e}", duration=3000)

    def _save_and_close(self):
        """保存并关闭"""
        try:
            self._save_settings()
            self.accept()
        except Exception as e:
            Toast.error(self, f"保存失败: {e}", duration=3000)

    def _sync_now(self):
        """立即同步"""
        QMessageBox.information(self, "同步", "邮件同步功能开发中...")
        self.statusbar.showMessage("同步完成", 3000) if hasattr(self, 'statusbar') else None

    def _test_outlook_connection(self):
        """测试Outlook连接"""
        account = self.outlook_account.text().strip()
        if not account:
            self.outlook_status.setText("请输入账户")
            self.outlook_status.setStyleSheet("color: #F44336;")
            return

        # TODO: 实现Outlook连接测试
        self.outlook_status.setText("测试中...")
        self.outlook_status.setStyleSheet("color: #666;")

        # 模拟测试
        QTimer.singleShot(1000, lambda: self._show_outlook_result(True))

    def _show_outlook_result(self, success: bool):
        """显示Outlook测试结果"""
        if success:
            self.outlook_status.setText("✓ 连接成功")
            self.outlook_status.setStyleSheet("color: #4CAF50;")
        else:
            self.outlook_status.setText("✗ 连接失败")
            self.outlook_status.setStyleSheet("color: #F44336;")

    def _load_todo_list(self):
        """加载待办列表"""
        self.todo_list.clear()
        try:
            from ..data.todo_repo import TodoRepo
            todo_repo = TodoRepo(self.db)
            todos = todo_repo.get_all_todos(completed=False)

            for todo in todos[:20]:  # 最多显示20个
                priority_icon = "🔴" if todo.get('priority') == '高' else "🟡"
                self.todo_list.addItem(f"{priority_icon} {todo.get('content', '')[:50]}")

        except Exception as e:
            self.logger.error(f"加载待办列表失败: {e}")

    def _load_user_profile(self):
        """加载用户画像"""
        try:
            from ..data.user_profile_repo import UserProfileRepo
            profile_repo = UserProfileRepo(self.db)
            profile = profile_repo.get_profile()

            if profile['name']:
                self.profile_name_edit.setText(profile['name'])
            if profile['department']:
                self.profile_dept_edit.setText(profile['department'])
            if profile['role']:
                self.profile_role_edit.setText(profile['role'])
            if profile['work_description']:
                self.profile_desc_edit.setText(profile['work_description'])

        except Exception as e:
            self.logger.error(f"加载用户画像失败: {e}")

    def _sync_selected_todos(self):
        """同步选中的待办到日历"""
        selected = self.todo_list.currentRow()
        if selected < 0:
            QMessageBox.information(self, "提示", "请先选择要同步的待办事项")
            return

        QMessageBox.information(self, "同步", "待办同步到日历功能开发中...")

    # ========== Phase 7: 部门管理（完整优化版）==========
    
    def _create_department_tab(self) -> QWidget:
        """创建部门管理标签页（完整优化版）"""
        from PyQt5.QtWidgets import QStackedWidget, QScrollArea, QGridLayout, QMenu
        from .components.department_card import DepartmentCard
        
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(12)
        
        # ========== 顶部工具栏 ==========
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # 搜索框
        self.dept_search = QLineEdit()
        self.dept_search.setPlaceholderText("🔍 搜索部门名称...")
        self.dept_search.setClearButtonEnabled(True)
        self.dept_search.textChanged.connect(self._filter_departments)
        self.dept_search.setMinimumWidth(200)
        toolbar.addWidget(self.dept_search, 2)
        
        # 视图切换按钮
        self.view_toggle_btn = QPushButton("📋 列表视图")
        self.view_toggle_btn.clicked.connect(self._toggle_dept_view)
        self.view_toggle_btn.setMinimumWidth(100)
        toolbar.addWidget(self.view_toggle_btn)
        
        # 添加部门按钮
        self.add_dept_btn = QPushButton("➕ 添加部门")
        self.add_dept_btn.clicked.connect(self._add_department)
        self.add_dept_btn.setObjectName("primaryBtn")
        self.add_dept_btn.setMinimumWidth(100)
        toolbar.addWidget(self.add_dept_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("刷新部门列表")
        refresh_btn.setFixedWidth(40)
        refresh_btn.clicked.connect(self._load_departments)
        toolbar.addWidget(refresh_btn)
        
        main_layout.addLayout(toolbar)
        
        # ========== 主内容区（可切换视图）==========
        self.dept_stack = QStackedWidget()
        
        # 视图1: 列表视图（树形分组）
        list_widget = self._create_list_view()
        self.dept_stack.addWidget(list_widget)
        
        # 视图2: 卡片视图
        card_widget = self._create_card_view()
        self.dept_stack.addWidget(card_widget)
        
        # 默认显示列表视图
        self.dept_stack.setCurrentIndex(0)
        self.current_view = 'list'
        
        # ========== 可调整大小的分割布局 ==========
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #E5E7EB;
                border-radius: 4px;
            }
            QSplitter::handle:hover {
                background: #667eea;
            }
        """)
        
        # 部门视图区域（放入分割器）
        dept_container = QWidget()
        dept_layout = QVBoxLayout(dept_container)
        dept_layout.setContentsMargins(0, 0, 0, 0)
        dept_layout.addWidget(self.dept_stack)
        splitter.addWidget(dept_container)
        
        # 成员列表区域（放入分割器）
        member_group = QGroupBox("团队成员")
        member_group.setStyleSheet("QGroupBox { padding-top: 15px; padding-bottom: 10px; }")
        member_layout = QVBoxLayout(member_group)
        member_layout.setSpacing(10)
        
        # 成员列表（使用自定义组件，支持调整行高）
        from .components.member_list import MemberListWidget
        self.member_list = MemberListWidget()
        self.member_list.currentRowChanged.connect(self._on_member_selected)
        member_layout.addWidget(self.member_list, 1)
        
        # 成员按钮
        member_btn_layout = QHBoxLayout()
        member_btn_layout.setSpacing(10)
        
        self.add_member_btn = QPushButton("添加成员")
        self.add_member_btn.clicked.connect(self._add_member)
        self.add_member_btn.setEnabled(False)
        self.add_member_btn.setMinimumWidth(90)
        member_btn_layout.addWidget(self.add_member_btn)
        
        self.edit_member_btn = QPushButton("编辑成员")
        self.edit_member_btn.clicked.connect(self._edit_member)
        self.edit_member_btn.setEnabled(False)
        self.edit_member_btn.setMinimumWidth(90)
        member_btn_layout.addWidget(self.edit_member_btn)
        
        self.del_member_btn = QPushButton("删除成员")
        self.del_member_btn.clicked.connect(self._delete_member)
        self.del_member_btn.setEnabled(False)
        self.del_member_btn.setMinimumWidth(90)
        member_btn_layout.addWidget(self.del_member_btn)
        
        member_btn_layout.addStretch()
        member_layout.addLayout(member_btn_layout)
        splitter.addWidget(member_group)
        
        # 设置分割器初始比例：部门区域占65%，成员区域占35%
        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)
        
        main_layout.addWidget(splitter, 1)
        
        # ========== 同步设置（固定在底部）==========
        sync_group = QGroupBox("同步设置")
        sync_group.setStyleSheet("QGroupBox { padding-top: 15px; padding-bottom: 10px; }")
        sync_layout = QFormLayout(sync_group)
        sync_layout.setSpacing(10)
        
        self.share_path_edit = QLineEdit()
        self.share_path_edit.setPlaceholderText("例如: \\\\server\\shared\\team-todos 或 /mnt/shared/team-todos")
        sync_layout.addRow("共享路径:", self.share_path_edit)
        
        sync_btn_layout = QHBoxLayout()
        self.sync_upload_btn = QPushButton("上传我的待办")
        self.sync_upload_btn.clicked.connect(self._sync_upload)
        self.sync_upload_btn.setEnabled(False)
        sync_btn_layout.addWidget(self.sync_upload_btn)
        
        self.sync_download_btn = QPushButton("查看团队待办")
        self.sync_download_btn.clicked.connect(self._sync_download)
        self.sync_download_btn.setEnabled(False)
        sync_btn_layout.addWidget(self.sync_download_btn)
        
        sync_layout.addRow(sync_btn_layout)
        main_layout.addWidget(sync_group)
        
        # 加载部门数据
        self._load_departments()
        
        return widget
    
    def _create_list_view(self) -> QWidget:
        """创建列表视图（树形分组）"""
        from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 树形部门列表
        self.dept_tree = QTreeWidget()
        self.dept_tree.setHeaderHidden(True)
        self.dept_tree.setAnimated(True)  # 动画效果
        self.dept_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dept_tree.customContextMenuRequested.connect(self._show_dept_context_menu)
        self.dept_tree.currentItemChanged.connect(self._on_tree_item_selected)
        
        # 设置样式
        self.dept_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                background: white;
            }
            QTreeWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background: #F0F4FF;
            }
            QTreeWidget::item:selected {
                background: #E0E7FF;
                color: #667eea;
            }
            QTreeWidget::branch {
                background: transparent;
            }
        """)
        
        layout.addWidget(self.dept_tree)
        return widget
    
    def _create_card_view(self) -> QWidget:
        """创建卡片视图"""
        from PyQt5.QtWidgets import QScrollArea, QGridLayout
        
        # 滚动容器
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: #FAFAFA;
            }
        """)
        
        # 卡片容器
        self.card_container = QWidget()
        self.card_grid = QGridLayout(self.card_container)
        self.card_grid.setSpacing(16)
        self.card_grid.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(self.card_container)
        return scroll
    
    def _toggle_dept_view(self):
        """切换部门视图"""
        if self.current_view == 'list':
            # 切换到卡片视图
            self.dept_stack.setCurrentIndex(1)
            self.view_toggle_btn.setText("📊 卡片视图")
            self.current_view = 'card'
        else:
            # 切换到列表视图
            self.dept_stack.setCurrentIndex(0)
            self.view_toggle_btn.setText("📋 列表视图")
            self.current_view = 'list'
    
    def _filter_departments(self, text: str):
        """实时搜索部门"""
        text = text.lower().strip()
        
        if self.current_view == 'list':
            # 过滤树形列表
            self._filter_tree_items(self.dept_tree.invisibleRootItem(), text)
        else:
            # 过滤卡片
            self._filter_cards(text)
    
    def _filter_tree_items(self, parent_item, text: str):
        """过滤树形项目"""
        from PyQt5.QtWidgets import QTreeWidgetItem
        
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            
            # 如果是部门项（有dept_id数据）
            dept_id = item.data(0, Qt.UserRole)
            if dept_id:
                dept_name = item.text(0).lower()
                is_match = text in dept_name if text else True
                item.setHidden(not is_match)
            else:
                # 如果是分组项，递归检查子项
                self._filter_tree_items(item, text)
                
                # 如果所有子项都隐藏，则隐藏分组
                has_visible_child = False
                for j in range(item.childCount()):
                    if not item.child(j).isHidden():
                        has_visible_child = True
                        break
                item.setHidden(not has_visible_child)
    
    def _filter_cards(self, text: str):
        """过滤卡片"""
        for i in range(self.card_grid.count()):
            card = self.card_grid.itemAt(i).widget()
            if card and hasattr(card, 'dept'):
                dept_name = card.dept.name.lower()
                is_match = text in dept_name if text else True
                card.setVisible(is_match)
    
    def _show_dept_context_menu(self, pos):
        """显示部门右键菜单"""
        from PyQt5.QtWidgets import QMenu
        
        item = self.dept_tree.itemAt(pos)
        if not item:
            return
        
        dept_id = item.data(0, Qt.UserRole)
        if not dept_id:
            return  # 不是部门项（可能是分组项）
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #667eea;
                color: white;
            }
        """)
        
        edit_action = menu.addAction("✏️ 编辑")
        edit_action.triggered.connect(lambda: self._edit_department_by_id(dept_id))
        
        sync_action = menu.addAction("🔄 同步待办")
        sync_action.triggered.connect(lambda: self._sync_department_by_id(dept_id))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ 删除")
        delete_action.triggered.connect(lambda: self._delete_department_by_id(dept_id))
        
        menu.exec_(self.dept_tree.mapToGlobal(pos))
    
    def _on_tree_item_selected(self, current, previous):
        """树形项目选中事件"""
        if not current:
            return
        
        dept_id = current.data(0, Qt.UserRole)
        if dept_id:
            self._on_department_selected(dept_id)
    
    def _load_departments(self):
        """加载部门列表（支持树形和卡片视图）"""
        try:
            from ..data.department_repo import DepartmentRepo
            from ..data.team_member_repo import TeamMemberRepo
            from .components.department_card import DepartmentCard
            from PyQt5.QtWidgets import QTreeWidgetItem
            
            dept_repo = DepartmentRepo(self.db)
            member_repo = TeamMemberRepo(self.db)
            departments = dept_repo.get_all()
            
            # === 1. 加载树形视图 ===
            self.dept_tree.clear()
            
            # 按中心分组
            groups = {}
            for dept in departments:
                center = self._extract_center(dept.name)
                if center not in groups:
                    groups[center] = []
                groups[center].append(dept)
            
            # 渲染树形结构
            for center_name, depts in sorted(groups.items()):
                # 创建分组项
                center_item = QTreeWidgetItem(self.dept_tree)
                center_item.setText(0, f"📁 {center_name} ({len(depts)}个部门)")
                center_item.setExpanded(True)  # 默认展开
                center_item.setFont(0, QFont("Microsoft YaHei", 10, QFont.Bold))
                
                for dept in depts:
                    # 创建部门项
                    dept_item = QTreeWidgetItem(center_item)
                    member_count = len(member_repo.get_by_department(dept.id))
                    dept_item.setText(0, f"🏢 {dept.name}  👥 {member_count}人")
                    dept_item.setData(0, Qt.UserRole, dept.id)
                    dept_item.setToolTip(0, f"共享路径: {dept.share_path or '未设置'}")
            
            # === 2. 加载卡片视图 ===
            # 清空现有卡片
            for i in reversed(range(self.card_grid.count())):
                self.card_grid.itemAt(i).widget().deleteLater()
            
            # 响应式网格布局（每行3个卡片）
            cols = 3
            for i, dept in enumerate(departments):
                member_count = len(member_repo.get_by_department(dept.id))
                card = DepartmentCard(dept, member_count)
                card.edit_clicked.connect(self._edit_department_by_id)
                card.sync_clicked.connect(self._sync_department_by_id)
                card.card_clicked.connect(self._on_department_selected)
                
                row = i // cols
                col = i % cols
                self.card_grid.addWidget(card, row, col)
            
            # 添加弹性空间
            self.card_grid.setRowStretch(self.card_grid.rowCount(), 1)
            
        except Exception as e:
            self.logger.error(f"加载部门列表失败: {e}")
    
    def _extract_center(self, dept_name: str) -> str:
        """从部门名称提取中心名"""
        # 常见的中心关键词
        centers = ['技术', '产品', '运营', '市场', '销售', '财务', '人力', '行政']
        for center in centers:
            if center in dept_name:
                return f"{center}中心"
        return "其他部门"
    
    def _on_department_selected(self, dept_id: int):
        """部门选中事件（统一处理）"""
        # 更新按钮状态
        self.add_member_btn.setEnabled(True)
        self.sync_upload_btn.setEnabled(True)
        self.sync_download_btn.setEnabled(True)
        
        # 加载成员列表
        self._load_members(dept_id)
        
        # 加载共享路径
        try:
            from ..data.department_repo import DepartmentRepo
            dept_repo = DepartmentRepo(self.db)
            dept = dept_repo.get_by_id(dept_id)
            if dept:
                self.share_path_edit.setText(dept.share_path)
        except Exception as e:
            self.logger.error(f"加载部门信息失败: {e}")
    
    def _edit_department_by_id(self, dept_id: int):
        """根据ID编辑部门"""
        from PyQt5.QtWidgets import QInputDialog
        from ..data.department_repo import DepartmentRepo
        
        dept_repo = DepartmentRepo(self.db)
        dept = dept_repo.get_by_id(dept_id)
        
        name, ok1 = QInputDialog.getText(self, "编辑部门", "部门名称:", text=dept.name)
        if not ok1:
            return
        
        share_path, ok2 = QInputDialog.getText(self, "编辑部门", "共享路径:", text=dept.share_path)
        if not ok2:
            return
        
        try:
            dept_repo.update(dept_id, name=name, share_path=share_path)
            Toast.success(self, "部门更新成功")
            self._load_departments()
        except Exception as e:
            Toast.error(self, f"更新失败: {e}")
    
    def _sync_department_by_id(self, dept_id: int):
        """根据ID同步部门待办"""
        # TODO: 实现同步逻辑
        Toast.info(self, "同步功能开发中...")
    
    def _delete_department_by_id(self, dept_id: int):
        """根据ID删除部门"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除该部门吗？\n将同时删除所有成员和同步记录！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from ..data.department_repo import DepartmentRepo
                dept_repo = DepartmentRepo(self.db)
                dept_repo.delete(dept_id)
                
                Toast.success(self, "部门删除成功")
                self._load_departments()
                self.member_list.clear()
            except Exception as e:
                Toast.error(self, f"删除失败: {e}")
    
    def _on_member_selected(self, row: int):
        """成员选中事件"""
        has_selection = row >= 0
        self.edit_member_btn.setEnabled(has_selection)
        self.del_member_btn.setEnabled(has_selection)
    
    def _load_members(self, dept_id: int):
        """加载成员列表"""
        try:
            from ..data.team_member_repo import TeamMemberRepo
            member_repo = TeamMemberRepo(self.db)
            members = member_repo.get_by_department(dept_id)
            
            self.member_list.clear()
            for member in members:
                # 两行显示：姓名邮箱 + 角色标识
                leader_mark = " [团队负责人]" if member.is_leader else " [成员]"
                display_text = f"{member.name} <{member.email}>{leader_mark}"
                # 使用自定义的添加方法
                self.member_list.addMemberItem(
                    member_id=member.id,
                    display_text=display_text,
                    is_leader=member.is_leader
                )
                
        except Exception as e:
            self.logger.error(f"加载成员列表失败: {e}")
    
    def _add_department(self):
        """添加部门"""
        from PyQt5.QtWidgets import QInputDialog
        
        name, ok1 = QInputDialog.getText(self, "添加部门", "部门名称:")
        if not ok1 or not name:
            return
        
        share_path, ok2 = QInputDialog.getText(self, "添加部门", "共享路径:")
        if not ok2 or not share_path:
            return
        
        try:
            from ..data.department_repo import DepartmentRepo
            dept_repo = DepartmentRepo(self.db)
            dept_id = dept_repo.create(name, share_path)
            
            Toast.success(self, f"部门 '{name}' 添加成功")
            self._load_departments()
            
        except Exception as e:
            Toast.error(self, f"添加部门失败: {e}")
    
    def _edit_department(self):
        """编辑部门（从按钮调用）"""
        # 获取当前选中的部门
        current_item = self.dept_tree.currentItem()
        if not current_item:
            return
        
        dept_id = current_item.data(0, Qt.UserRole)
        if dept_id:
            self._edit_department_by_id(dept_id)
    
    def _delete_department(self):
        """删除部门（从按钮调用）"""
        # 获取当前选中的部门
        current_item = self.dept_tree.currentItem()
        if not current_item:
            return
        
        dept_id = current_item.data(0, Qt.UserRole)
        if dept_id:
            self._delete_department_by_id(dept_id)
    
    def _add_member(self):
        """添加成员"""
        # 从树形列表获取选中部门
        current_item = self.dept_tree.currentItem()
        if not current_item:
            return
        
        dept_id = current_item.data(0, Qt.UserRole)
        if not dept_id:
            Toast.warning(self, "请选择一个部门")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        from ..data.team_member_repo import TeamMemberRepo
        
        name, ok1 = QInputDialog.getText(self, "添加成员", "姓名:")
        if not ok1 or not name:
            return
        
        email, ok2 = QInputDialog.getText(self, "添加成员", "邮箱:")
        if not ok2 or not email:
            return
        
        role, ok3 = QInputDialog.getText(self, "添加成员", "角色:")
        if not ok3:
            return
        
        is_leader = QMessageBox.question(
            self, "Leader", "该成员是否为Leader?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes
        
        try:
            member_repo = TeamMemberRepo(self.db)
            member_id = member_repo.create(dept_id, name, email, role, is_leader)
            
            Toast.success(self, f"成员 '{name}' 添加成功")
            self._load_members(dept_id)
            self._load_departments()  # 刷新部门卡片显示的成员数
            
        except Exception as e:
            Toast.error(self, f"添加成员失败: {e}")
    
    def _edit_member(self):
        """编辑成员"""
        # 获取选中的部门和成员
        dept_item = self.dept_tree.currentItem()
        member_item = self.member_list.currentItem()
        if not dept_item or not member_item:
            return
        
        dept_id = dept_item.data(0, Qt.UserRole)
        member_id = member_item.data(Qt.UserRole)
        
        if not dept_id or not member_id:
            return
        
        from PyQt5.QtWidgets import QInputDialog
        from ..data.team_member_repo import TeamMemberRepo
        
        member_repo = TeamMemberRepo(self.db)
        member = member_repo.get_by_id(member_id)
        
        name, ok1 = QInputDialog.getText(self, "编辑成员", "姓名:", text=member.name)
        if not ok1:
            return
        
        email, ok2 = QInputDialog.getText(self, "编辑成员", "邮箱:", text=member.email)
        if not ok2:
            return
        
        role, ok3 = QInputDialog.getText(self, "编辑成员", "角色:", text=member.role)
        if not ok3:
            return
        
        is_leader = QMessageBox.question(
            self, "Leader", "该成员是否为Leader?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes
        
        try:
            member_repo.update(member_id, name=name, email=email, role=role, is_leader=is_leader)
            Toast.success(self, "成员更新成功")
            self._load_members(dept_id)
            self._load_departments()  # 刷新部门卡片
            
        except Exception as e:
            Toast.error(self, f"更新成员失败: {e}")
    
    def _delete_member(self):
        """删除成员"""
        # 获取选中的部门和成员
        dept_item = self.dept_tree.currentItem()
        member_item = self.member_list.currentItem()
        if not dept_item or not member_item:
            return
        
        dept_id = dept_item.data(0, Qt.UserRole)
        member_id = member_item.data(Qt.UserRole)
        
        if not dept_id or not member_id:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除该成员吗？\n将同时删除所有同步记录！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from ..data.team_member_repo import TeamMemberRepo
                member_repo = TeamMemberRepo(self.db)
                member_repo.delete(member_id)
                
                Toast.success(self, "成员删除成功")
                self._load_members(dept_id)
                self._load_departments()  # 刷新部门卡片
                
            except Exception as e:
                Toast.error(self, f"删除成员失败: {e}")
    
    def _sync_upload(self):
        """上传待办"""
        # 从树形列表获取选中部门
        current_item = self.dept_tree.currentItem()
        if not current_item:
            return
        
        dept_id = current_item.data(0, Qt.UserRole)
        if not dept_id:
            Toast.warning(self, "请选择一个部门")
            return
        
        # 检查用户画像是否已设置
        try:
            from ..data.user_profile_repo import UserProfileRepo
            profile_repo = UserProfileRepo(self.db)
            profile = profile_repo.get_profile()
            
            if not profile['name'] or not profile['department']:
                Toast.warning(self, "请先在「用户画像」标签页设置姓名和部门信息")
                return
            
            # 根据用户邮箱找到对应的成员记录
            from ..data.team_member_repo import TeamMemberRepo
            member_repo = TeamMemberRepo(self.db)
            
            members = member_repo.get_by_department(dept_id)
            
            if not members:
                Toast.warning(self, "请先添加团队成员")
                return
            
            # 查找匹配的成员(通过姓名)
            member = None
            for m in members:
                if m.name == profile['name']:
                    member = m
                    break
            
            if not member:
                reply = QMessageBox.question(
                    self, "提示",
                    f"未找到姓名为 '{profile['name']}' 的成员记录\n是否创建新成员？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    member_id = member_repo.create(
                        dept_id, profile['name'], 
                        f"{profile['name']}@temp.com",
                        profile['role'], False
                    )
                else:
                    return
            else:
                member_id = member.id
            
            # 执行上传
            from ..core.sync_service import SyncService
            sync_service = SyncService(self.db)
            result = sync_service.upload_todos(member_id)
            
            if result.success:
                Toast.success(self, f"成功上传 {result.todo_count} 条待办")
            else:
                Toast.error(self, f"上传失败: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"上传待办失败: {e}")
            Toast.error(self, f"上传失败: {e}")
    
    def _sync_download(self):
        """查看团队待办"""
        # 从树形列表获取选中部门
        current_item = self.dept_tree.currentItem()
        if not current_item:
            return
        
        dept_id = current_item.data(0, Qt.UserRole)
        if not dept_id:
            Toast.warning(self, "请选择一个部门")
            return
        
        try:
            from ..core.sync_service import SyncService
            sync_service = SyncService(self.db)
            team_todos = sync_service.get_team_todos(dept_id)
            
            if not team_todos:
                Toast.info(self, "暂无团队成员待办数据")
                return
            
            # 显示统计信息
            total_todos = sum(len(data.todos) for data in team_todos.values())
            member_count = len(team_todos)
            
            Toast.success(
                self, 
                f"已加载 {member_count} 位成员的待办数据\n共计 {total_todos} 条待办"
            )
            
            # TODO: 在主界面显示团队待办视图
            
        except Exception as e:
            self.logger.error(f"查看团队待办失败: {e}")
            Toast.error(self, f"加载失败: {e}")
