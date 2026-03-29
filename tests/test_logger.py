# tests/test_logger.py
"""
日志工具测试
"""
import pytest
import os
import tempfile
import logging
from src.utils.logger import setup_logger, get_log_dir, get_default_logger


class TestLogger:
    """日志工具测试类"""
    
    def test_setup_logger_creates_logger(self):
        """测试setup_logger能创建日志记录器"""
        logger = setup_logger('test_logger', None)
        assert logger is not None
        assert logger.name == 'test_logger'
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_with_log_dir(self):
        """测试带日志目录的日志记录器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logger('test_with_dir', tmpdir)
            assert logger is not None
            assert len(logger.handlers) >= 1  # 至少有控制台handler
    
    def test_get_log_dir_returns_valid_path(self):
        """测试get_log_dir返回有效路径"""
        log_dir = get_log_dir()
        assert 'ai-mail-assistant' in log_dir
        assert os.path.isabs(log_dir)
    
    def test_get_log_dir_creates_directory(self):
        """测试get_log_dir会创建目录"""
        log_dir = get_log_dir()
        assert os.path.exists(log_dir)
        assert os.path.isdir(log_dir)
    
    def test_default_logger_has_correct_name(self):
        """测试默认日志记录器名称正确"""
        logger = get_default_logger()
        assert logger.name == 'ai-mail-assistant'
    
    def test_multiple_setup_returns_same_logger(self):
        """测试多次setup返回同一个logger实例"""
        logger1 = setup_logger('same_name', None)
        logger2 = setup_logger('same_name', None)
        assert logger1 is logger2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
