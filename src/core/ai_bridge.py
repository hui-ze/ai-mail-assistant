# src/core/ai_bridge.py
"""
AI处理器桥接器模块
提供统一的AI接口，支持本地Ollama和云端API
"""
import json
import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

from ..data.database import Database


class AIProvider(Enum):
    """AI提供商枚举"""
    OLLAMA = "ollama"
    WENXIN = "wenxin"  # 百度文心
    QIANWEN = "qianwen"  # 阿里通义
    DEEPSEEK = "deepseek"  # DeepSeek
    NONE = "none"  # 无AI服务


@dataclass
class SummaryResult:
    """AI摘要生成结果"""
    summary: str
    todos: List[str]
    model_used: str
    tokens_used: int
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class OllamaConfig:
    """Ollama配置"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:8b"  # 默认使用 qwen3:8b（用户已安装）
    timeout: int = 120


@dataclass
class CloudAPIConfig:
    """云端API配置"""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout: int = 60


class OllamaProcessor:
    """Ollama本地模型处理器"""

    SYSTEM_PROMPT = """你是一个专业的邮件助手。请分析以下邮件内容，生成：
1. 简洁的中文摘要（50-100字）
2. 识别出的待办事项列表

请以JSON格式返回，格式如下：
{
    "summary": "摘要内容",
    "todos": ["待办1", "待办2", ...]
}

只返回JSON，不要有其他内容。"""

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama服务不可用: {e}")
            return False

    def generate_summary(self, subject: str, body: str) -> SummaryResult:
        """生成邮件摘要"""
        try:
            # 构造提示
            prompt = f"邮件主题: {subject}\n\n邮件内容:\n{body[:2000]}"

            # 调用Ollama API
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": f"{self.SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500
                    }
                },
                timeout=self.config.timeout
            )

            if response.status_code != 200:
                return SummaryResult(
                    summary="",
                    todos=[],
                    model_used=self.config.model,
                    tokens_used=0,
                    success=False,
                    error=f"Ollama API错误: {response.status_code}"
                )

            result = response.json()
            content = result.get("response", "")

            # 解析JSON响应
            try:
                # 尝试提取JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    return SummaryResult(
                        summary=data.get("summary", content),
                        todos=data.get("todos", []),
                        model_used=self.config.model,
                        tokens_used=result.get("eval_count", 0),
                        success=True
                    )
                else:
                    # 没有找到JSON，返回原始内容作为摘要
                    return SummaryResult(
                        summary=content[:500],
                        todos=[],
                        model_used=self.config.model,
                        tokens_used=result.get("eval_count", 0),
                        success=True
                    )
            except json.JSONDecodeError:
                return SummaryResult(
                    summary=content[:500],
                    todos=[],
                    model_used=self.config.model,
                    tokens_used=result.get("eval_count", 0),
                    success=True
                )

        except requests.exceptions.Timeout:
            return SummaryResult(
                summary="",
                todos=[],
                model_used=self.config.model,
                tokens_used=0,
                success=False,
                error="请求超时，请检查Ollama服务状态"
            )
        except Exception as e:
            self.logger.error(f"Ollama生成摘要失败: {e}")
            return SummaryResult(
                summary="",
                todos=[],
                model_used=self.config.model,
                tokens_used=0,
                success=False,
                error=str(e)
            )


class CloudAPIProcessor:
    """云端API处理器（文心/通义/DeepSeek）"""

    def __init__(self, provider: AIProvider, config: CloudAPIConfig):
        self.provider = provider
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 设置API端点
        self.endpoints = {
            AIProvider.WENXIN: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
            AIProvider.QIANWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            AIProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions"
        }

    def is_available(self) -> bool:
        """检查云端API是否可用"""
        return bool(self.config.api_key)

    def generate_summary(self, subject: str, body: str) -> SummaryResult:
        """生成邮件摘要"""
        if not self.config.api_key:
            return SummaryResult(
                summary="",
                todos=[],
                model_used=self.config.model,
                tokens_used=0,
                success=False,
                error="API密钥未配置"
            )

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }

            prompt = f"""你是一个专业的邮件助手。请分析以下邮件内容，生成：
1. 简洁的中文摘要（50-100字）
2. 识别出的待办事项列表

请以JSON格式返回，格式如下：
{{
    "summary": "摘要内容",
    "todos": ["待办1", "待办2", ...]
}}

邮件主题: {subject}
邮件内容:
{body[:2000]}

