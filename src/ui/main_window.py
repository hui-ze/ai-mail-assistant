# -*- coding: utf-8 -*-
"""
主窗口模块
三栏布局：账号栏 + 邮件列表 + 详情面板
"""

import logging
from typing import Optional, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLabel,
    QPushButton, QToolBar, QStatusBar, QMessageBox,
    QSplitter, QFrame, QLineEdit, QComboBox, QDialog,
    QTreeWidget, QTreeWidgetItem, QMenu, QSizePolicy,
    QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QScreen

from ..data.database import Database
from ..data.email_repo import EmailRepo
from ..data.user_profile_repo import UserProfileRepo
from ..core.imap_client import IMAPClient, EmailData
from ..core.ai_service import AIService
from .user_profile_dialog import UserProfileDialog
from .components.loading_overlay import LoadingOverlay
from .components.toast import Toast
from ..utils.icon_manager import get_icon_manager


class MainWindow(QMainWindow):
    """主窗口"""

    # 信号定义
    email_selected = pyqtSignal(int)  # 邮件ID
    account_changed = pyqtSignal(str)  # 账号变更
    refresh_requested = pyqtSignal()  # 刷新请求

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.email_repo = EmailRepo(db)
        self.ai_service = AIService(db)  # AI服务
        self.current_account: Optional[str] = None
        self.current_emails: List[EmailData] = []
        self.current_email_id: Optional[int] = None
        
        # 初始化logger（必须在其他方法调用之前）
        self.logger = logging.getLogger(__name__)

        # 初始化UI
        self._init_ui()
        
        # 恢复窗口状态（如果有保存的状态）
        self._restore_window_state()
        
        # 初始化加载遮罩（确保初始隐藏）
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        
        self._load_accounts()
        self._check_ai_status()
        self._load_all_todos()  # 加载所有待办事项（必须在 _create_statusbar 之后）
        
        # 首次启动引导（无账号时显示完整向导，否则只检查用户画像）
        self._check_first_run()

        self.logger.info("MainWindow initialized")

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("邮件智能助手")

        # 设置窗口图标
        try:
            icon_manager = get_icon_manager()
            icon_manager.setup_window_icon(self)
        except Exception as e:
            self.logger.warning(f"设置窗口图标失败: {e}")
        
        # 窗口自适应屏幕尺寸
        self._resize_to_screen()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 使用 QSplitter 实现可调整宽度的三栏布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)  # 分割线宽度
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E0E0E0;
            }
            QSplitter::handle:hover {
                background-color: #2196F3;
            }
        """)
        
        # 左侧栏：账号列表
        self.left_panel = self._create_left_panel()
        splitter.addWidget(self.left_panel)
        
        # 中间栏：邮件列表
        self.middle_panel = self._create_middle_panel()
        splitter.addWidget(self.middle_panel)
        
        # 右侧栏：详情/摘要面板
        self.right_panel = self._create_right_panel()
        splitter.addWidget(self.right_panel)
        
        # 设置初始宽度比例 (左:中:右 = 1:2:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        
        # 保存 splitter 引用（用于保存/恢复布局）
        self.main_splitter = splitter
        
        main_layout.addWidget(splitter)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建状态栏
        self._create_statusbar()
        
        # 连接信号
        self._connect_signals()
    
    def _resize_to_screen(self):
        """根据屏幕尺寸调整窗口大小"""
        # 获取主屏幕
        screen = QApplication.primaryScreen()
        if not screen:
            # 如果无法获取屏幕，使用默认尺寸
            self.setGeometry(100, 100, 1400, 900)
            return
        
        # 获取屏幕可用区域（排除任务栏）
        available_geometry = screen.availableGeometry()
        
        # 计算窗口尺寸（屏幕的 85%）
        width = int(available_geometry.width() * 0.85)
        height = int(available_geometry.height() * 0.85)
        
        # 计算居中位置
        x = available_geometry.x() + (available_geometry.width() - width) // 2
        y = available_geometry.y() + (available_geometry.height() - height) // 2
        
        # 设置窗口几何尺寸
        self.setGeometry(x, y, width, height)
        
        self.logger.info(f"窗口尺寸已适配屏幕: {width}x{height}, 位置: ({x}, {y})")

    def _create_left_panel(self) -> QFrame:
        """创建左侧栏"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setMinimumWidth(150)  # 最小宽度，防止过小
        frame.setAccessibleName("账号列表面板")
        
        # 设置大小策略：可伸展但保持最小宽度
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        frame.setSizePolicy(size_policy)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title = QLabel("📬 邮件账号")
        title.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(title)

        # 账号列表
        self.account_list = QListWidget()
        self.account_list.setAlternatingRowColors(True)
        self.account_list.setAccessibleName("邮箱账号列表")
        self.account_list.setAccessibleDescription("显示所有已配置的邮箱账号，点击选择")
        layout.addWidget(self.account_list)

        # 添加账号按钮
        add_btn = QPushButton("+ 添加账号")
        add_btn.clicked.connect(self._on_add_account)
        add_btn.setAccessibleName("添加邮箱账号")
        add_btn.setAccessibleDescription("添加新的邮箱账号配置")
        add_btn.setShortcut("Ctrl+Shift+A")
        layout.addWidget(add_btn)

        return frame

    def _create_middle_panel(self) -> QFrame:
        """创建中间栏"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setAccessibleName("邮件列表面板")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索邮件...")
        self.search_input.setAccessibleName("搜索邮件")
        self.search_input.setAccessibleDescription("输入关键词搜索邮件")
        # 设置 Ctrl+F 快捷键聚焦搜索框
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.search_input.setFocus)
        search_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "未读", "已读", "带附件"])
        self.filter_combo.setAccessibleName("邮件筛选")
        self.filter_combo.setAccessibleDescription("筛选邮件列表")
        search_layout.addWidget(self.filter_combo)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._on_refresh)
        refresh_btn.setAccessibleName("刷新邮件列表")
        refresh_btn.setAccessibleDescription("刷新当前账号的邮件列表")
        refresh_btn.setShortcut("F5")
        search_layout.addWidget(refresh_btn)

        layout.addLayout(search_layout)

        # 邮件列表
        self.email_list = QListWidget()
        self.email_list.setAlternatingRowColors(True)
        self.email_list.setSpacing(2)
        self.email_list.setAccessibleName("邮件列表")
        self.email_list.setAccessibleDescription("显示当前选中账号的所有邮件，按上下键浏览")
        
        # 设置自定义委托（实现未读高亮、附件图标等视觉效果）
        from .email_list_delegate import EmailListDelegate
        self.email_list.setItemDelegate(EmailListDelegate(self.email_list))
        
        layout.addWidget(self.email_list)

        return frame

    def _create_right_panel(self) -> QFrame:
        """创建右侧栏"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setAccessibleName("邮件详情面板")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # Tab标签页
        from PyQt5.QtWidgets import QTabWidget
        self.detail_tabs = QTabWidget()
        self.detail_tabs.setAccessibleName("邮件详情标签页")


        # 邮件详情页
        self.email_detail = QTextEdit()
        self.email_detail.setReadOnly(True)
        self.email_detail.setAccessibleName("邮件原始内容")
        self.detail_tabs.addTab(self.email_detail, "邮件内容")

        # AI摘要页
        self.summary_panel = QTextEdit()
        self.summary_panel.setReadOnly(True)
        self.summary_panel.setAccessibleName("AI生成的摘要")
        self.summary_panel.setAccessibleDescription("AI自动生成的邮件摘要和关键信息")
        self.detail_tabs.addTab(self.summary_panel, "AI摘要")

        # 待办事项页（全局待办列表 - 只显示未完成）
        from PyQt5.QtWidgets import QVBoxLayout as QVVBox, QTreeWidget, QTreeWidgetItem
        todo_widget = QWidget()
        todo_layout = QVBoxLayout(todo_widget)
        
        # 使用 TreeWidget 支持分组显示
        self.todo_tree = QTreeWidget()
        self.todo_tree.setHeaderLabels(["待办事项", "状态", "优先级"])
        self.todo_tree.setColumnWidth(0, 400)
        self.todo_tree.setColumnWidth(1, 80)
        self.todo_tree.setColumnWidth(2, 80)
        self.todo_tree.setAccessibleName("待办事项列表")
        self.todo_tree.setAccessibleDescription("未完成的待办事项，按邮件日期分组")
        
        # 启用多选模式（支持 Ctrl/Shift 多选）
        from PyQt5.QtWidgets import QAbstractItemView
        self.todo_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 启用右键菜单
        self.todo_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.todo_tree.customContextMenuRequested.connect(self._show_todo_context_menu)
        
        todo_layout.addWidget(self.todo_tree)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新待办列表")
        refresh_btn.clicked.connect(self._refresh_all_todo_lists)
        btn_layout.addWidget(refresh_btn)
        
        # 标记完成按钮
        complete_btn = QPushButton("✓ 标记完成")
        complete_btn.clicked.connect(self._on_mark_todo_complete)
        complete_btn.setAccessibleName("标记选中待办为已完成")
        btn_layout.addWidget(complete_btn)
        
        # 删除待办按钮
        delete_btn = QPushButton("🗑 删除待办")
        delete_btn.clicked.connect(self._on_delete_todo)
        delete_btn.setAccessibleName("删除选中的待办事项")
        btn_layout.addWidget(delete_btn)
        
        todo_layout.addLayout(btn_layout)
        
        # 双击切换完成状态
        self.todo_tree.itemDoubleClicked.connect(self._on_todo_double_click)
        
        self.detail_tabs.addTab(todo_widget, "待办事项")
        
        # 已完成事项页（独立的标签页）
        completed_widget = QWidget()
        completed_layout = QVBoxLayout(completed_widget)
        
        # 已完成事项树
        self.completed_tree = QTreeWidget()
        self.completed_tree.setHeaderLabels(["已完成事项", "完成时间", "优先级"])
        self.completed_tree.setColumnWidth(0, 400)
        self.completed_tree.setColumnWidth(1, 150)
        self.completed_tree.setColumnWidth(2, 80)
        self.completed_tree.setAccessibleName("已完成事项列表")
        self.completed_tree.setAccessibleDescription("已完成的待办事项，按邮件日期分组")
        
        # 启用多选
        self.completed_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 启用右键菜单
        self.completed_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.completed_tree.customContextMenuRequested.connect(self._show_completed_context_menu)
        
        completed_layout.addWidget(self.completed_tree)
        
        # 按钮区域
        completed_btn_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_completed_btn = QPushButton("🔄 刷新已完成列表")
        refresh_completed_btn.clicked.connect(self._refresh_all_todo_lists)
        completed_btn_layout.addWidget(refresh_completed_btn)
        
        # 标记未完成按钮
        incomplete_btn = QPushButton("↩ 标记未完成")
        incomplete_btn.clicked.connect(self._on_mark_completed_incomplete)
        incomplete_btn.setAccessibleName("标记选中项为未完成")
        completed_btn_layout.addWidget(incomplete_btn)
        
        # 删除按钮
        delete_completed_btn = QPushButton("🗑 删除")
        delete_completed_btn.clicked.connect(self._on_delete_completed)
        delete_completed_btn.setAccessibleName("删除选中的已完成事项")
        completed_btn_layout.addWidget(delete_completed_btn)
        
        completed_layout.addLayout(completed_btn_layout)
        
        # 双击切换状态
        self.completed_tree.itemDoubleClicked.connect(self._on_completed_double_click)
        
        self.detail_tabs.addTab(completed_widget, "已完成事项")

        layout.addWidget(self.detail_tabs)

        return frame

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setAccessibleName("主工具栏")
        toolbar.setAccessibleDescription("包含常用操作按钮的工具栏")
        self.addToolBar(toolbar)

        # 添加按钮
        new_btn = QPushButton("新邮件")
        new_btn.setAccessibleName("撰写新邮件")
        new_btn.setAccessibleDescription("创建一封新邮件")
        new_btn.setShortcut("Ctrl+N")
        toolbar.addWidget(new_btn)

        toolbar.addSeparator()

        # 智能分析按钮
        ai_btn = QPushButton("AI分析")
        ai_btn.clicked.connect(self._on_ai_analyze)
        ai_btn.setAccessibleName("AI分析当前邮件")
        ai_btn.setAccessibleDescription("使用AI分析当前选中邮件，生成摘要和提取待办事项")
        ai_btn.setShortcut("Ctrl+A")
        self.ai_btn = ai_btn  # 保存引用以便后续使用
        toolbar.addWidget(ai_btn)

        toolbar.addSeparator()

        # 同步到日历按钮
        sync_cal_btn = QPushButton("同步到日历")
        sync_cal_btn.clicked.connect(self._on_sync_to_calendar)
        sync_cal_btn.setAccessibleName("同步待办到日历")
        sync_cal_btn.setAccessibleDescription("将当前邮件的待办事项同步到系统日历")
        sync_cal_btn.setShortcut("Ctrl+L")
        toolbar.addWidget(sync_cal_btn)

        toolbar.addSeparator()

        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self._on_open_settings)
        settings_btn.setAccessibleName("打开设置")
        settings_btn.setAccessibleDescription("打开应用程序设置对话框")
        settings_btn.setShortcut("Ctrl+,")
        toolbar.addWidget(settings_btn)

    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.statusbar.setAccessibleName("状态栏")
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")

    def _connect_signals(self):
        """连接信号"""
        self.account_list.itemClicked.connect(self._on_account_selected)
        self.email_list.itemClicked.connect(self._on_email_selected)
        self.search_input.textChanged.connect(self._on_search)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)

    def _load_accounts(self):
        """加载账号列表"""
        self.account_list.clear()
        accounts = self.db.query("SELECT id, email_address FROM accounts ORDER BY created_at DESC")
        for account_id, email in accounts:
            self.account_list.addItem(f"{email} ({account_id})")

        if accounts:
            self.account_list.setCurrentRow(0)

    def _on_add_account(self):
        """添加账号"""
        from .add_account_dialog import AddAccountDialog

        dialog = AddAccountDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_accounts()
            self.statusbar.showMessage("账号添加成功", 3000)

    def _on_account_selected(self, item: QListWidgetItem):
        """账号选中"""
        text = item.text()
        # 提取邮箱地址
        email = text.split(" (")[0]
        self.current_account = email
        self.account_changed.emit(email)
        self._load_emails(email)

    def _load_emails(self, account_email: str):
        """加载邮件列表"""
        self.email_list.clear()
        self.current_emails = []

        # 获取 account_id
        account = self.db.query_one(
            "SELECT id FROM accounts WHERE email_address = ?", 
            (account_email,)
        )
        if not account:
            return
        
        account_id = account[0]

        # 从数据库加载邮件
        emails = self.email_repo.get_emails_by_account(account_id, limit=100)

        for email_data in emails:
            self._add_email_to_list(email_data)

        self.statusbar.showMessage(f"已加载 {len(emails)} 封邮件", 3000)

    def _add_email_to_list(self, email: dict):
        """添加邮件到列表
        
        Args:
            email: 邮件字典（来自 EmailRepo.get_emails_by_account）
        """
        item = QListWidgetItem()
        
        # 绑定完整的邮件数据到 item（用于委托渲染）
        item.setData(Qt.UserRole, email)
        
        # 设置列表项大小（委托会使用）
        item.setSizeHint(QSize(0, 65))
        
        self.email_list.addItem(item)
        self.current_emails.append(email)

    def _on_email_selected(self, item: QListWidgetItem):
        """邮件选中"""
        row = self.email_list.row(item)
        if 0 <= row < len(self.current_emails):
            email = self.current_emails[row]
            self._show_email_detail(email)
            email_id = email.get('id')
            if email_id:
                self.email_selected.emit(email_id)

    def _show_email_detail(self, email: dict):
        """显示邮件详情"""
        # 从字典中安全获取数据
        sender = email.get('sender', '(未知发件人)')
        recipient = email.get('recipient', email.get('recipients', '(未知收件人)'))
        subject = email.get('subject', '(无主题)')
        date = email.get('date', '')
        body = email.get('body', email.get('body_text', '(无内容)'))
        
        content = f"""
<b>发件人:</b> {sender}<br>
<b>收件人:</b> {recipient}<br>
<b>主题:</b> {subject}<br>
<b>时间:</b> {date}<br>
<hr>
{body}
"""
        self.email_detail.setHtml(content)

    def _on_search(self, text: str):
        """搜索"""
        # 简单实现：过滤列表
        for i in range(self.email_list.count()):
            item = self.email_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _on_filter_changed(self, index: int):
        """筛选变更"""
        filter_text = self.filter_combo.currentText()
        
        # 特殊处理：带附件筛选暂未实现
        if filter_text == "带附件":
            QMessageBox.information(
                self, 
                "功能提示", 
                "附件筛选功能需要升级数据库结构，\n"
                "当前版本暂不支持此功能。\n\n"
                "后续版本会添加附件检测功能。"
            )
            # 重置回"全部"
            self.filter_combo.blockSignals(True)  # 阻止信号触发
            self.filter_combo.setCurrentIndex(0)  # 切换回"全部"
            self.filter_combo.blockSignals(False)
            return
        
        # 遍历当前邮件列表，根据筛选条件隐藏/显示
        for i in range(self.email_list.count()):
            item = self.email_list.item(i)
            if 0 <= i < len(self.current_emails):
                email = self.current_emails[i]
                should_show = self._should_show_email(email, filter_text)
                item.setHidden(not should_show)
        
        # 更新状态栏
        visible_count = sum(1 for i in range(self.email_list.count()) if not self.email_list.item(i).isHidden())
        self.statusbar.showMessage(f"显示 {visible_count} 封邮件（筛选条件：{filter_text}）", 3000)
    
    def _should_show_email(self, email: dict, filter_text: str) -> bool:
        """判断邮件是否应该显示
        
        Args:
            email: 邮件字典
            filter_text: 筛选条件（"全部"、"未读"、"已读"）
        
        Returns:
            是否应该显示
        """
        if filter_text == "全部":
            return True
        elif filter_text == "未读":
            return not email.get('is_read', False)
        elif filter_text == "已读":
            return email.get('is_read', False)
        return True

    def _on_refresh(self):
        """刷新邮件 - 从 IMAP 服务器同步"""
        if not self.current_account:
            QMessageBox.information(self, "提示", "请先选择一个账号")
            return

        self.statusbar.showMessage("正在连接邮箱服务器...")
        
        # 获取账号配置
        account = self.db.query_one(
            "SELECT id, email_address, imap_server, imap_port, auth_code_encrypted FROM accounts WHERE email_address = ?",
            (self.current_account,)
        )
        
        if not account:
            QMessageBox.warning(self, "错误", "账号信息不存在")
            return
        
        account_id, email_addr, server, port, auth_code = account
        
        # 在后台线程执行同步
        from PyQt5.QtCore import QThread, pyqtSignal
        from ..core.imap_client import IMAPClient
        
        class SyncThread(QThread):
            finished = pyqtSignal(list, str)  # (emails, error_msg)
            progress = pyqtSignal(str)
            
            def __init__(self, server, port, email, auth_code):
                super().__init__()
                self.server = server
                self.port = port
                self.email = email
                self.auth_code = auth_code
            
            def run(self):
                client = None
                try:
                    client = IMAPClient()
                    self.progress.emit("正在连接服务器...")
                    
                    if not client.connect(self.server, self.port, self.email, self.auth_code):
                        self.finished.emit([], "连接失败，请检查授权码")
                        return
                    
                    self.progress.emit("正在选择收件箱...")
                    if not client.select_folder("INBOX"):
                        self.finished.emit([], "无法打开收件箱")
                        return
                    
                    self.progress.emit("正在获取邮件列表...")
                    emails = client.fetch_emails(limit=50)
                    
                    if client:
                        client.disconnect()
                    self.finished.emit(emails, "")
                    
                except Exception as e:
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    self.finished.emit([], f"{type(e).__name__}: {str(e)}")
        
        self._sync_thread = SyncThread(server, port, email_addr, auth_code)
        self._sync_thread.progress.connect(lambda msg: self.statusbar.showMessage(msg))
        self._sync_thread.finished.connect(lambda emails, err: self._on_sync_finished(emails, err, account_id))
        self._sync_thread.start()
        
        # 显示加载遮罩
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.show("正在同步邮件...", "正在连接服务器...", cancellable=False)
    
    def _on_sync_finished(self, emails, error_msg, account_id):
        """同步完成回调"""
        # 确保隐藏 loading overlay
        try:
            if hasattr(self, 'loading_overlay'):
                self.loading_overlay.hide()
        except Exception:
            pass
        
        if error_msg:
            QMessageBox.critical(self, "同步失败", f"❌ {error_msg}")
            self.statusbar.showMessage(f"同步失败: {error_msg}", 5000)
            return
        
        if not emails:
            self.statusbar.showMessage("没有新邮件", 3000)
            return
        
        # 保存邮件到数据库
        saved_count = 0
        for email_data in emails:
            try:
                # 检查是否已存在
                existing = self.email_repo.get_email_by_uid(email_data.uid, account_id)
                if existing:
                    continue
                
                # 保存新邮件（使用 EmailRepo.save_email 的正确签名）
                self.email_repo.save_email(email_data, account_id)
                saved_count += 1
                
            except Exception as e:
                self.logger.warning(f"保存邮件失败: {e}")
        
        # 刷新列表
        self._load_emails(self.current_account)
        self.statusbar.showMessage(f"同步完成，新增 {saved_count} 封邮件", 5000)
        QMessageBox.information(self, "同步完成", f"✅ 成功同步 {saved_count} 封新邮件")

    def _check_ai_status(self):
        """检查AI服务状态"""
        status = self.ai_service.get_ai_status()
        if status['available']:
            self.logger.info(f"AI服务可用: {status['provider']}")
        else:
            self.logger.warning("AI服务不可用，请配置AI服务")

    def _on_ai_analyze(self):
        """AI分析当前邮件"""
        current_row = self.email_list.currentRow()
        if current_row < 0 or current_row >= len(self.current_emails):
            Toast.warning(self, "请先选择一封邮件")
            return

        email = self.current_emails[current_row]
        self.current_email_id = email.get('id')

        # 检查AI服务是否可用
        if not self.ai_service.ai_bridge.is_available():
            reply = QMessageBox.question(
                self, 'AI未配置',
                "AI服务未配置，是否现在配置？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from .ai_manager import AIConfigDialog
                dialog = AIConfigDialog(self.ai_service.ai_bridge, self)
                dialog.exec_()
                if not self.ai_service.ai_bridge.is_available():
                    return
            else:
                return

        self.detail_tabs.setCurrentIndex(1)  # 切换到摘要页

        # 检查是否已有摘要
        email_id = email.get('id')
        existing_summary = self.ai_service.get_email_summary(email_id)
        
        # 决定是否强制重新生成
        force = False
        if existing_summary:
            # 已有摘要，询问是否重新生成
            reply = QMessageBox.question(
                self, '重新生成摘要',
                "该邮件已有AI摘要，是否重新生成？\n\n重新生成将覆盖现有摘要和待办事项。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                force = True

        # 显示加载遮罩
        self.loading_overlay.show("正在进行AI分析...", "正在连接AI服务...", cancellable=False)

        # 创建后台线程执行 AI 分析
        class AIAnalysisThread(QThread):
            finished = pyqtSignal(dict)  # 分析结果
            progress = pyqtSignal(int, str)  # 进度更新
            
            def __init__(self, ai_service, email_id, force):
                super().__init__()
                self.ai_service = ai_service
                self.email_id = email_id
                self.force = force
            
            def run(self):
                try:
                    self.progress.emit(20, "正在分析邮件内容...")
                    result = self.ai_service.generate_email_summary(self.email_id, force=self.force)
                    self.progress.emit(80, "正在处理结果...")
                    self.finished.emit(result)
                except Exception as e:
                    self.finished.emit({
                        'success': False,
                        'error': str(e)
                    })
        
        # 创建并启动线程
        self.ai_thread = AIAnalysisThread(self.ai_service, email_id, force)
        self.ai_thread.progress.connect(self._on_ai_progress)
        self.ai_thread.finished.connect(self._on_ai_finished)
        self.ai_thread.start()
    
    def _on_ai_progress(self, percent: int, message: str):
        """AI分析进度更新"""
        self.loading_overlay.update_progress(percent, message)
    
    def _on_ai_finished(self, result: dict):
        """AI分析完成"""
        try:
            if result['success']:
                summary = result['summary']
                
                # 构建摘要HTML
                html_parts = [
                    '<div style="font-family:\'Microsoft YaHei\',sans-serif;padding:15px;">',
                    '<h4 style="color:#333;margin:0 0 10px 0;">📝 摘要</h4>',
                    '<hr style="border:0;border-top:1px solid #eee;margin-bottom:10px;">',
                    f'<p style="color:#555;line-height:1.8;white-space:pre-wrap;">{summary["summary_text"]}</p>',
                ]
                
                # 如果有待办事项，添加待办列表
                todos = summary.get('todos', [])
                if todos:
                    html_parts.extend([
                        '<div style="margin-top:20px;padding-top:15px;border-top:1px solid #eee;">',
                        '<h4 style="color:#333;margin:0 0 10px 0;">✅ 待办事项</h4>',
                        '<ul style="color:#555;line-height:1.8;margin:0;padding-left:20px;">'
                    ])
                    for todo in todos:
                        html_parts.append(f'<li style="margin:8px 0;">{todo}</li>')
                    html_parts.extend([
                        '</ul>',
                        '</div>'
                    ])
                
                # 添加模型信息
                html_parts.extend([
                    '<div style="margin-top:20px;padding-top:10px;border-top:1px solid #eee;">',
                    f'<p style="color:#888;font-size:9pt;margin:0;">🤖 模型: {summary["model_used"]} | 📊 Token: {summary["tokens_used"]}</p>',
                    '</div>',
                    '</div>'
                ])
                
                html = '\n'.join(html_parts)
                self.summary_panel.setHtml(html)

                # 刷新待办列表
                if result.get('todo_count', 0) > 0:
                    self._load_all_todos()

                self.loading_overlay.update_progress(100, "分析完成！")
                QTimer.singleShot(500, self.loading_overlay.hide)
                Toast.success(self, f"AI分析完成，提取到 {result.get('todo_count', 0)} 个待办", duration=3000)
            else:
                self.loading_overlay.hide()
                self.summary_panel.setHtml(f'<div style="color:red;padding:20px;">❌ 分析失败: {result.get("error")}</div>')
                Toast.error(self, f"AI分析失败: {result.get('error', '未知错误')}", duration=4000)

        except Exception as e:
            self.loading_overlay.hide()
            self.logger.error(f"AI分析失败: {e}")
            self.summary_panel.setHtml(f'<div style="color:red;padding:20px;">❌ 错误: {str(e)}</div>')
            Toast.error(self, f"发生错误: {str(e)}", duration=4000)

    def _on_extract_todos(self):
        """提取待办事项"""
        current_row = self.email_list.currentRow()
        if current_row < 0 or current_row >= len(self.current_emails):
            Toast.warning(self, "请先选择一封邮件")
            return

        email = self.current_emails[current_row]
        self.current_email_id = email.get('id')

        # 检查AI服务
        if not self.ai_service.ai_bridge.is_available():
            Toast.warning(self, "请先配置AI服务")
            return

        # 显示加载遮罩
        self.loading_overlay.show("正在提取待办事项...", cancellable=False)

        try:
            # 提取待办
            email_id = email.get('id')
            result = self.ai_service.extract_todos_from_email(email_id)
            
            self.loading_overlay.hide()

            if result['success'] and result.get('saved_count', 0) > 0:
                # 刷新全局待办列表
                self._load_all_todos()
                # 切换到待办页
                self.detail_tabs.setCurrentIndex(2)
                Toast.success(self, f"提取到 {result['saved_count']} 个待办事项")
            else:
                Toast.info(self, "该邮件中未发现待办事项")

        except Exception as e:
            self.logger.error(f"待办提取失败: {e}")
            self.todo_list.addItem(f"❌ 错误: {str(e)}")

    def _load_email_todos(self, email_id: int):
        """加载邮件的待办事项（更新全局列表）"""
        # 刷新全局待办列表
        self._load_all_todos()
    
    def _load_all_todos(self):
        """加载未完成的待办事项，按邮件日期分组"""
        self.todo_tree.clear()
        try:
            # 获取所有未完成的待办事项，关联邮件信息
            sql = '''
                SELECT t.id, t.content, t.priority, t.email_id,
                       e.subject, e.date, e.sender
                FROM todos t
                LEFT JOIN emails e ON t.email_id = e.id
                WHERE t.completed = 0
                ORDER BY e.date DESC, t.created_at DESC
            '''
            results = self.db.query(sql)

            if not results:
                item = QTreeWidgetItem(self.todo_tree)
                item.setText(0, "暂无待办事项")
                item.setDisabled(True)
                return

            # 按邮件日期分组
            current_date_group = None
            current_parent = None
            todo_count = 0

            for row in results:
                todo_id, content, priority, email_id, subject, email_date, sender = row

                # 格式化日期（只取日期部分）
                date_str = email_date[:10] if email_date else "未知日期"

                # 创建新的日期分组
                if date_str != current_date_group:
                    current_date_group = date_str
                    current_parent = QTreeWidgetItem(self.todo_tree)
                    current_parent.setText(0, f"📅 {date_str}")
                    current_parent.setExpanded(True)
                    current_parent.setFont(0, QFont("Microsoft YaHei", 10, QFont.Bold))

                # 创建待办项
                todo_item = QTreeWidgetItem(current_parent)
                priority_icon = "🔴" if priority == "high" else ("🟡" if priority == "medium" else "🟢")

                # 显示待办内容和邮件主题
                display_text = f"☐ {content}"
                if subject:
                    display_text += f" (📧 {subject[:30]}{'...' if len(subject) > 30 else ''})"

                todo_item.setText(0, display_text)
                todo_item.setText(1, "待处理")
                todo_item.setText(2, f"{priority_icon} {priority}")
                todo_item.setData(0, Qt.UserRole, todo_id)  # 存储待办ID
                todo_count += 1

            # 统计信息
            self.statusbar.showMessage(f"待处理: {todo_count} 项", 3000)
            
        except Exception as e:
            self.logger.error(f"加载待办失败: {e}")
            item = QTreeWidgetItem(self.todo_tree)
            item.setText(0, f"❌ 加载失败: {str(e)}")
            item.setDisabled(True)
    
    def _load_completed_todos(self):
        """加载已完成的待办事项，按邮件日期分组"""
        self.completed_tree.clear()
        try:
            # 获取所有已完成的待办事项，按邮件日期分组
            # 先查询每个日期是否有未完成的待办
            sql = '''
                SELECT t.id, t.content, t.priority, t.email_id,
                       e.subject, e.date, e.sender, t.completed_at
                FROM todos t
                LEFT JOIN emails e ON t.email_id = e.id
                WHERE t.completed = 1
                AND NOT EXISTS (
                    SELECT 1 FROM todos t2 
                    LEFT JOIN emails e2 ON t2.email_id = e2.id
                    WHERE t2.completed = 0 
                    AND COALESCE(e2.date, '') = COALESCE(e.date, '')
                )
                ORDER BY e.date DESC, t.completed_at DESC
            '''
            results = self.db.query(sql)
            
            if not results:
                item = QTreeWidgetItem(self.completed_tree)
                item.setText(0, "暂无已完成事项")
                item.setDisabled(True)
                return
            
            # 按邮件日期分组
            current_date_group = None
            current_parent = None
            completed_count = 0
            
            for row in results:
                todo_id, content, priority, email_id, subject, email_date, sender, completed_at = row
                
                # 格式化日期（只取日期部分）
                date_str = email_date[:10] if email_date else "未知日期"
                
                # 创建新的日期分组
                if date_str != current_date_group:
                    current_date_group = date_str
                    current_parent = QTreeWidgetItem(self.completed_tree)
                    current_parent.setText(0, f"📅 {date_str} (全部完成)")
                    current_parent.setExpanded(True)
                    current_parent.setFont(0, QFont("Microsoft YaHei", 10, QFont.Bold))
                    current_parent.setForeground(0, QColor("#388E3C"))  # 绿色
                
                # 创建已完成项
                todo_item = QTreeWidgetItem(current_parent)
                priority_icon = "🔴" if priority == "high" else ("🟡" if priority == "medium" else "🟢")
                
                # 显示待办内容
                display_text = f"✅ {content}"
                if subject:
                    display_text += f" (📧 {subject[:30]}{'...' if len(subject) > 30 else ''})"
                
                todo_item.setText(0, display_text)
                
                # 显示完成时间
                if completed_at:
                    completed_time = completed_at[:16] if len(completed_at) > 16 else completed_at
                    todo_item.setText(1, f"✓ {completed_time}")
                else:
                    todo_item.setText(1, "已完成")
                
                todo_item.setText(2, f"{priority_icon} {priority}")
                todo_item.setData(0, Qt.UserRole, todo_id)  # 存储待办ID
                
                # 已完成的待办用灰色显示
                todo_item.setForeground(0, QColor("#999"))
                todo_item.setForeground(1, QColor("#999"))
                completed_count += 1
            
            # 统计信息
            self.statusbar.showMessage(f"已完成: {completed_count} 项", 3000)
            
        except Exception as e:
            self.logger.error(f"加载已完成事项失败: {e}")
            item = QTreeWidgetItem(self.completed_tree)
            item.setText(0, f"❌ 加载失败: {str(e)}")
            item.setDisabled(True)
    
    def _refresh_all_todo_lists(self):
        """刷新待办事项和已完成事项两个列表"""
        self._load_all_todos()
        self._load_completed_todos()
    
    def _on_todo_double_click(self, item: QTreeWidgetItem, column: int):
        """双击待办事项切换完成状态"""
        # 检查是否是待办项（有存储ID的）
        todo_id = item.data(0, Qt.UserRole)
        if not todo_id:
            return  # 这是日期分组标题，不处理
        
        # 切换完成状态
        try:
            # 查询当前状态
            current = self.db.query_one(
                "SELECT completed FROM todos WHERE id = ?",
                (todo_id,)
            )
            
            if not current:
                return
            
            is_completed = not current[0]
            
            # 更新数据库（execute 会自动 commit）
            self.db.execute(
                "UPDATE todos SET completed = ? WHERE id = ?",
                (is_completed, todo_id)
            )
            
            # 刷新列表
            self._load_all_todos()
            
            status = "已完成" if is_completed else "待处理"
            self.statusbar.showMessage(f"待办事项已标记为{status}", 3000)
            
        except Exception as e:
            self.logger.error(f"切换待办状态失败: {e}")
            QMessageBox.warning(self, "错误", f"操作失败: {str(e)}")
    
    def _on_mark_todo_complete(self):
        """标记选中待办为已完成"""
        selected_items = self.todo_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个待办事项")
            return
        
        count = 0
        for item in selected_items:
            todo_id = item.data(0, Qt.UserRole)
            if not todo_id:
                continue  # 跳过分组标题
            
            try:
                # 标记为已完成，并记录完成时间
                self.db.execute(
                    "UPDATE todos SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (todo_id,)
                )
                count += 1
            except Exception as e:
                self.logger.error(f"标记完成失败: {e}")
        
        self._refresh_all_todo_lists()
        self.statusbar.showMessage(f"已标记 {count} 个待办为完成", 3000)
    
    def _on_mark_todo_incomplete(self):
        """标记选中待办为未完成"""
        selected_items = self.todo_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个待办事项")
            return
        
        count = 0
        for item in selected_items:
            todo_id = item.data(0, Qt.UserRole)
            if not todo_id:
                continue  # 跳过分组标题
            
            try:
                # 标记为未完成，清除完成时间
                self.db.execute(
                    "UPDATE todos SET completed = 0, completed_at = NULL WHERE id = ?",
                    (todo_id,)
                )
                count += 1
            except Exception as e:
                self.logger.error(f"标记未完成失败: {e}")
        
        self._refresh_all_todo_lists()
        self.statusbar.showMessage(f"已标记 {count} 个待办为未完成", 3000)
    
    def _on_delete_todo(self):
        """删除选中的待办事项"""
        selected_items = self.todo_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个待办事项")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_items)} 个待办事项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        count = 0
        for item in selected_items:
            todo_id = item.data(0, Qt.UserRole)
            if not todo_id:
                continue
            
            try:
                self.db.execute(
                    "DELETE FROM todos WHERE id = ?",
                    (todo_id,)
                )
                count += 1
            except Exception as e:
                self.logger.error(f"删除待办失败: {e}")
        
        self._load_all_todos()
        self.statusbar.showMessage(f"已删除 {count} 个待办事项", 3000)
    
    def _show_todo_context_menu(self, position):
        """显示待办事项右键菜单"""
        selected_items = self.todo_tree.selectedItems()
        if not selected_items:
            return
        
        # 过滤出真正的待办项（排除日期分组标题）
        todo_items = []
        for item in selected_items:
            todo_id = item.data(0, Qt.UserRole)
            if todo_id:
                todo_items.append((item, todo_id))
        
        if not todo_items:
            return
        
        from PyQt5.QtWidgets import QMenu, QAction
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 根据选中数量显示不同的菜单项
        if len(todo_items) == 1:
            # 单个待办：显示切换状态和删除
            todo_id = todo_items[0][1]
            
            # 查询当前状态
            current = self.db.query_one(
                "SELECT completed FROM todos WHERE id = ?",
                (todo_id,)
            )
            
            if current:
                is_completed = current[0]
                
                # 切换完成状态
                toggle_action = QAction("✓ 标记为已完成" if not is_completed else "☐ 标记为未完成", self)
                toggle_action.triggered.connect(lambda: self._toggle_todo_status(todo_id))
                menu.addAction(toggle_action)
        else:
            # 多个待办：显示批量操作
            mark_complete_action = QAction(f"✓ 标记为已完成 ({len(todo_items)}个)", self)
            mark_complete_action.triggered.connect(self._on_mark_todo_complete)
            menu.addAction(mark_complete_action)
            
            mark_incomplete_action = QAction(f"☐ 标记为未完成 ({len(todo_items)}个)", self)
            mark_incomplete_action.triggered.connect(self._on_mark_todo_incomplete)
            menu.addAction(mark_incomplete_action)
        
        menu.addSeparator()
        
        # 删除操作（单选和多选都适用）
        delete_text = f"🗑 删除待办 ({len(todo_items)}个)" if len(todo_items) > 1 else "🗑 删除待办"
        delete_action = QAction(delete_text, self)
        delete_action.triggered.connect(self._on_delete_todo)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(self.todo_tree.viewport().mapToGlobal(position))
    
    def _toggle_todo_status(self, todo_id: int):
        """切换单个待办的完成状态"""
        try:
            # 查询当前状态
            current = self.db.query_one(
                "SELECT completed FROM todos WHERE id = ?",
                (todo_id,)
            )
            
            if not current:
                return
            
            is_completed = not current[0]
            
            # 更新数据库（execute 会自动 commit）
            if is_completed:
                # 标记为已完成，记录完成时间
                self.db.execute(
                    "UPDATE todos SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (todo_id,)
                )
            else:
                # 标记为未完成，清除完成时间
                self.db.execute(
                    "UPDATE todos SET completed = 0, completed_at = NULL WHERE id = ?",
                    (todo_id,)
                )
            
            # 刷新两个列表
            self._refresh_all_todo_lists()
            
            status = "已完成" if is_completed else "未完成"
            self.statusbar.showMessage(f"待办事项已标记为{status}", 3000)
            
        except Exception as e:
            self.logger.error(f"切换待办状态失败: {e}")
            QMessageBox.warning(self, "错误", f"操作失败: {str(e)}")
    
    def _show_completed_context_menu(self, position):
        """显示已完成事项的右键菜单"""
        selected_items = self.completed_tree.selectedItems()
        
        # 过滤出有效的已完成项（排除分组标题）
        todo_items = [item for item in selected_items if item.data(0, Qt.UserRole)]
        
        if not todo_items:
            return
        
        menu = QMenu()
        
        if len(todo_items) == 1:
            # 单选：显示切换状态选项
            toggle_action = menu.addAction("标记为未完成")
            delete_action = menu.addAction("删除")
            
            action = menu.exec_(self.completed_tree.mapToGlobal(position))
            
            if action == toggle_action:
                self._on_mark_completed_incomplete()
            elif action == delete_action:
                self._on_delete_completed()
        else:
            # 多选：显示批量操作
            batch_incomplete_action = menu.addAction(f"批量标记未完成 ({len(todo_items)} 项)")
            batch_delete_action = menu.addAction(f"批量删除 ({len(todo_items)} 项)")
            
            action = menu.exec_(self.completed_tree.mapToGlobal(position))
            
            if action == batch_incomplete_action:
                self._on_mark_completed_incomplete()
            elif action == batch_delete_action:
                self._on_delete_completed()
    
    def _on_completed_double_click(self, item: QTreeWidgetItem, column: int):
        """双击已完成事项切换为未完成"""
        todo_id = item.data(0, Qt.UserRole)
        if not todo_id:
            return  # 这是日期分组标题，不处理
        
        # 标记为未完成
        try:
            self.db.execute(
                "UPDATE todos SET completed = 0, completed_at = NULL WHERE id = ?",
                (todo_id,)
            )
            
            self._refresh_all_todo_lists()
            self.statusbar.showMessage("待办事项已标记为未完成", 3000)
            
        except Exception as e:
            self.logger.error(f"切换状态失败: {e}")
            QMessageBox.warning(self, "错误", f"操作失败: {str(e)}")
    
    def _on_mark_completed_incomplete(self):
        """标记已完成的待办为未完成"""
        selected_items = self.completed_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个已完成事项")
            return
        
        count = 0
        for item in selected_items:
            todo_id = item.data(0, Qt.UserRole)
            if not todo_id:
                continue  # 跳过分组标题
            
            try:
                self.db.execute(
                    "UPDATE todos SET completed = 0, completed_at = NULL WHERE id = ?",
                    (todo_id,)
                )
                count += 1
            except Exception as e:
                self.logger.error(f"标记未完成失败: {e}")
        
        self._refresh_all_todo_lists()
        self.statusbar.showMessage(f"已标记 {count} 项为未完成", 3000)
    
    def _on_delete_completed(self):
        """删除选中的已完成事项"""
        selected_items = self.completed_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择一个已完成事项")
            return
        
        # 过滤出有效的已完成项
        todo_items = [item for item in selected_items if item.data(0, Qt.UserRole)]
        
        if not todo_items:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(todo_items)} 个已完成事项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        count = 0
        for item in todo_items:
            todo_id = item.data(0, Qt.UserRole)
            try:
                self.db.execute(
                    "DELETE FROM todos WHERE id = ?",
                    (todo_id,)
                )
                count += 1
            except Exception as e:
                self.logger.error(f"删除失败: {e}")
        
        self._refresh_all_todo_lists()
        self.statusbar.showMessage(f"已删除 {count} 个已完成事项", 3000)
    
    def _delete_single_todo(self, todo_id: int):
        """删除单个待办事项"""
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个待办事项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.db.execute(
                "DELETE FROM todos WHERE id = ?",
                (todo_id,)
            )
            self._refresh_all_todo_lists()
            self.statusbar.showMessage("待办事项已删除", 3000)
        except Exception as e:
            self.logger.error(f"删除待办失败: {e}")
            QMessageBox.warning(self, "错误", f"删除失败: {str(e)}")

    def set_status(self, message: str):
        """设置状态栏消息"""
        self.statusbar.showMessage(message)

    def _on_open_settings(self):
        """打开设置对话框"""
        from .settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.db, self)
        dialog.exec_()

    def _on_sync_to_calendar(self):
        """同步待办到日历"""
        current_row = self.email_list.currentRow()
        if current_row < 0 or current_row >= len(self.current_emails):
            QMessageBox.information(self, "提示", "请先选择一封邮件")
            return

        email = self.current_emails[current_row]
        email_id = email.get('id')

        # 检查是否有所属待办
        from ..data.todo_repo import TodoRepo
        todo_repo = TodoRepo(self.db)
        todos = todo_repo.get_todos_by_email(email_id)

        if not todos:
            QMessageBox.information(self, "提示", "当前邮件没有待办事项")
            return

        # 创建日历同步服务
        from ..core.calendar_sync import create_calendar_sync

        # 获取日历设置
        import json
        calendar_settings = self.db.query_one(
            "SELECT value FROM settings WHERE id = 2"
        )
        calendar_type = 3  # 默认本地日历
        if calendar_settings and calendar_settings[0]:
            try:
                settings = json.loads(calendar_settings[0])
                calendar_type = settings.get('type', 3)
            except:
                pass

        calendar_sync = create_calendar_sync(self.db, calendar_type)

        if not calendar_sync.is_configured():
            reply = QMessageBox.question(
                self, '日历未配置',
                "日历服务未配置，是否现在配置？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._on_open_settings()
            return

        # 同步待办
        synced_count = 0
        for todo in todos:
            result = calendar_sync.sync_todo_to_calendar(todo)
            if result.success:
                synced_count += 1

        QMessageBox.information(
            self, "同步完成",
            f"成功同步 {synced_count}/{len(todos)} 个待办到日历"
        )

    def closeEvent(self, event):
        """关闭事件"""
        # 保存窗口状态
        self._save_window_state()
        
        reply = QMessageBox.question(
            self, '确认退出',
            "确定要退出邮件助手吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    
    def _save_window_state(self):
        """保存窗口状态到数据库"""
        try:
            import json
            
            # 保存分割器状态
            splitter_state = self.main_splitter.saveState().data().hex()
            
            window_state = {
                'splitter_state': splitter_state,
                'window_geometry': {
                    'x': self.geometry().x(),
                    'y': self.geometry().y(),
                    'width': self.width(),
                    'height': self.height()
                }
            }
            
            # 保存到数据库 settings 表
            self.db.execute(
                "INSERT OR REPLACE INTO settings (id, value) VALUES (10, ?)",
                (json.dumps(window_state),)
            )
            
            self.logger.info("窗口状态已保存")
            
        except Exception as e:
            self.logger.error(f"保存窗口状态失败: {e}")
    
    def _restore_window_state(self):
        """从数据库恢复窗口状态"""
        try:
            import json
            from PyQt5.QtCore import QByteArray
            
            result = self.db.query_one("SELECT value FROM settings WHERE id = 10")
            if not result or not result[0]:
                return
            
            window_state = json.loads(result[0])
            
            # 恢复分割器状态
            if 'splitter_state' in window_state:
                splitter_data = QByteArray.fromHex(window_state['splitter_state'].encode())
                self.main_splitter.restoreState(splitter_data)
            
            # 恢复窗口几何尺寸（如果用户之前调整过）
            if 'window_geometry' in window_state:
                geo = window_state['window_geometry']
                # 验证几何尺寸是否有效（在屏幕范围内）
                screen = QApplication.primaryScreen()
                if screen:
                    available = screen.availableGeometry()
                    # 确保窗口在屏幕可见范围内
                    if (geo['x'] >= available.x() and 
                        geo['y'] >= available.y() and 
                        geo['x'] + geo['width'] <= available.x() + available.width() and
                        geo['y'] + geo['height'] <= available.y() + available.height()):
                        self.setGeometry(geo['x'], geo['y'], geo['width'], geo['height'])
            
            self.logger.info("窗口状态已恢复")
            
        except Exception as e:
            self.logger.error(f"恢复窗口状态失败: {e}")
    
    def _check_first_run(self):
        """首次运行检测：无账号时显示完整引导向导，否则只检查用户画像"""
        accounts = self.db.query("SELECT id FROM accounts LIMIT 1")
        
        if not accounts:
            # 全新用户：显示完整引导向导
            self.logger.info("首次启动，显示引导向导")
            from .welcome_wizard import WelcomeWizard
            wizard = WelcomeWizard(self.db, self)
            wizard.exec_()
            # 向导完成后重新加载账号列表
            self._load_accounts()
        else:
            # 已有账号：只检查用户画像是否设置
            self._check_user_profile()

    def _check_user_profile(self):
        """检查用户画像，如果为空则显示引导对话框"""
        profile_repo = UserProfileRepo(self.db)
        
        if profile_repo.is_profile_empty():
            self.logger.info("用户画像为空，显示引导对话框")
            
            # 显示用户画像对话框
            dialog = UserProfileDialog(self.db, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.logger.info("用户画像已设置")
            else:
                self.logger.info("用户跳过了画像设置")


