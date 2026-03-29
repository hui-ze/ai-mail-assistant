# -*- coding: utf-8 -*-
"""
UI模块测试
注意：UI测试需要显示窗口，在无头环境下会跳过
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# 尝试导入PyQt5
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 not available, skipping UI tests")


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not installed")
class TestAddAccountDialog(unittest.TestCase):
    """测试添加账号对话框"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        """设置测试"""
        self.mock_db = MagicMock()

    def test_dialog_creation(self):
        """测试对话框创建"""
        from src.ui.add_account_dialog import AddAccountDialog

        dialog = AddAccountDialog(self.mock_db)
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "添加邮件账号")

    def test_preset_servers(self):
        """测试预设服务器"""
        from src.ui.add_account_dialog import AddAccountDialog

        self.assertIn('QQ邮箱', AddAccountDialog.PRESET_SERVERS)
        self.assertIn('163邮箱', AddAccountDialog.PRESET_SERVERS)
        self.assertIn('Gmail', AddAccountDialog.PRESET_SERVERS)


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not installed")
class TestEmailListDelegate(unittest.TestCase):
    """测试邮件列表委托"""

    def test_size_hint(self):
        """测试尺寸提示"""
        from src.ui.email_list_delegate import EmailListDelegate

        delegate = EmailListDelegate()
        self.assertEqual(delegate.ITEM_HEIGHT, 65)

        # 测试自定义高度
        delegate.setItemHeight(80)
        self.assertEqual(delegate.item_height, 80)


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not installed")
class TestPanels(unittest.TestCase):
    """测试面板组件"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_summary_panel_creation(self):
        """测试摘要面板创建"""
        from src.ui.panels import SummaryPanel
        from src.data.summary_repo import SummaryRepo

        mock_repo = MagicMock(spec=SummaryRepo)
        panel = SummaryPanel(mock_repo)

        self.assertIsNotNone(panel)
        self.assertIsNotNone(panel.summary_text)

    def test_todo_panel_creation(self):
        """测试待办面板创建"""
        from src.ui.panels import TodoPanel
        from src.data.todo_repo import TodoRepo

        mock_repo = MagicMock(spec=TodoRepo)
        panel = TodoPanel(mock_repo)

        self.assertIsNotNone(panel)
        self.assertIsNotNone(panel.todo_list)


class TestImports(unittest.TestCase):
    """测试导入"""

    def test_import_ui_module(self):
        """测试UI模块导入"""
        # 只测试导入，不测试实际UI创建
        import src.ui
        self.assertTrue(hasattr(src.ui, '__all__'))


if __name__ == '__main__':
    unittest.main()
