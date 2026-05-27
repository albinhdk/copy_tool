from typing import List, Dict
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem

class FileTreeView(QTreeWidget):
    """文件树视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    
    def __init__(self, parent=None):
        """初始化文件树视图"""
        super().__init__(parent)
        self.setHeaderLabels(["文件路径", "状态"])
        self.setColumnCount(2)
        self.setColumnWidth(0, 400)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self._setup_style()
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
            }
            QTreeWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #f3f4f6;
            }
            QTreeWidget::item:selected {
                background-color: #e5e7eb;
                color: #111827;
            }
        """)
    
    def load_files(self, files: List[FileItem]):
        """
        加载文件列表，构建树形结构
        
        Args:
            files: 文件项列表
        """
        self.blockSignals(True)
        self.clear()
        
        # 构建树形结构
        for file_item in files:
            parts = file_item.relative_path.replace("\\", "/").split("/")
            parent = self.invisibleRootItem()
            
            # 创建或查找目录节点
            for i, part in enumerate(parts[:-1]):
                found = None
                for j in range(parent.childCount()):
                    if parent.child(j).text(0) == part:
                        found = parent.child(j)
                        break
                
                if found is None:
                    found = QTreeWidgetItem(parent, [part, ""])
                    found.setFlags(found.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    found.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
                    parent = found
                else:
                    parent = found
            
            # 创建文件节点
            file_item_widget = QTreeWidgetItem(parent, [parts[-1], file_item.status])
            file_item_widget.setData(0, Qt.ItemDataRole.UserRole, file_item.relative_path)
            file_item_widget.setFlags(file_item_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            file_item_widget.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
        
        self.expandAll()
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表"""
        selected = []
        self._collect_checked(self.invisibleRootItem(), selected)
        return selected
    
    def _collect_checked(self, parent: QTreeWidgetItem, selected: List[str]):
        """递归收集选中的文件"""
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.childCount() == 0:  # 叶子节点（文件）
                if item.checkState(0) == Qt.CheckState.Checked:
                    rel_path = item.data(0, Qt.ItemDataRole.UserRole)
                    if rel_path:
                        selected.append(rel_path)
            else:
                self._collect_checked(item, selected)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total, selected = self._count_items(self.invisibleRootItem())
        return {"total": total, "selected": selected}
    
    def _count_items(self, parent: QTreeWidgetItem) -> tuple:
        """递归统计文件数量"""
        total = 0
        selected = 0
        
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.childCount() == 0:  # 叶子节点
                total += 1
                if item.checkState(0) == Qt.CheckState.Checked:
                    selected += 1
            else:
                t, s = self._count_items(item)
                total += t
                selected += s
        
        return total, selected
    
    def set_all_checked(self, checked: bool):
        """设置所有项的选中状态"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.blockSignals(True)
        self._set_checked_recursive(self.invisibleRootItem(), state)
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _set_checked_recursive(self, parent: QTreeWidgetItem, state: Qt.CheckState):
        """递归设置选中状态"""
        for i in range(parent.childCount()):
            item = parent.child(i)
            item.setCheckState(0, state)
            self._set_checked_recursive(item, state)
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """项状态变化处理"""
        # 级联更新子项
        self.blockSignals(True)
        self._propagate_check(item, item.checkState(0))
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _propagate_check(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """级联传播选中状态到子项"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._propagate_check(child, state)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
            }
        """)
        
        select_all = QAction("全选", self)
        select_all.triggered.connect(lambda: self.set_all_checked(True))
        
        deselect_all = QAction("全不选", self)
        deselect_all.triggered.connect(lambda: self.set_all_checked(False))
        
        menu.addAction(select_all)
        menu.addAction(deselect_all)
        
        menu.exec(self.mapToGlobal(pos))