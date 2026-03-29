# -*- coding: utf-8 -*-
"""
图标资源管理模块
统一管理应用中的所有图标资源
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize


class IconManager:
    """图标管理器"""
    
    _instance: Optional['IconManager'] = None
    
    def __init__(self, icons_dir: str):
        """初始化图标管理器
        
        Args:
            icons_dir: 图标目录路径
        """
        self.icons_dir = Path(icons_dir)
        self.logger = logging.getLogger(__name__)
        
        # 图标缓存
        self._icon_cache = {}
        
        # 定义图标路径
        self.icon_paths = {
            'app': self.icons_dir / 'app.ico',
            'app_16': self.icons_dir / 'app-icon-16.png',
            'app_32': self.icons_dir / 'app-icon-32.png',
            'app_64': self.icons_dir / 'app-icon-64.png',
            'app_128': self.icons_dir / 'app-icon-128.png',
            'app_256': self.icons_dir / 'app-icon-256.png',
        }
    
    @classmethod
    def init_instance(cls, icons_dir: str) -> 'IconManager':
        """初始化单例实例
        
        Args:
            icons_dir: 图标目录路径
            
        Returns:
            IconManager实例
        """
        if cls._instance is None:
            cls._instance = cls(icons_dir)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'IconManager':
        """获取单例实例
        
        Returns:
            IconManager实例
            
        Raises:
            RuntimeError: 如果实例未初始化
        """
        if cls._instance is None:
            raise RuntimeError("IconManager未初始化，请先调用init_instance()")
        return cls._instance
    
    def get_icon(self, icon_name: str, size: Optional[int] = None) -> QIcon:
        """获取图标
        
        Args:
            icon_name: 图标名称（如 'app'）
            size: 可选的图标尺寸（如 64）
            
        Returns:
            QIcon对象，如果图标不存在则返回空图标
        """
        # 构建缓存键
        cache_key = f"{icon_name}_{size}" if size else icon_name
        
        # 检查缓存
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # 确定图标路径
        if size:
            icon_key = f"{icon_name}_{size}"
            icon_path = self.icon_paths.get(icon_key)
        else:
            icon_path = self.icon_paths.get(icon_name)
        
        # 如果指定尺寸的图标不存在，尝试使用ICO文件
        if icon_path is None or not icon_path.exists():
            icon_path = self.icon_paths.get('app')
        
        # 加载图标
        if icon_path and icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self._icon_cache[cache_key] = icon
                    self.logger.debug(f"成功加载图标: {icon_path}")
                    return icon
                else:
                    self.logger.warning(f"图标加载失败: {icon_path}")
            except Exception as e:
                self.logger.error(f"加载图标时出错 {icon_path}: {e}")
        else:
            self.logger.warning(f"图标文件不存在: {icon_path}")
        
        # 返回空图标
        return QIcon()
    
    def get_pixmap(self, icon_name: str, size: int = 64) -> QPixmap:
        """获取位图
        
        Args:
            icon_name: 图标名称
            size: 位图尺寸
            
        Returns:
            QPixmap对象
        """
        icon = self.get_icon(icon_name, size)
        if not icon.isNull():
            return icon.pixmap(QSize(size, size))
        return QPixmap()
    
    def setup_app_icon(self, app) -> None:
        """设置应用图标
        
        Args:
            app: QApplication实例
        """
        try:
            # 尝试加载ICO文件（Windows最佳兼容性）
            icon = self.get_icon('app')
            if not icon.isNull():
                app.setWindowIcon(icon)
                self.logger.info("应用图标设置成功")
            else:
                self.logger.warning("应用图标设置失败，使用默认图标")
        except Exception as e:
            self.logger.error(f"设置应用图标时出错: {e}")
    
    def setup_window_icon(self, window) -> None:
        """设置窗口图标
        
        Args:
            window: QMainWindow或QDialog实例
        """
        try:
            icon = self.get_icon('app')
            if not icon.isNull():
                window.setWindowIcon(icon)
                self.logger.debug(f"窗口图标设置成功: {window.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"设置窗口图标时出错: {e}")


def init_icon_manager(icons_dir: str) -> IconManager:
    """初始化图标管理器
    
    Args:
        icons_dir: 图标目录路径
        
    Returns:
        IconManager实例
    """
    return IconManager.init_instance(icons_dir)


def get_icon_manager() -> IconManager:
    """获取图标管理器实例
    
    Returns:
        IconManager实例
    """
    return IconManager.get_instance()
