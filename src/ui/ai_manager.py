# -*- coding: utf-8 -*-
"""
AI服务管理器组件
提供AI状态指示、配置界面和使用统计
"""

import logging
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QLineEdit,
    QTextEdit, QGroupBox, QFormLayout, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ..core.ai_bridge import AIBridge, AIProvider


class AIStatusIndicator(QWidget):
    """AI状态指示器组件"""

    # 状态信号
    status_changed = pyqtSignal(str, bool)  # provider, is_available

    def __init__(self, ai_bridge: AIBridge, parent=None):
        super().__init__(parent)
        self.ai_bridge = ai_bridge
        self.logger = logging.getLogger(__name__)

        self._init_ui()
        self._start_status_check()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)

        # 状态图标
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Segoe UI Emoji", 10))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # 提供商名称
        self.provider_label = QLabel("AI: 检测中...")
        self.provider_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.provider_label)

        layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setToolTip("刷新状态")
        refresh_btn.clicked.connect(self._check_status)
        layout.addWidget(refresh_btn)

        # 配置按钮
        config_btn = QPushButton("⚙")
        config_btn.setFixedSize(24, 24)
        config_btn.setToolTip("AI配置")
        config_btn.clicked.connect(self._show_config_dialog)
        layout.addWidget(config_btn)

        self._check_status()

    def _start_status_check(self):
        """启动状态检查定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_status)
        self.timer.start(30000)  # 每30秒检查一次

    def _check_status(self):
        """检查AI状态"""
        try:
            is_available = self.ai_bridge.is_available()
            provider = self.ai_bridge.get_current_provider()

            if is_available:
                if provider == "ollama":
                    self.status_label.setStyleSheet("color: #4CAF50;")
                    self.provider_label.setText("AI: Ollama (本地)")
                else:
                    self.status_label.setStyleSheet("color: #2196F3;")
                    self.provider_label.setText(f"AI: {provider}")
            else:
                self.status_label.setStyleSheet("color: #F44336;")
                self.provider_label.setText("AI: 未连接")

            self.status_changed.emit(provider, is_available)

        except Exception as e:
            self.logger.error(f"检查AI状态失败: {e}")
            self.status_label.setStyleSheet("color: #F44336;")
            self.provider_label.setText("AI: 错误")

    def _show_config_dialog(self):
        """显示配置对话框"""
        dialog = AIConfigDialog(self.ai_bridge, self)
        dialog.exec_()
        self._check_status()


class AIConfigDialog(QDialog):
    """AI配置对话框"""

    def __init__(self, ai_bridge: AIBridge, parent=None):
        super().__init__(parent)
        self.ai_bridge = ai_bridge
        self.logger = logging.getLogger(__name__)

        self._init_ui()
        self._load_current_config()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("AI服务配置")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setFont(QFont("Microsoft YaHei", 10))

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Tab页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Ollama配置页
        tabs.addTab(self._create_ollama_tab(), "Ollama (本地)")

        # 云端API配置页
        tabs.addTab(self._create_cloud_tab(), "云端API")

        # 使用统计页
        tabs.addTab(self._create_stats_tab(), "使用统计")

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._save_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_ollama_tab(self) -> QWidget:
        """创建Ollama配置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 说明
        hint = QLabel("""
        <b>Ollama</b> 允许你在本地运行开源AI模型，完全免费且保护隐私。
        <br><br>
        请先安装 Ollama: <a href="https://ollama.com">https://ollama.com</a>
        """)
        hint.setStyleSheet("color: #555; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        hint.setOpenExternalLinks(True)
        layout.addWidget(hint)

        # 连接测试
        test_group = QGroupBox("连接测试")
        test_layout = QVBoxLayout(test_group)

        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setPlaceholderText("http://localhost:11434")
        test_layout.addWidget(QLabel("服务器地址:"))
        test_layout.addWidget(self.ollama_url_input)

        test_btn_layout = QHBoxLayout()
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_ollama_connection)
        test_btn_layout.addWidget(test_btn)
        test_btn_layout.addStretch()

        self.test_result_label = QLabel("")
        test_btn_layout.addWidget(self.test_result_label)
        test_layout.addLayout(test_btn_layout)

        layout.addWidget(test_group)

        # 模型选择
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        # 初始化时不添加预设列表，而是从本地获取
        model_layout.addWidget(QLabel("选择模型:"))
        model_layout.addWidget(self.model_combo)

        refresh_models_btn = QPushButton("刷新模型列表")
        refresh_models_btn.clicked.connect(self._refresh_models)
        model_layout.addWidget(refresh_models_btn)
        
        # 初始化时自动获取一次模型列表
        QTimer.singleShot(500, self._refresh_models)

        layout.addWidget(model_group)

        layout.addStretch()
        return widget

    def _create_cloud_tab(self) -> QWidget:
        """创建云端API配置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 说明
        hint = QLabel(
            "云端API提供更强大的AI能力，但需要付费使用。\n\n"
            "• DeepSeek - 性价比高，适合中文\n"
            "• 通义千问 - 阿里云，稳定性好\n"
            "• 文心一言 - 百度，擅长中文理解"
        )
        hint.setStyleSheet("color: #555; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 选择提供商
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.cloud_provider_combo = QComboBox()
        self.cloud_provider_combo.addItems([
            "DeepSeek (推荐)",
            "通义千问 (阿里)",
            "文心一言 (百度)"
        ])
        form_layout.addRow("AI提供商:", self.cloud_provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API密钥:", self.api_key_input)

        self.cloud_model_input = QLineEdit()
        self.cloud_model_input.setPlaceholderText("留空使用默认模型")
        form_layout.addRow("模型名称:", self.cloud_model_input)

        layout.addLayout(form_layout)

        # 测试连接
        test_btn = QPushButton("验证API密钥")
        test_btn.clicked.connect(self._test_cloud_connection)
        layout.addWidget(test_btn)

        self.cloud_test_result = QLabel("")
        layout.addWidget(self.cloud_test_result)

        layout.addStretch()
        return widget

    def _create_stats_tab(self) -> QWidget:
        """创建使用统计页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 统计表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["日期", "提供商", "模型", "Token数"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.stats_table)

        # 总计
        stats = self.ai_bridge.get_usage_stats()
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel(f"总请求次数: {stats['total_requests']}"))
        total_layout.addWidget(QLabel(f"总Token数: {stats['total_tokens']}"))
        total_layout.addStretch()
        layout.addLayout(total_layout)

        return widget

    def _load_current_config(self):
        """加载当前配置"""
        # Ollama配置
        self.ollama_url_input.setText(self.ai_bridge.ollama_config.base_url)
        
        # 先刷新模型列表，再设置当前模型
        self._refresh_models()
        
        # 设置当前模型（延迟设置，确保模型列表已加载）
        QTimer.singleShot(100, lambda: self.model_combo.setCurrentText(self.ai_bridge.ollama_config.model))

    def _test_ollama_connection(self):
        """测试Ollama连接"""
        url = self.ollama_url_input.text().strip()
        if not url:
            url = "http://localhost:11434"

        try:
            import requests
            response = requests.get(f"{url}/api/tags", timeout=5)

            if response.status_code == 200:
                self.test_result_label.setText("✓ 连接成功")
                self.test_result_label.setStyleSheet("color: #4CAF50;")
            else:
                self.test_result_label.setText("✗ 连接失败")
                self.test_result_label.setStyleSheet("color: #F44336;")

        except Exception as e:
            self.test_result_label.setText(f"✗ 连接失败: {e}")
            self.test_result_label.setStyleSheet("color: #F44336;")

    def _test_cloud_connection(self):
        """测试云端API连接"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入API密钥")
            return
        
        provider_index = self.cloud_provider_combo.currentIndex()
        provider_names = ["deepseek", "qianwen", "wenxin"]
        provider = provider_names[provider_index]
        
        self.cloud_test_result.setText("验证中...")
        self.cloud_test_result.setStyleSheet("color: #666;")
        
        try:
            # 根据不同提供商验证API密钥
            if provider == "deepseek":
                success = self._test_deepseek_api(api_key)
            elif provider == "qianwen":
                success = self._test_qianwen_api(api_key)
            elif provider == "wenxin":
                success = self._test_wenxin_api(api_key)
            else:
                success = False
            
            if success:
                self.cloud_test_result.setText("✓ API密钥有效")
                self.cloud_test_result.setStyleSheet("color: #4CAF50;")
            else:
                self.cloud_test_result.setText("✗ API密钥无效")
                self.cloud_test_result.setStyleSheet("color: #F44336;")
        
        except Exception as e:
            self.cloud_test_result.setText(f"✗ 验证失败: {str(e)}")
            self.cloud_test_result.setStyleSheet("color: #F44336;")
    
    def _test_deepseek_api(self, api_key: str) -> bool:
        """测试DeepSeek API密钥"""
        import requests
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )
            return response.status_code in [200, 400]  # 400可能是token限制，但密钥有效
        except Exception as e:
            self.logger.error(f"DeepSeek API测试失败: {e}")
            return False
    
    def _test_qianwen_api(self, api_key: str) -> bool:
        """测试通义千问API密钥"""
        # 通义千问使用 DashScope API
        import requests
        try:
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-turbo",
                    "input": {"messages": [{"role": "user", "content": "test"}]}
                },
                timeout=10
            )
            return response.status_code in [200, 400]
        except Exception as e:
            self.logger.error(f"通义千问API测试失败: {e}")
            return False
    
    def _test_wenxin_api(self, api_key: str) -> bool:
        """测试文心一言API密钥"""
        # 文心一言需要API Key和Secret Key
        QMessageBox.information(
            self, 
            "提示", 
            "文心一言需要 API Key 和 Secret Key 配对使用\n"
            "请在配置文件中同时设置这两个密钥"
        )
        return False  # 暂不支持单独验证

    def _refresh_models(self):
        """刷新模型列表"""
        url = self.ollama_url_input.text().strip()
        if url:
            self.ai_bridge.ollama_config.base_url = url
            self.ai_bridge._ollama_processor = None

        models = self.ai_bridge.get_available_models()
        if models:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            self.logger.info(f"获取到 {len(models)} 个模型")
        else:
            self.logger.warning("未获取到模型列表")

    def _save_config(self):
        """保存配置"""
        # 获取当前Tab
        current_tab = self.parent()
        if not current_tab:
            current_tab = 0

        try:
            # 保存Ollama配置
            url = self.ollama_url_input.text().strip()
            model = self.model_combo.currentText().strip()
            self.ai_bridge.configure_ollama(base_url=url, model=model)

            # 保存云端配置（如果用户输入了）
            api_key = self.api_key_input.text().strip()
            if api_key:
                providers = {
                    "DeepSeek (推荐)": AIProvider.DEEPSEEK,
                    "通义千问 (阿里)": AIProvider.QIANWEN,
                    "文心一言 (百度)": AIProvider.WENXIN
                }
                provider = providers.get(
                    self.cloud_provider_combo.currentText(),
                    AIProvider.DEEPSEEK
                )
                model = self.cloud_model_input.text().strip() or None
                self.ai_bridge.configure_cloud(provider, api_key, model)

            QMessageBox.information(self, "成功", "配置已保存！")
            self.accept()

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.warning(self, "错误", f"保存失败: {e}")


class AIUsageStatsWidget(QWidget):
    """AI使用统计组件"""

    def __init__(self, ai_bridge: AIBridge, parent=None):
        super().__init__(parent)
        self.ai_bridge = ai_bridge
        self.logger = logging.getLogger(__name__)

        self._init_ui()
        self._load_stats()

        # 定时刷新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._load_stats)
        self.timer.start(60000)  # 每分钟刷新

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title = QLabel("📊 AI使用统计")
        title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        layout.addWidget(title)

        # 统计卡片
        stats = self.ai_bridge.get_usage_stats()

        cards_layout = QHBoxLayout()

        # 请求次数卡片
        self.requests_card = self._create_stat_card(
            "总请求", str(stats['total_requests']), "#2196F3"
        )
        cards_layout.addWidget(self.requests_card)

        # Token数卡片
        self.tokens_card = self._create_stat_card(
            "总Token", str(stats['total_tokens']), "#4CAF50"
        )
        cards_layout.addWidget(self.tokens_card)

        layout.addLayout(cards_layout)

        # 费用估算
        cost = stats['total_tokens'] / 1000 * 0.001  # 假设每千token $0.001
        self.cost_label = QLabel(f"💰 估算费用: ${cost:.4f}")
        self.cost_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.cost_label)

        layout.addStretch()

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {color}15;
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        return card

    def _load_stats(self):
        """加载统计数据"""
        try:
            stats = self.ai_bridge.get_usage_stats()
            self.requests_card.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(str(stats['total_requests']))
            self.tokens_card.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(str(stats['total_tokens']))

            cost = stats['total_tokens'] / 1000 * 0.001
            self.cost_label.setText(f"💰 估算费用: ${cost:.4f}")

        except Exception as e:
            self.logger.error(f"加载统计失败: {e}")
