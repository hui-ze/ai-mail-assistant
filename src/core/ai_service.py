# src/core/ai_service.py
"""
AI服务层模块
封装AI摘要生成和待办提取的业务逻辑
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..data.database import Database
from ..data.email_repo import EmailRepo
from ..data.summary_repo import SummaryRepo, SummaryResult
from ..data.todo_repo import TodoRepo
from .ai_bridge import AIBridge, SummaryResult as AISummaryResult
from .todo_assigner import TodoAssigner, AssignmentResult


class AIService:
    """
    AI服务类
    
    负责协调AI桥接器和数据仓储，提供完整的摘要生成和待办提取功能
    """

    def __init__(self, db: Database):
        """
        初始化AI服务
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.ai_bridge = AIBridge(db)
        self.email_repo = EmailRepo(db)
        self.summary_repo = SummaryRepo(db)
        self.todo_repo = TodoRepo(db)
        self.todo_assigner = TodoAssigner(db)  # 新增：待办归属判断器
        self.logger = logging.getLogger(__name__)

    def generate_email_summary(self, email_id: int, force: bool = False) -> Dict[str, Any]:
        """
        生成邮件摘要
        
        Args:
            email_id: 邮件ID
            force: 是否强制重新生成
        
        Returns:
            结果字典，包含success、summary、error等字段
        """
        # 检查是否已有摘要
        if not force:
            existing = self.summary_repo.get_summary_by_email_id(email_id)
            if existing:
                self.logger.info(f"邮件 {email_id} 已有摘要，使用缓存")
                # 将 SummaryResult 对象转换为字典格式
                return {
                    'success': True,
                    'summary': {
                        'id': existing.id,
                        'email_id': existing.email_id,
                        'summary_text': existing.summary_text,
                        'todos': json.loads(existing.todos_json) if existing.todos_json else [],
                        'model_used': existing.model_used,
                        'tokens_used': existing.tokens_used
                    },
                    'cached': True,
                    'todo_count': len(json.loads(existing.todos_json)) if existing.todos_json else 0
                }

        # 获取邮件内容
        email = self.email_repo.get_email_by_id(email_id)
        if not email:
            return {
                'success': False,
                'error': '邮件不存在'
            }

        # 调用AI生成摘要
        self.logger.info(f"正在为邮件 {email_id} 生成摘要...")
        
        # 支持字典和对象两种访问方式
        subject = email['subject'] if isinstance(email, dict) else email.subject
        body = email.get('body_text', email.get('body', '')) if isinstance(email, dict) else email.body
        
        ai_result = self.ai_bridge.generate_summary(
            subject,
            body
        )

        if not ai_result.success:
            return {
                'success': False,
                'error': ai_result.error or 'AI生成失败'
            }

        # 保存摘要到数据库
        summary_id = self.summary_repo.save_summary(
            email_id=email_id,
            summary_text=ai_result.summary,
            todos_json=json.dumps(ai_result.todos),
            model_used=ai_result.model_used,
            tokens_used=ai_result.tokens_used
        )

        # 提取待办事项
        todo_count = 0
        if ai_result.todos:
            # 获取邮件收件人信息（用于归属判断）
            email_to = email.get('recipients', '') if isinstance(email, dict) else getattr(email, 'recipients', '')
            email_cc = email.get('cc', '') if isinstance(email, dict) else getattr(email, 'cc', '')
            email_sender = email.get('sender', '') if isinstance(email, dict) else getattr(email, 'sender', '')
            
            # 解析收件人列表
            recipients = [r.strip() for r in email_to.split(',') if r.strip()]
            cc_list = [c.strip() for c in email_cc.split(',') if c.strip()]
            
            for todo_text in ai_result.todos:
                # 归属判断
                assignment = self.todo_assigner.analyze_assignment(
                    todo_content=todo_text,
                    email_recipients=recipients,
                    email_cc=cc_list,
                    email_sender=email_sender,
                    email_body=body
                )
                
                # 创建待办并设置归属信息
                self.todo_repo.create_todo(
                    content=todo_text,
                    email_id=email_id,
                    summary_id=summary_id,
                    priority='中',
                    assignee=assignment.assignee,
                    assign_type=assignment.assign_type,
                    confidence=assignment.confidence,
                    assign_reason=assignment.assign_reason
                )
                todo_count += 1

        self.logger.info(f"邮件 {email_id} 摘要生成完成，待办事项: {todo_count}")

        return {
            'success': True,
            'summary': {
                'id': summary_id,
                'email_id': email_id,
                'summary_text': ai_result.summary,
                'todos': ai_result.todos,
                'model_used': ai_result.model_used,
                'tokens_used': ai_result.tokens_used
            },
            'todo_count': todo_count,
            'cached': False
        }

    def extract_todos_from_email(self, email_id: int) -> Dict[str, Any]:
        """
        从邮件中提取待办事项
        
        Args:
            email_id: 邮件ID
        
        Returns:
            结果字典
        """
        email = self.email_repo.get_email_by_id(email_id)
        if not email:
            return {
                'success': False,
                'error': '邮件不存在'
            }

        # 提取待办
        # 支持字典和对象两种访问方式
        subject = email['subject'] if isinstance(email, dict) else email.subject
        body = email.get('body_text', email.get('body', '')) if isinstance(email, dict) else email.body
        
        todos = self.ai_bridge.extract_todos(subject, body)

        # 保存待办到数据库
        saved_count = 0
        for todo_text in todos:
            self.todo_repo.create_todo(
                content=todo_text,
                email_id=email_id,
                priority='中'
            )
            saved_count += 1

        return {
            'success': True,
            'todos': todos,
            'saved_count': saved_count
        }

    def get_email_summary(self, email_id: int) -> Optional[SummaryResult]:
        """
        获取邮件摘要
        
        Args:
            email_id: 邮件ID
        
        Returns:
            SummaryResult对象或None
        """
        return self.summary_repo.get_summary_by_email_id(email_id)

    def get_email_todos(self, email_id: int) -> List:
        """
        获取邮件关联的待办事项
        
        Args:
            email_id: 邮件ID
        
        Returns:
            待办事项列表
        """
        return self.todo_repo.get_todos_by_email_id(email_id)

    def batch_generate_summaries(self, account_id: int = None, limit: int = 10) -> Dict[str, Any]:
        """
        批量生成未处理邮件的摘要
        
        Args:
            account_id: 账号ID（可选）
            limit: 处理的邮件数量限制
        
        Returns:
            结果字典
        """
        # 获取未处理的邮件
        if account_id:
            emails = self.email_repo.get_unprocessed_emails(account_id, limit)
        else:
            emails = self.email_repo.get_all_unprocessed_emails(limit)

        if not emails:
            return {
                'success': True,
                'processed': 0,
                'message': '没有需要处理的邮件'
            }

        success_count = 0
        failed_count = 0
        errors = []

        for email in emails:
            try:
                result = self.generate_email_summary(email.id)
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"邮件 {email.id}: {result.get('error')}")
            except Exception as e:
                failed_count += 1
                errors.append(f"邮件 {email.id}: {str(e)}")
                self.logger.error(f"处理邮件 {email.id} 失败: {e}")

        return {
            'success': True,
            'processed': success_count + failed_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }

    def get_ai_status(self) -> Dict[str, Any]:
        """
        获取AI服务状态
        
        Returns:
            状态字典
        """
        is_available = self.ai_bridge.is_available()
        provider = self.ai_bridge.get_current_provider()
        stats = self.ai_bridge.get_usage_stats()

        # 获取可用模型（如果是Ollama）
        models = []
        if provider == 'ollama':
            models = self.ai_bridge.get_available_models()

        return {
            'available': is_available,
            'provider': provider,
            'models': models,
            'stats': stats
        }

    def configure_ollama(self, base_url: str = None, model: str = None):
        """配置Ollama"""
        self.ai_bridge.configure_ollama(base_url, model)

    def configure_cloud(self, provider, api_key: str, model: str = None):
        """配置云端API"""
        self.ai_bridge.configure_cloud(provider, api_key, model)
