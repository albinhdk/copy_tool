from typing import List, Dict, Tuple
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem
from ..config import TREE_VIEW_STYLE, CONTEXT_MENU_STYLE


class FileTreeView(QTreeWidget):
    """文件树视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    
    def __init__(self, parent=None):
        """初始化文件树视图"""
        super().__init__(parent)
        self.setHeaderLabels(["文件路径", "状态"])
        self.setColumnCount(2)
        self.setColumnWidth(0, 400)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()
        
        # 排序状态
        self._sort_by_status = False
        self._status_order = ['已修改', '已添加', '已删除', '已重命名', '已复制', '未跟踪', '已忽略']
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(TREE_VIEW_STYLE)
    
    def load_files(self, files: List[FileItem]):
        """
        加载文件列表，构建树形结构
        
        使用字典缓存目录节点，将查找时间从O(n*d*c)降为O(n*d)
        
        Args:
            files: 文件项列表
        """
        self.blockSignals(True)
        self.clear()
        
        # 根据排序设置对文件进行排序
        if self._sort_by_status:
            files = self._sort_files_by_status(files)
        
        # 路径缓存：key=路径元组, value=QTreeWidgetItem
        node_cache: Dict[Tuple[str, ...], QTreeWidgetItem] = {}
        
        for file_item in files:
            parts = file_item.relative_path.replace("\\", "/").split("/")
            
            # 创建或查找目录节点
            parent = self.invisibleRootItem()
            for i in range(len(parts) - 1):
                dir_path = tuple(parts[:i + 1])
                
                if dir_path in node_cache:
                    parent = node_cache[dir_path]
                else:
                    found = QTreeWidgetItem(parent, [parts[i], ""])
                    found.setFlags(found.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    found.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
                    node_cache[dir_path] = found
                    parent = found
            
            # 创建文件节点
            file_item_widget = QTreeWidgetItem(parent, [parts[-1], file_item.status])
            file_item_widget.setData(0, Qt.ItemDataRole.UserRole, file_item.relative_path)
            file_item_widget.setFlags(file_item_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            file_item_widget.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
        
        self.expandAll()
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _sort_files_by_status(self, files: List[FileItem]) -> List[FileItem]:
        """
        按状态对文件进行排序
        
        Args:
            files: 文件项列表
            
        Returns:
            排序后的文件项列表
        """
        def get_status_order(file_item: FileItem) -> int:
            try:
                return self._status_order.index(file_item.status)
            except ValueError:
                return len(self._status_order)  # 未知状态排在最后
        
        return sorted(files, key=get_status_order)
    
    def set_sort_by_status(self, enabled: bool):
        """
        设置是否按状态排序
        
        Args:
            enabled: 是否启用按状态排序
        """
        self._sort_by_status = enabled
    
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
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """处理双击事件"""
        # 只处理文件节点（叶子节点），忽略目录节点
        if item.childCount() == 0:
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_double_clicked.emit(file_path)
    
    def _propagate_check(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """级联传播选中状态到子项"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._propagate_check(child, state)
    
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
