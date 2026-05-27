from typing import List
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem
from ..config import LIST_VIEW_STYLE, CONTEXT_MENU_STYLE


class FileListView(QListWidget):
    """文件列表视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    
    def __init__(self, parent=None):
        """初始化文件列表视图"""
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(LIST_VIEW_STYLE)
    
    def load_files(self, files: List[FileItem]):
        """
        加载文件列表
        
        Args:
            files: 文件项列表
        """
        self.blockSignals(True)
        self.clear()
        
        for file_item in files:
            item = QListWidgetItem(file_item.get_display_text())
            item.setData(Qt.ItemDataRole.UserRole, file_item.relative_path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
            self.addItem(item)
        
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表"""
        selected = []
        for i in range(self.count()):
            item = self.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = self.count()
        selected = sum(1 for i in range(total) if self.item(i).checkState() == Qt.CheckState.Checked)
        return {"total": total, "selected": selected}
    
    def set_all_checked(self, checked: bool):
        """设置所有项的选中状态"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.blockSignals(True)
        for i in range(self.count()):
            self.item(i).setCheckState(state)
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _on_item_changed(self, item: QListWidgetItem):
        """项状态变化处理"""
        self.selection_changed.emit()
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """处理双击事件"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_double_clicked.emit(file_path)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        select_all = QAction("全选", self)
        select_all.triggered.connect(lambda: self.set_all_checked(True))
        
        deselect_all = QAction("全不选", self)
        deselect_all.triggered.connect(lambda: self.set_all_checked(False))
        
        menu.addAction(select_all)
        menu.addAction(deselect_all)
        
        menu.exec(self.mapToGlobal(pos))
