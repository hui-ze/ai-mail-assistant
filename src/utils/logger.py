# src/utils/logger.py
"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_dir: Optional[str] = None) -> logging.Logger:
    """
    创建并配置日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录，默认使用应用数据目录下的logs子目录
    
    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器 - INFO及以上级别显示
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 - DEBUG及以上级别记录
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'{name}_{datetime.now():%Y%m%d}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_log_dir() -> str:
    """
    获取日志目录
    
    Returns:
        日志目录的绝对路径
    """
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(app_data, 'ai-mail-assistant', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_default_logger() -> logging.Logger:
    """
    获取默认的日志记录器（用于主模块）
    
    Returns:
        默认Logger实例
    """
    return setup_logger('ai-mail-assistant', get_log_dir())
