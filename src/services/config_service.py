from typing import List
from PySide6.QtCore import QSettings
from ..config import MAX_HISTORY_ITEMS


class ConfigService:
    """配置管理服务，处理历史记录和用户配置"""
    
    def __init__(self, settings: QSettings):
        """
        初始化配置服务
        
        Args:
            settings: QSettings实例，用于持久化存储
        """
        self.settings = settings
    
    def get_source_history(self) -> List[str]:
        """获取源目录历史记录"""
        return self._get_history("src_history")
    
    def save_source_history(self, path: str, max_items: int = None):
        """
        保存源目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认使用配置常量
        """
        self._save_history("src_history", path, max_items)
    
    def get_target_history(self) -> List[str]:
        """获取目标目录历史记录"""
        return self._get_history("tgt_history")
    
    def save_target_history(self, path: str, max_items: int = None):
        """
        保存目标目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认使用配置常量
        """
        self._save_history("tgt_history", path, max_items)
    
    def get_filter_history(self) -> List[str]:
        """获取过滤搜索历史记录"""
        return self._get_history("filter_history")
    
    def save_filter_history(self, text: str, max_items: int = None):
        """
        保存过滤搜索文本到历史记录
        
        Args:
            text: 过滤文本
            max_items: 最大记录数量，默认使用配置常量
        """
        self._save_history("filter_history", text, max_items)
    
    def _get_history(self, key: str) -> List[str]:
        """
        获取历史记录的通用方法
        
        Args:
            key: 设置项的键名
            
        Returns:
            历史记录列表
        """
        history = self.settings.value(key, [])
        if not isinstance(history, list):
            return []
        return [str(h) for h in history]
    
    def _save_history(self, key: str, path: str, max_items: int = None):
        """
        保存历史记录的通用方法
        
        Args:
            key: 设置项的键名
            path: 目录路径
            max_items: 最大记录数量
        """
        if not path:
            return
        
        if max_items is None:
            max_items = MAX_HISTORY_ITEMS
        
        history = self._get_history(key)
        
        # 移除已存在的路径（如果有的话）
        if path in history:
            history.remove(path)
        
        # 添加到最前面
        history.insert(0, path)
        
        # 限制最大数量
        history = history[:max_items]
        
        self.settings.setValue(key, history)
