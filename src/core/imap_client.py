# src/core/imap_client.py
"""
IMAP客户端模块
封装IMAP连接、邮件获取、解析等功能
"""
import imaplib
import socket
from email import message_from_bytes
from email.header import decode_header
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import logging
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

from src.utils.logger import setup_logger, get_log_dir

logger = setup_logger('imap_client', get_log_dir())

# 设置默认超时时间（秒）
DEFAULT_IMAP_TIMEOUT = 15


@dataclass
class EmailData:
    """邮件数据结构"""
    uid: str
    subject: str
    sender: str
    sender_email: str
    recipients: str
    date: datetime
    body_text: str
    body_html: Optional[str] = None
    folder: str = 'INBOX'
    is_read: bool = False
    cc: Optional[str] = None
    attachments: List[Dict] = field(default_factory=list)


class IMAPClient:
    """IMAP客户端封装类"""
    
    # 常用邮件服务商IMAP配置
    IMAP_SERVERS = {
        'qq': {'server': 'imap.qq.com', 'port': 993},
        '163': {'server': 'imap.163.com', 'port': 993},
        '126': {'server': 'imap.126.com', 'port': 993},
        'gmail': {'server': 'imap.gmail.com', 'port': 993},
        'outlook': {'server': 'outlook.office365.com', 'port': 993},
    }
    
    def __init__(self):
        """初始化IMAP客户端"""
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.current_folder: Optional[str] = None
        self.email_server: Optional[str] = None
        self.logged_in: bool = False
    
    def connect(self, server: str, port: int, email_addr: str, auth_code: str, timeout: int = DEFAULT_IMAP_TIMEOUT) -> bool:
        """
        连接到IMAP服务器
        
        Args:
            server: IMAP服务器地址
            port: 端口（默认993）
            email_addr: 邮箱地址
            auth_code: 授权码（非登录密码）
            timeout: 连接超时时间（秒）
        
        Returns:
            连接是否成功
        """
        try:
            logger.info(f"Connecting to {server}:{port} as {email_addr} (timeout={timeout}s)")
            
            # 设置 socket 超时
            socket.setdefaulttimeout(timeout)
            
            # 创建 SSL 连接
            self.connection = imaplib.IMAP4_SSL(server, port)
            
            # 登录
            result = self.connection.login(email_addr, auth_code)
            logger.info(f"Login response: {result}")
            
            self.email_server = server
            self.logged_in = True
            logger.info("IMAP connection successful")
            return True
            
        except socket.timeout:
            logger.error(f"IMAP connection timeout after {timeout} seconds")
            self._cleanup()
            return False
        except imaplib.IMAP4.error as e:
            error_msg = str(e).replace(b'\n', b' ').decode('utf-8', errors='ignore') if isinstance(e, bytes) else str(e)
            logger.error(f"IMAP authentication failed: {error_msg}")
            self._cleanup()
            return False
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {server}: {e}")
            self._cleanup()
            return False
        except ConnectionRefusedError:
            logger.error(f"Connection refused by {server}:{port}")
            self._cleanup()
            return False
        except Exception as e:
            logger.error(f"IMAP connection failed: {type(e).__name__}: {e}")
            self._cleanup()
            return False
    
    def connect_by_email(self, email_addr: str, auth_code: str) -> bool:
        """
        根据邮箱地址自动识别服务器并连接
        
        Args:
            email_addr: 邮箱地址
            auth_code: 授权码
        
        Returns:
            连接是否成功
        """
        # 从邮箱地址提取域名判断服务商
        domain = email_addr.split('@')[1].lower() if '@' in email_addr else ''
        
        # 匹配服务商
        for name, config in self.IMAP_SERVERS.items():
            if name in domain or domain.endswith(name + '.com'):
                return self.connect(
                    config['server'], 
                    config['port'], 
                    email_addr, 
                    auth_code
                )
        
        logger.warning(f"Unknown email domain: {domain}, cannot auto-configure IMAP")
        return False
    
    def disconnect(self):
        """断开IMAP连接"""
        self._cleanup()
        logger.info("IMAP disconnected")
    
    def _cleanup(self):
        """清理连接状态"""
        if self.connection:
            try:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection.logout()
            except Exception as e:
                logger.debug(f"Cleanup error: {e}")
            finally:
                self.connection = None
                self.current_folder = None
                self.email_server = None
                self.logged_in = False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        if not self.connection or not self.logged_in:
            return False
        try:
            # 发送NOOP命令检查连接
            self.connection.noop()
            return True
        except:
            self._cleanup()
            return False
    
    def list_folders(self) -> List[str]:
        """
        列出所有文件夹
        
        Returns:
            文件夹名称列表
        """
        if not self.is_connected():
            return []
        
        try:
            _, folders = self.connection.list()
            folder_list = []
            for folder in folders:
                if not folder:
                    continue
                # 解析文件夹名称
                decoded = folder.decode('utf-8', errors='replace')
                # 格式: b'(\\HasNoChildren) "/" "INBOX"'
                parts = decoded.split('"')
                if len(parts) >= 2:
                    folder_name = parts[-2].strip()
                    if folder_name:
                        folder_list.append(folder_name)
            logger.info(f"Found {len(folder_list)} folders")
            return folder_list
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            return []
    
    def select_folder(self, folder: str = 'INBOX') -> bool:
        """
        选择文件夹
        
        Args:
            folder: 文件夹名称
        
        Returns:
            选择是否成功
        """
        if not self.is_connected():
            return False
        
        try:
            status, _ = self.connection.select(f'"{folder}"' if ' ' in folder else folder)
            if status == 'OK':
                self.current_folder = folder
                logger.info(f"Selected folder: {folder}")
                return True
            else:
                logger.error(f"Failed to select folder {folder}: {status}")
                return False
        except Exception as e:
            logger.error(f"Error selecting folder {folder}: {e}")
            return False
    
    def get_folder_info(self) -> Dict:
        """
        获取当前文件夹信息
        
        Returns:
            文件夹信息字典
        """
        if not self.is_connected() or not self.current_folder:
            return {}
        
        try:
            status, data = self.connection.status(
                f'"{self.current_folder}"', 
                '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)'
            )
            if status == 'OK' and data:
                info = {}
                # 解析状态信息
                for item in data:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8', errors='replace')
                    parts = item.split()
                    for i, part in enumerate(parts):
                        if part == 'MESSAGES':
                            info['messages'] = int(parts[i + 1].rstrip(')'))
                        elif part == 'RECENT':
                            info['recent'] = int(parts[i + 1].rstrip(')'))
                        elif part == 'UIDNEXT':
                            info['uidnext'] = int(parts[i + 1].rstrip(')'))
                        elif part == 'UIDVALIDITY':
                            info['uidvalidity'] = int(parts[i + 1].rstrip(')'))
                        elif part == 'UNSEEN':
                            info['unseen'] = int(parts[i + 1].rstrip(')'))
                return info
        except Exception as e:
            logger.error(f"Error getting folder info: {e}")
        return {}
    
    def fetch_emails(
        self,
        since_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[EmailData]:
        """
        获取邮件列表
        
        Args:
            since_date: 起始日期（可选）
            before_date: 结束日期（可选）
            limit: 最多获取数量
            unread_only: 只获取未读邮件
        
        Returns:
            邮件列表
        """
        if not self.is_connected() or not self.current_folder:
            return []
        
        try:
            # 构建搜索条件
            search_criteria = []
            
            if unread_only:
                search_criteria.append('UNSEEN')
            elif since_date or before_date:
                # 日期条件
                if since_date:
                    search_criteria.append(f'SINCE {since_date.strftime("%d-%b-%Y")}')
                if before_date:
                    search_criteria.append(f'BEFORE {before_date.strftime("%d-%b-%Y")}')
            
            if not search_criteria:
                search_criteria = ['ALL']
            
            # 执行搜索
            _, search_result = self.connection.search(None, *search_criteria)
            email_ids = search_result[0].split() if search_result else []
            
            # 限制数量（取最新的）
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]
            
            logger.info(f"Found {len(email_ids)} emails matching criteria")
            
            # 获取邮件详情
            emails = []
            for email_id in email_ids:
                email_data = self._fetch_single_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def fetch_email_by_uid(self, uid: str) -> Optional[EmailData]:
        """
        根据UID获取单封邮件
        
        Args:
            uid: 邮件UID
        
        Returns:
            邮件数据对象
        """
        if not self.is_connected():
            return None
        
        try:
            _, msg_data = self.connection.uid('FETCH', uid, '(RFC822)')
            if msg_data and msg_data[0]:
                raw_email = msg_data[0][1]
                return self._parse_email(uid, raw_email)
        except Exception as e:
            logger.error(f"Error fetching email by UID {uid}: {e}")
        return None
    
    def _fetch_single_email(self, email_id: bytes) -> Optional[EmailData]:
        """获取单封邮件详情"""
        try:
            _, msg_data = self.connection.fetch(email_id, '(RFC822)')
            if msg_data and msg_data[0]:
                raw_email = msg_data[0][1]
                uid = email_id.decode()
                return self._parse_email(uid, raw_email)
        except Exception as e:
            logger.error(f"Error fetching single email: {e}")
        return None
    
    def _parse_email(self, uid: str, raw_email: bytes) -> Optional[EmailData]:
        """解析邮件内容"""
        try:
            msg = message_from_bytes(raw_email)
            
            # 解析主题
            subject = self._decode_header(msg.get('Subject', ''))
            
            # 解析发件人
            sender_raw = msg.get('From', '')
            sender, sender_email = self._parse_address(sender_raw)
            
            # 解析收件人和抄送
            recipients = self._decode_header(msg.get('To', ''))
            cc = self._decode_header(msg.get('Cc', ''))
            
            # 解析日期
            date_str = msg.get('Date', '')
            date = self._parse_date(date_str)
            
            # 解析正文
            body_text, body_html = self._parse_body(msg)
            
            # 检查是否已读
            is_read = False
            # 尝试从FLAGS获取
            try:
                _, flags_data = self.connection.fetch(email_id if isinstance(email_id, bytes) else email_id.encode(), '(FLAGS)')
                if flags_data:
                    flags_str = flags_data[0].decode() if isinstance(flags_data[0], bytes) else str(flags_data[0])
                    is_read = 'SEEN' in flags_str.upper()
            except:
                pass
            
            return EmailData(
                uid=uid,
                subject=subject,
                sender=sender,
                sender_email=sender_email,
                recipients=recipients,
                date=date,
                body_text=body_text,
                body_html=body_html,
                folder=self.current_folder or 'INBOX',
                is_read=is_read,
                cc=cc if cc else None
            )
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """解码邮件头（支持多种编码）"""
        if not header:
            return ''
        
        decoded_parts = []
        try:
            parts = decode_header(header)
            for content, charset in parts:
                if isinstance(content, bytes):
                    charset = charset or 'utf-8'
                    try:
                        decoded_parts.append(content.decode(charset))
                    except:
                        decoded_parts.append(content.decode('utf-8', errors='replace'))
                elif content:
                    decoded_parts.append(content)
        except Exception:
            return header
        
        return ''.join(decoded_parts).strip()
    
    def _parse_address(self, address_raw: str) -> Tuple[str, str]:
        """解析邮件地址"""
        if not address_raw:
            return ('', '')
        
        try:
            # 格式: "显示名称 <email@example.com>"
            if '<' in address_raw and '>' in address_raw:
                name = address_raw.split('<')[0].strip().strip('"').strip()
                email = address_raw.split('<')[1].split('>')[0].strip()
                return (name, email)
            elif '@' in address_raw:
                return (address_raw, address_raw)
        except Exception:
            pass
        
        return (address_raw, '')
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析邮件日期"""
        if not date_str:
            return datetime.now()
        
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
        
        # 备用解析
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%d %b %Y %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return datetime.now()
    
    def _parse_body(self, msg) -> Tuple[str, str]:
        """解析邮件正文"""
        body_text = ''
        body_html = ''
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # 忽略附件
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain' and not body_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='replace').strip()
                
                elif content_type == 'text/html' and not body_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_html = payload.decode(charset, errors='replace').strip()
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                content_type = msg.get_content_type()
                
                if content_type == 'text/html':
                    body_html = payload.decode(charset, errors='replace').strip()
                else:
                    body_text = payload.decode(charset, errors='replace').strip()
        
        return (body_text, body_html)
