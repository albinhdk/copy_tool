from typing import List
from PySide6.QtWidgets import QComboBox

class HistoryComboBox(QComboBox):
    """带历史记录的下拉框组件"""
    
    def __init__(self, placeholder: str = "", parent=None):
        """
        初始化历史记录下拉框
        
        Args:
            placeholder: 占位符文本
            parent: 父组件
        """
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText(placeholder)
        self.setFixedHeight(32)
    
    def load_history(self, history: List[str]):
        """
        加载历史记录
        
        Args:
            history: 历史记录列表
        """
        self.blockSignals(True)
        self.clear()
        if history:
            self.addItems(history)
        self.setCurrentText("")
        self.blockSignals(False)
    
    def add_to_history(self, path: str, max_items: int = 10):
        """
        添加路径到历史记录
        
        Args:
            path: 要添加的路径
            max_items: 最大记录数量
        """
        if not path:
            return
        
        # 获取当前所有项
        history = [self.itemText(i) for i in range(self.count())]
        
        # 移除已存在的路径
        if path in history:
            history.remove(path)
        
        # 添加到最前面
        history.insert(0, path)
        
        # 限制最大数量
        history = history[:max_items]
        
        # 刷新下拉框
        self.blockSignals(True)
        self.clear()
        self.addItems(history)
        self.setCurrentText(path)
        self.blockSignals(False)
        
        return history