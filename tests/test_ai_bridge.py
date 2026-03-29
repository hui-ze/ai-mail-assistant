# -*- coding: utf-8 -*-
"""
AI桥接器模块测试
"""

import unittest
from unittest.mock import MagicMock, patch


class TestAIBridge(unittest.TestCase):
    """测试AIBridge"""

    def test_bridge_creation(self):
        """测试桥接器创建"""
        from src.core.ai_bridge import AIBridge, AIProvider

        bridge = AIBridge(db=None)
        self.assertIsNotNone(bridge)
        self.assertIsNotNone(bridge.current_provider)

    def test_provider_enum(self):
        """测试提供商枚举"""
        from src.core.ai_bridge import AIProvider

        self.assertEqual(AIProvider.OLLAMA.value, "ollama")
        self.assertEqual(AIProvider.DEEPSEEK.value, "deepseek")
        self.assertEqual(AIProvider.WENXIN.value, "wenxin")
        self.assertEqual(AIProvider.QIANWEN.value, "qianwen")

    def test_summary_result_dataclass(self):
        """测试SummaryResult数据类"""
        from src.core.ai_bridge import SummaryResult

        result = SummaryResult(
            summary="测试摘要",
            todos=["待办1", "待办2"],
            model_used="test-model",
            tokens_used=100,
            success=True
        )

        self.assertEqual(result.summary, "测试摘要")
        self.assertEqual(len(result.todos), 2)
        self.assertTrue(result.success)
        self.assertIsNone(result.error)

    def test_generate_summary_fallback(self):
        """测试摘要生成（无服务时返回失败）"""
        from src.core.ai_bridge import AIBridge

        bridge = AIBridge(db=None)
        # 强制设置为无服务
        bridge.current_provider = bridge.current_provider.__class__.NONE

        result = bridge.generate_summary("测试主题", "测试内容")
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    def test_usage_stats(self):
        """测试使用统计"""
        from src.core.ai_bridge import AIBridge

        bridge = AIBridge(db=None)
        stats = bridge.get_usage_stats()

        self.assertIn('total_requests', stats)
        self.assertIn('total_tokens', stats)
        self.assertIn('provider', stats)


class TestOllamaProcessor(unittest.TestCase):
    """测试Ollama处理器"""

    def test_processor_creation(self):
        """测试处理器创建"""
        from src.core.ai_bridge import OllamaProcessor, OllamaConfig

        config = OllamaConfig()
        processor = OllamaProcessor(config)

        self.assertIsNotNone(processor)
        self.assertEqual(processor.config.base_url, "http://localhost:11434")

    def test_custom_config(self):
        """测试自定义配置"""
        from src.core.ai_bridge import OllamaProcessor, OllamaConfig

        config = OllamaConfig(
            base_url="http://custom:11434",
            model="custom-model"
        )
        processor = OllamaProcessor(config)

        self.assertEqual(processor.config.base_url, "http://custom:11434")
        self.assertEqual(processor.config.model, "custom-model")


class TestCloudAPIProcessor(unittest.TestCase):
    """测试云端API处理器"""

    def test_processor_creation(self):
        """测试处理器创建"""
        from src.core.ai_bridge import CloudAPIProcessor, CloudAPIConfig, AIProvider

        config = CloudAPIConfig(
            api_key="test-key",
            model="test-model"
        )
        processor = CloudAPIProcessor(AIProvider.DEEPSEEK, config)

        self.assertIsNotNone(processor)
        self.assertEqual(processor.config.api_key, "test-key")

    def test_is_available(self):
        """测试可用性检查"""
        from src.core.ai_bridge import CloudAPIProcessor, CloudAPIConfig, AIProvider

        # 有API密钥
        config = CloudAPIConfig(api_key="test-key")
        processor = CloudAPIProcessor(AIProvider.DEEPSEEK, config)
        self.assertTrue(processor.is_available())

        # 无API密钥
        config = CloudAPIConfig(api_key="")
        processor = CloudAPIProcessor(AIProvider.DEEPSEEK, config)
        self.assertFalse(processor.is_available())


if __name__ == '__main__':
    unittest.main()
