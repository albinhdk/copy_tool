from datetime import datetime
from typing import List

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem
from ..config import LIST_VIEW_STYLE, CONTEXT_MENU_STYLE, STATUS_ORDER

# Qt 角色：0=相对路径，1=文件状态，2=最后修改时间
STATISTICS_STATUS_ROLE = Qt.ItemDataRole.UserRole + 1


class _FileListItem(QTreeWidgetItem):
    """兼容原列表项无参数 text() 调用的表格项。"""

    def text(self, column: int = 0) -> str:
        return super().text(column)


class FileListView(QTreeWidget):
    """带最后修改时间列的文件列表视图组件。"""

    selection_changed = Signal()
    file_double_clicked = Signal(str)
    time_sort_activated = Signal()

    def __init__(self, parent=None):
        """初始化文件列表视图。"""
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["文件", "最后修改时间"])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)

        header = self.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.sectionClicked.connect(self._on_header_clicked)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()

        self._sort_by_status = False
        self._sort_by_time = False
        self._time_sort_order = Qt.SortOrder.DescendingOrder
        self._status_order = list(STATUS_ORDER)

    def _setup_style(self):
        """设置样式。"""
        self.setStyleSheet(LIST_VIEW_STYLE)

    def load_files(self, files: List[FileItem]):
        """加载文件列表。"""
        self.blockSignals(True)
        self.clear()

        if self._sort_by_time:
            files = self._sort_files_by_time(files)
        elif self._sort_by_status:
            files = self._sort_files_by_status(files)

        for file_item in files:
            item = _FileListItem([
                file_item.get_display_text(),
                self._format_modified_time(file_item.modified_time),
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, file_item.relative_path)
            item.setData(0, STATISTICS_STATUS_ROLE, file_item.status)
            item.setData(1, Qt.ItemDataRole.UserRole, file_item.modified_time)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                0,
                Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked,
            )
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            self.addTopLevelItem(item)

        self.blockSignals(False)
        self.selection_changed.emit()

    @staticmethod
    def _format_modified_time(modified_time: float | None) -> str:
        """将时间戳格式化为本地时间。"""
        if modified_time is None:
            return "—"
        return datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")

    def _sort_files_by_status(self, files: List[FileItem]) -> List[FileItem]:
        """按状态对文件进行排序。"""
        def get_status_order(file_item: FileItem) -> int:
            try:
                return self._status_order.index(file_item.status)
            except ValueError:
                return len(self._status_order)

        return sorted(files, key=get_status_order)

    def _sort_files_by_time(self, files: List[FileItem]) -> List[FileItem]:
        """按最后修改时间排序，无时间的文件始终放在末尾。"""
        dated_files = [item for item in files if item.modified_time is not None]
        undated_files = [item for item in files if item.modified_time is None]
        reverse = self._time_sort_order == Qt.SortOrder.DescendingOrder
        dated_files.sort(key=lambda item: item.modified_time, reverse=reverse)
        return dated_files + undated_files

    def set_sort_by_status(self, enabled: bool):
        """设置是否按状态排序。"""
        self._sort_by_status = enabled
        if enabled:
            self._sort_by_time = False
            self.header().setSortIndicatorShown(False)

    def _on_header_clicked(self, column: int):
        """点击最后修改时间表头时切换升序/降序。"""
        if column != 1:
            return

        if self._sort_by_time:
            self._time_sort_order = (
                Qt.SortOrder.AscendingOrder
                if self._time_sort_order == Qt.SortOrder.DescendingOrder
                else Qt.SortOrder.DescendingOrder
            )
        else:
            self._sort_by_time = True
            self._sort_by_status = False
            self._time_sort_order = Qt.SortOrder.DescendingOrder

        header = self.header()
        header.setSortIndicator(1, self._time_sort_order)
        header.setSortIndicatorShown(True)
        self._sort_current_items_by_time()
        self.time_sort_activated.emit()

    def _sort_current_items_by_time(self):
        """重排现有行，同时保留用户的勾选状态。"""
        self.blockSignals(True)
        items = [
            self.takeTopLevelItem(0)
            for _ in range(self.topLevelItemCount())
        ]
        dated_items = [
            item
            for item in items
            if item.data(1, Qt.ItemDataRole.UserRole) is not None
        ]
        undated_items = [
            item
            for item in items
            if item.data(1, Qt.ItemDataRole.UserRole) is None
        ]
        reverse = self._time_sort_order == Qt.SortOrder.DescendingOrder
        dated_items.sort(
            key=lambda item: item.data(1, Qt.ItemDataRole.UserRole),
            reverse=reverse,
        )
        self.addTopLevelItems(dated_items + undated_items)
        self.blockSignals(False)

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
            status = item.data(0, STATISTICS_STATUS_ROLE) or ""
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
