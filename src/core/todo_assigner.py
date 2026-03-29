# src/core/todo_assigner.py
"""
待办归属判断模块
结合用户画像和邮件内容，判断待办事项的归属
"""

import json
import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from ..data.database import Database
from ..data.user_profile_repo import UserProfileRepo
from .ai_bridge import AIBridge, AIProvider


@dataclass
class AssignmentResult:
    """归属判断结果"""
    assignee: str  # 归属人姓名
    assign_type: str  # 'self' / 'other' / 'team' / 'unknown'
    confidence: float  # 0.0 - 1.0
    assign_reason: str  # 判断理由
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


class TodoAssigner:
    """
    待办归属判断器
    
    判断逻辑：
    1. 检查收件人：用户邮箱是否在 To/Cc
    2. 分析内容：是否包含用户名/别名
    3. 结合用户画像：工作职责是否匹配
    4. AI 综合判断：归属类型 + 置信度
    """
    
    # 归属判断的系统提示词
    ASSIGNMENT_PROMPT = """你是一个待办事项分析助手。请判断以下待办事项的归属。

【用户信息】
- 姓名：{user_name}
- 部门：{department}
- 职位：{role}
- 工作描述：{work_description}
- 邮箱：{user_email}

【邮件信息】
- 收件人：{recipients}
- 抄送人：{cc}
- 发件人：{sender}
- 待办内容：{todo_content}

【邮件原文片段】
{email_body}

请判断这个待办事项是否属于该用户：
1. 如果邮件直接发给用户或抄送给用户
2. 如果邮件内容中提到了用户的名字或职位
3. 如果待办内容与用户的工作职责相关

返回 JSON：
{{
    "assignee": "归属人姓名或 '未知'",
    "assign_type": "self/other/team/unknown",
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}}

只返回 JSON，不要有其他内容。"""

    def __init__(self, db: Database):
        """
        初始化待办归属判断器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.profile_repo = UserProfileRepo(db)
        self.ai_bridge = AIBridge(db)
        self.logger = logging.getLogger(__name__)
    
    def analyze_assignment(
        self,
        todo_content: str,
        email_recipients: List[str],
        email_cc: List[str],
        email_sender: str,
        email_body: str
    ) -> AssignmentResult:
        """
        分析待办归属
        
        Args:
            todo_content: 待办事项内容
            email_recipients: 收件人列表
            email_cc: 抄送人列表
            email_sender: 发件人
            email_body: 邮件正文
            
        Returns:
            AssignmentResult 归属判断结果
        """
        try:
            # 1. 获取用户画像
            profile = self.profile_repo.get_profile()
            user_email = self.profile_repo.get_user_email()
            
            # 如果用户画像为空，返回 unknown
            if self.profile_repo.is_profile_empty():
                return AssignmentResult(
                    assignee="未知",
                    assign_type="unknown",
                    confidence=0.0,
                    assign_reason="用户画像未配置",
                    success=True
                )
            
            user_name = profile.get('name', '')
            department = profile.get('department', '')
            role = profile.get('role', '')
            work_description = profile.get('work_description', '')
            
            # 2. 快速规则判断（无需 AI）
            quick_result = self._quick_assignment_check(
                todo_content=todo_content,
                user_name=user_name,
                user_email=user_email,
                recipients=email_recipients,
                cc=email_cc,
                email_body=email_body,
                role=role,
                work_description=work_description
            )
            
            if quick_result:
                return quick_result
            
            # 3. AI 综合判断
            return self._ai_assignment_check(
                todo_content=todo_content,
                user_name=user_name,
                department=department,
                role=role,
                work_description=work_description,
                user_email=user_email,
                recipients=email_recipients,
                cc=email_cc,
                sender=email_sender,
                email_body=email_body
            )
            
        except Exception as e:
            self.logger.error(f"归属判断失败: {e}")
            return AssignmentResult(
                assignee="未知",
                assign_type="unknown",
                confidence=0.0,
                assign_reason="判断过程出错",
                success=False,
                error=str(e)
            )
    
    def _quick_assignment_check(
        self,
        todo_content: str,
        user_name: str,
        user_email: str,
        recipients: List[str],
        cc: List[str],
        email_body: str,
        role: str,
        work_description: str
    ) -> Optional[AssignmentResult]:
        """
        快速规则判断（无需 AI）
        
        Returns:
            如果能快速判断则返回结果，否则返回 None
        """
        all_recipients = recipients + cc
        email_lower = email_body.lower()
        
        # 规则 0: 排除常见非人名词汇
        exclude_words = {
            '本周', '下周', '本周周报', '产品经理', '部门', '团队',
            '请准备', '请完成', '请相关', '相关人员', '负责人',
            '需要', '进行', '完成', '准备', '分析', '设计'
        }
        
        # 规则 1: 用户是收件人或抄送人
        is_direct_recipient = user_email and user_email in all_recipients
        
        # 规则 2: 邮件中明确提及用户姓名
        name_mentioned = user_name and user_name in email_body
        
        # 规则 3: 提及其他人姓名（过滤非人名词汇）
        name_pattern = r'[\u4e00-\u9fa5]{2,3}'
        all_names = re.findall(name_pattern, email_body)
        other_names = [n for n in all_names if n != user_name and n not in exclude_words]
        
        # 判断逻辑
        
        # 优先级 1: 用户是收件人 + 姓名被提及 → 归属自己
        if is_direct_recipient and name_mentioned:
            return AssignmentResult(
                assignee=user_name,
                assign_type="self",
                confidence=0.95,
                assign_reason=f"邮件直接发送给用户，且正文中提及姓名 '{user_name}'"
            )
        
        # 优先级 2: 用户是收件人 + 职责相关 → 归属自己
        if is_direct_recipient and work_description:
            keywords = work_description.replace('，', ' ').replace('、', ' ').split()
            todo_keywords = [kw for kw in keywords if kw in todo_content]
            if todo_keywords:
                return AssignmentResult(
                    assignee=user_name,
                    assign_type="self",
                    confidence=0.85,
                    assign_reason=f"邮件发送给用户，待办内容与职责匹配（{'、'.join(todo_keywords)}）"
                )
        
        # 优先级 3: 用户是收件人 + 无其他人名 → 归属自己
        if is_direct_recipient and len(other_names) == 0:
            return AssignmentResult(
                assignee=user_name,
                assign_type="self",
                confidence=0.80,
                assign_reason="邮件直接发送给用户，且未提及其他人"
            )
        
        # 优先级 4: 姓名被提及 + 无其他人名 → 归属自己
        if name_mentioned and len(other_names) == 0:
            return AssignmentResult(
                assignee=user_name,
                assign_type="self",
                confidence=0.75,
                assign_reason=f"邮件内容中明确提及用户姓名 '{user_name}'"
            )
        
        # 优先级 5: 职责匹配（团队邮件或一般邮件）
        if work_description:
            # 提取关键词（支持中文标点 + 空格分割）
            keywords = re.split(r'[，、,；;和与及]\s*', work_description)
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            
            # 额外提取2-4字的中文关键词（用于未分词的描述）
            chinese_keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', work_description)
            all_keywords = list(set(keywords + chinese_keywords))
            
            # 排除常见无意义词
            exclude_words = {'负责', '需要', '进行', '完成', '准备', '包括', '参与'}
            all_keywords = [kw for kw in all_keywords if kw not in exclude_words and len(kw) >= 2]
            
            # 检查待办内容是否包含职责关键词
            todo_keywords = []
            for kw in all_keywords:
                if kw in todo_content:
                    todo_keywords.append(kw)
            
            # 双向检查：待办中的关键词子串也在职责描述中
            todo_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', todo_content)
            for tw in todo_words:
                # 检查待办词是否在职责描述中（子串匹配）
                if tw in work_description and tw not in exclude_words and tw not in todo_keywords:
                    todo_keywords.append(tw)
                # 反向检查：职责描述中是否包含待办词的部分
                else:
                    for char in tw:
                        if char in work_description and len(tw) >= 2:
                            # 至少有一个共同字，可能有相关性
                            if any(c in work_description for c in tw[:2]):
                                todo_keywords.append(tw)
                                break
            
            # 去重
            todo_keywords = list(set(todo_keywords))
            
            if todo_keywords:
                # 检查是否是团队邮件
                team_keywords = ['team@', 'all@', 'group@', '-team@', '-all@']
                is_team_email = any(kw in ' '.join(recipients).lower() for kw in team_keywords)
                
                return AssignmentResult(
                    assignee=user_name,
                    assign_type="self",
                    confidence=0.75 if is_team_email else 0.70,
                    assign_reason=f"待办内容与用户职责匹配（{'、'.join(todo_keywords)}）"
                )
        
        # 优先级 6: 团队邮件（部门邮箱）
        team_keywords = ['team@', 'all@', 'group@', '-team@', '-all@']
        is_team_email = any(kw in ' '.join(recipients).lower() for kw in team_keywords)
        
        if is_team_email:
            # 团队待办
            return AssignmentResult(
                assignee="团队",
                assign_type="team",
                confidence=0.6,
                assign_reason="团队邮件，属于部门共同待办"
            )
        
        # 优先级 7: 提及其他人 + 用户不是收件人 → 归属他人
        if other_names and not is_direct_recipient:
            return AssignmentResult(
                assignee=other_names[0],
                assign_type="other",
                confidence=0.7,
                assign_reason=f"邮件内容主要提及 '{other_names[0]}'，用户非收件人"
            )
        
        # 优先级 7: 用户是收件人 + 提及其他人（可能是协作）→ 需要 AI 判断
        if is_direct_recipient and other_names:
            # 不返回，交给 AI 判断
            return None
        
        return None
    
    def _ai_assignment_check(
        self,
        todo_content: str,
        user_name: str,
        department: str,
        role: str,
        work_description: str,
        user_email: str,
        recipients: List[str],
        cc: List[str],
        sender: str,
        email_body: str
    ) -> AssignmentResult:
        """
        AI 综合判断
        
        Returns:
            AssignmentResult
        """
        # 构造提示词
        prompt = self.ASSIGNMENT_PROMPT.format(
            user_name=user_name or "未知",
            department=department or "未知",
            role=role or "未知",
            work_description=work_description or "无",
            user_email=user_email or "未知",
            recipients=", ".join(recipients) if recipients else "无",
            cc=", ".join(cc) if cc else "无",
            sender=sender or "未知",
            todo_content=todo_content,
            email_body=email_body[:1000] if email_body else "无"
        )
        
        # 调用 AI（使用 Ollama 或云端 API）
        try:
            if self.ai_bridge.current_provider == AIProvider.OLLAMA:
                # 使用 Ollama
                import requests
                response = requests.post(
                    f"{self.ai_bridge.ollama_config.base_url}/api/generate",
                    json={
                        "model": self.ai_bridge.ollama_config.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 300
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    content = response.json().get("response", "")
                    # 解析 JSON
                    return self._parse_ai_response(content, user_name)
            
            # 如果 AI 不可用或返回 None，返回默认值
            return AssignmentResult(
                assignee=user_name or "未知",
                assign_type="self" if user_email in (recipients + cc) else "unknown",
                confidence=0.5,
                assign_reason="快速规则无法判断，基于收件人信息"
            )
            
        except Exception as e:
            self.logger.warning(f"AI 归属判断失败: {e}")
            # 降级到简单规则
            return AssignmentResult(
                assignee=user_name or "未知",
                assign_type="self" if user_email in (recipients + cc) else "unknown",
                confidence=0.5,
                assign_reason="AI 判断失败，基于简单规则"
            )
    
    def _parse_ai_response(self, content: str, default_name: str) -> AssignmentResult:
        """
        解析 AI 响应
        
        Args:
            content: AI 返回的内容
            default_name: 默认姓名
            
        Returns:
            AssignmentResult
        """
        try:
            # 提取 JSON
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                return AssignmentResult(
                    assignee=data.get("assignee", default_name or "未知"),
                    assign_type=data.get("assign_type", "unknown"),
                    confidence=float(data.get("confidence", 0.5)),
                    assign_reason=data.get("reason", "AI 分析"),
                    success=True
                )
        except Exception as e:
            self.logger.warning(f"解析 AI 响应失败: {e}")
        
        # 解析失败，返回默认值
        return AssignmentResult(
            assignee=default_name or "未知",
            assign_type="unknown",
            confidence=0.5,
            assign_reason="AI 响应解析失败"
        )
    
    def batch_analyze(
        self,
        todos: List[str],
        email_context: Dict[str, Any]
    ) -> List[AssignmentResult]:
        """
        批量分析待办归属
        
        Args:
            todos: 待办事项列表
            email_context: 邮件上下文（recipients, cc, sender, body）
            
        Returns:
            归属判断结果列表
        """
        results = []
        
        for todo in todos:
            result = self.analyze_assignment(
                todo_content=todo,
                email_recipients=email_context.get("recipients", []),
                email_cc=email_context.get("cc", []),
                email_sender=email_context.get("sender", ""),
                email_body=email_context.get("body", "")
            )
            results.append(result)
        
        return results
