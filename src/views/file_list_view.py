from typing import List, Optional

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem
from ..config import LIST_VIEW_STYLE, CONTEXT_MENU_STYLE, STATUS_ORDER


class _FileListItem(QTreeWidgetItem):
    """兼容原列表项无参数 text() 调用的表格项。"""

    def text(self, column: int = 0) -> str:
        return super().text(column)


class FileListView(QTreeWidget):
    """文件列表视图：文件路径、状态、最后修改时间三列均支持点击表头排序。"""

    selection_changed = Signal()
    file_double_clicked = Signal(str)
    # 表头排序生效时发出（排序列, 是否升序），供主窗口同步“按类型排序”按钮
    header_sort_activated = Signal(int, bool)

    # 各列首次点击时的默认排序方向
    _DEFAULT_SORT_ORDERS = {
        0: Qt.SortOrder.AscendingOrder,   # 文件路径：按路径升序
        1: Qt.SortOrder.AscendingOrder,   # 状态：按预设状态顺序
        2: Qt.SortOrder.DescendingOrder,  # 最后修改时间：最新在前
    }

    def __init__(self, parent=None):
        """初始化文件列表视图。"""
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHeaderLabels(["文件路径", "状态", "最后修改时间"])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)

        header = self.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        # 时间列宽度按完整时间戳的文字宽度固定，避免内容被省略号截断
        self.setColumnWidth(
            2, self.fontMetrics().horizontalAdvance("0000-00-00 00:00:00") + 24
        )
        header.sectionClicked.connect(self._on_header_clicked)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()

        # 排序状态：当前排序列（None 表示未排序）及各列记忆的排序方向
        self._sort_column: Optional[int] = None
        self._sort_orders = dict(self._DEFAULT_SORT_ORDERS)
        self._status_order = list(STATUS_ORDER)

    def _setup_style(self):
        """设置样式。"""
        self.setStyleSheet(LIST_VIEW_STYLE)

    def load_files(self, files: List[FileItem]):
        """加载文件列表。"""
        self.blockSignals(True)
        self.clear()

        for file_item in files:
            item = _FileListItem([
                file_item.relative_path,
                file_item.status,
                file_item.get_modified_time_text(),
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, file_item.relative_path)
            item.setData(2, Qt.ItemDataRole.UserRole, file_item.modified_time)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                0,
                Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked,
            )
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
            self.addTopLevelItem(item)

        # 加载后应用当前表头排序，保证过滤、刷新后排序状态不丢失
        if self._sort_column is not None:
            self._sort_current_items()

        self.blockSignals(False)
        self.selection_changed.emit()

    def set_sort_by_status(self, enabled: bool):
        """设置是否按状态排序（“按类型排序”按钮入口）。"""
        if enabled:
            self._sort_column = 1
            self._sort_orders[1] = Qt.SortOrder.AscendingOrder
            self.header().setSortIndicator(1, Qt.SortOrder.AscendingOrder)
            self.header().setSortIndicatorShown(True)
        elif self._sort_column == 1:
            # 仅取消状态列排序，避免影响通过表头设置的其它列排序
            self._sort_column = None
            self.header().setSortIndicatorShown(False)

    def _on_header_clicked(self, column: int):
        """点击表头排序：再次点击同一列切换升/降序；切换到新列时沿用该列上次的方向（首次点击为默认方向）。"""
        if column == self._sort_column:
            self._sort_orders[column] = (
                Qt.SortOrder.AscendingOrder
                if self._sort_orders[column] == Qt.SortOrder.DescendingOrder
                else Qt.SortOrder.DescendingOrder
            )
        else:
            self._sort_column = column

        order = self._sort_orders[column]
        header = self.header()
        header.setSortIndicator(column, order)
        header.setSortIndicatorShown(True)
        self._sort_current_items()
        self.header_sort_activated.emit(
            column, order == Qt.SortOrder.AscendingOrder
        )

    def _sort_current_items(self):
        """按当前排序列重排现有行，同时保留用户的勾选状态。"""
        if self._sort_column is None:
            return

        was_blocked = self.signalsBlocked()
        self.blockSignals(True)
        items = [
            self.takeTopLevelItem(0)
            for _ in range(self.topLevelItemCount())
        ]
        reverse = self._sort_orders[self._sort_column] == Qt.SortOrder.DescendingOrder

        if self._sort_column == 0:
            items.sort(key=self._path_sort_key, reverse=reverse)
        elif self._sort_column == 1:
            items = self._sort_items_with_fallback(
                items, self._status_sort_key, reverse
            )
        else:
            items = self._sort_items_with_fallback(
                items, self._time_sort_key, reverse
            )

        self.addTopLevelItems(items)
        self.blockSignals(was_blocked)

    @staticmethod
    def _sort_items_with_fallback(items: List[QTreeWidgetItem],
                                  sort_key, reverse: bool) -> List[QTreeWidgetItem]:
        """按排序键重排行，键为 None（未知状态/无时间）的项始终置于末尾。"""
        sortable, fallback = [], []
        for item in items:
            (sortable if sort_key(item) is not None else fallback).append(item)
        sortable.sort(key=sort_key, reverse=reverse)
        return sortable + fallback

    @staticmethod
    def _path_sort_key(item: QTreeWidgetItem):
        """路径排序键：大小写不敏感，同键时以原始路径保证顺序稳定。"""
        path = item.data(0, Qt.ItemDataRole.UserRole) or ""
        return (path.lower(), path)

    def _status_sort_key(self, item: QTreeWidgetItem):
        """状态排序键：按预设状态顺序取索引，未知状态返回 None 置于末尾。"""
        status = item.text(1)
        if status not in self._status_order:
            return None
        return self._status_order.index(status)

    @staticmethod
    def _time_sort_key(item: QTreeWidgetItem):
        """时间排序键：最后修改时间的时间戳，缺失时返回 None 置于末尾。"""
        return item.data(2, Qt.ItemDataRole.UserRole)

    def count(self) -> int:
        """返回文件行数，兼容原 QListWidget 接口。"""
        return self.topLevelItemCount()

    def item(self, index: int) -> QTreeWidgetItem:
        """返回指定文件行，兼容原 QListWidget 接口。"""
        return self.topLevelItem(index)

    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表。"""
        selected = []
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected.append(item.data(0, Qt.ItemDataRole.UserRole))
        return selected

    def get_statistics(self) -> dict:
        """获取统计信息（含按类型的已选数量）。"""
        total = self.topLevelItemCount()
        selected = 0
        by_status = {}
        for index in range(total):
            item = self.topLevelItem(index)
            if item.checkState(0) != Qt.CheckState.Checked:
                continue
            selected += 1
            status = item.text(1) or ""
            by_status[status] = by_status.get(status, 0) + 1
        return {"total": total, "selected": selected, "by_status": by_status}

    def set_all_checked(self, checked: bool):
        """设置所有项的选中状态。"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.blockSignals(True)
        for index in range(self.topLevelItemCount()):
            self.topLevelItem(index).setCheckState(0, state)
        self.blockSignals(False)
        self.selection_changed.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """项状态变化处理。"""
        self.selection_changed.emit()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """处理双击事件。"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_double_clicked.emit(file_path)

    def _show_context_menu(self, pos):
        """显示右键菜单。"""
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)

        select_all = QAction("全选", self)
        select_all.triggered.connect(lambda: self.set_all_checked(True))

        deselect_all = QAction("全不选", self)
        deselect_all.triggered.connect(lambda: self.set_all_checked(False))

        menu.addAction(select_all)
        menu.addAction(deselect_all)
        menu.exec(self.viewport().mapToGlobal(pos))
