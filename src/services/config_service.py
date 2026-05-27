from typing import List
from PySide6.QtCore import QSettings

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
        return self.settings.value("src_history", [])
    
    def save_source_history(self, path: str, max_items: int = 10):
        """
        保存源目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认为10
        """
        if not path:
            return
        
        history = self.get_source_history()
        
        # 移除已存在的路径（如果有的话）
        if path in history:
            history.remove(path)
        
        # 添加到最前面
        history.insert(0, path)
        
        # 限制最大数量
        history = history[:max_items]
        
        self.settings.setValue("src_history", history)
    
    def get_target_history(self) -> List[str]:
        """获取目标目录历史记录"""
        return self.settings.value("tgt_history", [])
    
    def save_target_history(self, path: str, max_items: int = 10):
        """
        保存目标目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认为10
        """
        if not path:
            return
        
        history = self.get_target_history()
        
        if path in history:
            history.remove(path)
        
        history.insert(0, path)
        history = history[:max_items]
        
        self.settings.setValue("tgt_history", history)