只返回JSON，不要有其他内容。"""

            payload = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500
            }

            response = requests.post(
                self.endpoints.get(self.provider, ""),
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code != 200:
                return SummaryResult(
                    summary="",
                    todos=[],
                    model_used=self.config.model,
                    tokens_used=0,
                    success=False,
                    error=f"API错误: {response.status_code} - {response.text}"
                )

            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 解析JSON响应
            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    return SummaryResult(
                        summary=data.get("summary", content),
                        todos=data.get("todos", []),
                        model_used=self.config.model,
                        tokens_used=result.get("usage", {}).get("total_tokens", 0),
                        success=True
                    )
            except json.JSONDecodeError:
                pass

            return SummaryResult(
                summary=content[:500],
                todos=[],
                model_used=self.config.model,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                success=True
            )

        except Exception as e:
            self.logger.error(f"云端API生成摘要失败: {e}")
            return SummaryResult(
                summary="",
                todos=[],
                model_used=self.config.model,
                tokens_used=0,
                success=False,
                error=str(e)
            )


class AIBridge:
    """
    AI处理器桥接器

    统一接口，支持多种AI后端：
    - 本地Ollama模型（免费）
    - 云端API（付费功能）
    """

    def __init__(self, db: Optional[Database] = None):
        """
        初始化AI桥接器

        Args:
            db: 数据库实例（可选，用于存储使用统计）
        """
        self.db = db
        self.current_provider = AIProvider.NONE
        self.logger = logging.getLogger(__name__)

        # 配置
        self.ollama_config = OllamaConfig()
        self.cloud_config = CloudAPIConfig()

        # 处理器
        self._ollama_processor: Optional[OllamaProcessor] = None
        self._cloud_processor: Optional[CloudAPIProcessor] = None

        # 自动检测可用服务
        self._detect_available_services()

    def _detect_available_services(self):
        """检测可用的AI服务"""
        # 先检查数据库中的配置（优先级最高）
        if self.db:
            settings = self._load_ai_settings()
            if settings:
                provider_name = settings.get("provider", "")
                self.logger.info(f"检测到数据库配置: provider={provider_name}")
                
                if provider_name == "ollama":
                    self.ollama_config.base_url = settings.get("ollama_url", self.ollama_config.base_url)
                    self.ollama_config.model = settings.get("ollama_model", self.ollama_config.model)
                    self._ollama_processor = OllamaProcessor(self.ollama_config)
                    if self._ollama_processor.is_available():
                        self.current_provider = AIProvider.OLLAMA
                        self.logger.info(f"使用数据库配置的Ollama: {self.ollama_config.model}")
                        return
                
                elif provider_name in ["wenxin", "qianwen", "deepseek"]:
                    self.cloud_config.api_key = settings.get("api_key", "")
                    self.cloud_config.base_url = settings.get("base_url", "")
                    self.cloud_config.model = settings.get("model", "")
                    
                    provider_map = {
                        "wenxin": AIProvider.WENXIN,
                        "qianwen": AIProvider.QIANWEN,
                        "deepseek": AIProvider.DEEPSEEK
                    }
                    provider = provider_map.get(provider_name, AIProvider.DEEPSEEK)
                    self._cloud_processor = CloudAPIProcessor(provider, self.cloud_config)
                    if self._cloud_processor.is_available():
                        self.current_provider = provider
                        self.logger.info(f"使用数据库配置的云端API: {provider_name}")
                        return
        
        # 自动检测Ollama（作为后备）
        try:
            self._ollama_processor = OllamaProcessor(self.ollama_config)
            if self._ollama_processor.is_available():
                self.current_provider = AIProvider.OLLAMA
                self.logger.info(f"自动检测到Ollama服务: {self.ollama_config.base_url}")
                return
        except Exception as e:
            self.logger.debug(f"Ollama检测失败: {e}")

    def _load_ai_settings(self) -> Dict[str, Any]:
        """从数据库加载AI设置"""
        if not self.db:
            return {}
        try:
            # 从 ai_settings 表读取
            result = self.db.query_one(
                "SELECT value FROM ai_settings WHERE key = 'ai_settings'"
            )
            if result and result[0]:
                settings = json.loads(result[0])
                self.logger.info(f"从数据库加载AI设置: provider={settings.get('provider')}")
                return settings
        except Exception as e:
            self.logger.error(f"加载AI设置失败: {e}")
        return {}

    def _save_ai_settings(self, settings: Dict[str, Any]):
        """保存AI设置到数据库"""
        if not self.db:
            return
        try:
            # 保存到 ai_settings 表
            self.db.execute(
                "INSERT OR REPLACE INTO ai_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                ("ai_settings", json.dumps(settings))
            )
        except Exception as e:
            self.logger.error(f"保存AI设置失败: {e}")

    def configure_ollama(self, base_url: str = None, model: str = None):
        """配置Ollama"""
        if base_url:
            self.ollama_config.base_url = base_url
        if model:
            self.ollama_config.model = model

        self._ollama_processor = OllamaProcessor(self.ollama_config)

        # 保存设置
        settings = self._load_ai_settings()
        settings.update({
            "provider": "ollama",
            "ollama_url": self.ollama_config.base_url,
            "ollama_model": self.ollama_config.model
        })
        self._save_ai_settings(settings)

        self.current_provider = AIProvider.OLLAMA

    def configure_cloud(self, provider: AIProvider, api_key: str, model: str = None):
        """配置云端API"""
        self.cloud_config.api_key = api_key
        if model:
            self.cloud_config.model = model
        else:
            # 设置默认模型
            defaults = {
                AIProvider.WENXIN: "ernie-4.0-8k-latest",
                AIProvider.QIANWEN: "qwen-plus",
                AIProvider.DEEPSEEK: "deepseek-chat"
            }
            self.cloud_config.model = defaults.get(provider, "gpt-3.5-turbo")
        
        # 设置对应的端点
        endpoints = {
            AIProvider.WENXIN: "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
            AIProvider.QIANWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            AIProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions"
        }
        self.cloud_config.base_url = endpoints.get(provider, "")

        self._cloud_processor = CloudAPIProcessor(provider, self.cloud_config)

        # 保存设置（包含所有必要字段）
        settings = self._load_ai_settings()
        settings.update({
            "provider": provider.value,
            "api_key": api_key,
            "model": self.cloud_config.model,
            "base_url": self.cloud_config.base_url
        })
        self._save_ai_settings(settings)
        
        self.logger.info(f"云端API配置已保存: provider={provider.value}, model={self.cloud_config.model}")

        self.current_provider = provider

    def generate_summary(self, email_subject: str, email_body: str) -> SummaryResult:
        """
        生成邮件摘要

        Args:
            email_subject: 邮件主题
            email_body: 邮件正文

        Returns:
            SummaryResult 摘要结果对象
        """
        if self.current_provider == AIProvider.OLLAMA and self._ollama_processor:
            result = self._ollama_processor.generate_summary(email_subject, email_body)
        elif self.current_provider in [AIProvider.WENXIN, AIProvider.QIANWEN, AIProvider.DEEPSEEK]:
            if self._cloud_processor:
                result = self._cloud_processor.generate_summary(email_subject, email_body)
            else:
                result = SummaryResult(
                    summary="",
                    todos=[],
                    model_used="",
                    tokens_used=0,
                    success=False,
                    error="云端API处理器未初始化"
                )
        else:
            result = SummaryResult(
                summary="",
                todos=[],
                model_used="",
                tokens_used=0,
                success=False,
                error="没有可用的AI服务"
            )

        # 记录使用统计
        if result.success and self.db:
            self._record_usage(result)

        return result

    def extract_todos(self, email_subject: str, email_body: str) -> List[str]:
        """
        从邮件中提取待办事项

        Args:
            email_subject: 邮件主题
            email_body: 邮件正文

        Returns:
            待办事项列表
        """
        result = self.generate_summary(email_subject, email_body)
        return result.todos

    def is_available(self) -> bool:
        """
        检查AI服务是否可用

        Returns:
            True表示可用
        """
        if self.current_provider == AIProvider.OLLAMA:
            return self._ollama_processor is not None and self._ollama_processor.is_available()
        elif self.current_provider in [AIProvider.WENXIN, AIProvider.QIANWEN, AIProvider.DEEPSEEK]:
            return self._cloud_processor is not None and self._cloud_processor.is_available()
        return False

    def set_provider(self, provider: AIProvider):
        """
        设置AI提供商

        Args:
            provider: AI提供商枚举
        """
        self.current_provider = provider

    def get_current_provider(self) -> str:
        """
        获取当前AI提供商名称

        Returns:
            提供商名称字符串
        """
        if self.current_provider == AIProvider.NONE:
            return "none"
        return self.current_provider.value

    def get_available_models(self) -> List[str]:
        """获取Ollama可用模型列表"""
        if not self._ollama_processor:
            return []
        try:
            response = requests.get(
                f"{self.ollama_config.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def get_usage_stats(self) -> dict:
        """
        获取AI使用统计

        Returns:
            使用统计字典
        """
        if not self.db:
            return {
                'total_requests': 0,
                'total_tokens': 0,
                'provider': self.current_provider.value
            }

        try:
            result = self.db.query_one(
                "SELECT COUNT(*), COALESCE(SUM(tokens_used), 0) FROM ai_usage"
            )
            if result:
                return {
                    'total_requests': result[0],
                    'total_tokens': result[1],
                    'provider': self.current_provider.value
                }
        except Exception:
            pass

        return {
            'total_requests': 0,
            'total_tokens': 0,
            'provider': self.current_provider.value
        }

    def _record_usage(self, result: SummaryResult):
        """记录AI使用情况"""
        if not self.db:
            return
        try:
            self.db.execute(
                """INSERT INTO ai_usage 
                (provider, model, tokens_used, success, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))""",
                (self.current_provider.value, result.model_used, result.tokens_used, result.success)
            )
        except Exception as e:
            self.logger.error(f"记录AI使用失败: {e}")
