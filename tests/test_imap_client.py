# tests/test_imap_client.py
"""
IMAP客户端模块测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.core.imap_client import IMAPClient, EmailData


class TestIMAPClient:
    """IMAP客户端测试类"""
    
    def test_client_init(self):
        """测试客户端初始化"""
        client = IMAPClient()
        assert client.connection is None
        assert client.current_folder is None
        assert not client.is_connected()
    
    @patch('imaplib.IMAP4_SSL')
    def test_connect_success(self, mock_imap):
        """测试成功连接"""
        mock_connection = Mock()
        mock_imap.return_value = mock_connection
        
        client = IMAPClient()
        result = client.connect('imap.example.com', 993, 'test@example.com', 'authcode')
        
        assert result is True
        assert client.is_connected()
        mock_connection.login.assert_called_once_with('test@example.com', 'authcode')
    
    @patch('imaplib.IMAP4_SSL')
    def test_connect_failure(self, mock_imap):
        """测试连接失败"""
        import imaplib
        mock_imap.side_effect = imaplib.IMAP4.error(b"Authentication failed")
        
        client = IMAPClient()
        result = client.connect('imap.example.com', 993, 'test@example.com', 'wrongcode')
        
        assert result is False
        assert not client.is_connected()
    
    def test_disconnect(self):
        """测试断开连接"""
        client = IMAPClient()
        mock_connection = Mock()
        client.connection = mock_connection
        client.logged_in = True
        
        client.disconnect()
        
        assert client.connection is None
        assert not client.logged_in
    
    @patch('imaplib.IMAP4_SSL')
    def test_list_folders(self, mock_imap):
        """测试列出文件夹"""
        mock_connection = Mock()
        mock_connection.noop.return_value = True
        mock_connection.list.return_value = ('OK', [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Sent"',
            b'(\\HasChildren) "/" "Work"',
        ])
        mock_imap.return_value = mock_connection
        
        client = IMAPClient()
        client.connect('imap.example.com', 993, 'test@example.com', 'authcode')
        folders = client.list_folders()
        
        assert len(folders) == 3
        assert 'INBOX' in folders
        assert 'Sent' in folders
    
    @patch('imaplib.IMAP4_SSL')
    def test_select_folder(self, mock_imap):
        """测试选择文件夹"""
        mock_connection = Mock()
        mock_connection.noop.return_value = True
        mock_connection.select.return_value = ('OK', [b'100'])
        mock_imap.return_value = mock_connection
        
        client = IMAPClient()
        client.connect('imap.example.com', 993, 'test@example.com', 'authcode')
        result = client.select_folder('INBOX')
        
        assert result is True
        assert client.current_folder == 'INBOX'
    
    @patch('imaplib.IMAP4_SSL')
    def test_select_folder_failure(self, mock_imap):
        """测试选择文件夹失败"""
        mock_connection = Mock()
        mock_connection.noop.return_value = True
        mock_connection.select.return_value = ('NO', [b'Folder not found'])
        mock_imap.return_value = mock_connection
        
        client = IMAPClient()
        client.connect('imap.example.com', 993, 'test@example.com', 'authcode')
        result = client.select_folder('InvalidFolder')
        
        assert result is False


class TestEmailData:
    """邮件数据测试类"""
    
    def test_email_data_creation(self):
        """测试邮件数据对象创建"""
        email = EmailData(
            uid='12345',
            subject='Test Subject',
            sender='Sender',
            sender_email='sender@example.com',
            recipients='test@example.com',
            date=datetime.now(),
            body_text='Test body',
            folder='INBOX'
        )
        
        assert email.uid == '12345'
        assert email.subject == 'Test Subject'
        assert email.is_read is False


class TestIMAPServerConfig:
    """IMAP服务器配置测试"""
    
    def test_known_servers(self):
        """测试已知服务器配置"""
        client = IMAPClient()
        
        # QQ邮箱
        assert 'qq.com' in client.IMAP_SERVERS['qq']['server']
        assert client.IMAP_SERVERS['qq']['port'] == 993
        
        # 163邮箱
        assert '163.com' in client.IMAP_SERVERS['163']['server']
        
        # Gmail
        assert 'gmail.com' in client.IMAP_SERVERS['gmail']['server']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
