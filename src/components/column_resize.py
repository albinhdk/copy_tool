"""表头列宽拖动支持。"""

from PySide6.QtWidgets import QHeaderView


class ResizableColumnsMixin:
    """让表格各列可拖动调整宽度，并保持首列自动填充剩余空间。"""

    MIN_FIRST_COLUMN_WIDTH = 160
    MIN_SECTION_WIDTH = 60

    def _setup_column_resizing(self):
        """将所有列设为可拖动模式，并准备首列自动填充逻辑。"""
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(self.MIN_SECTION_WIDTH)
        header.sectionResized.connect(self._on_section_resized)
        self._first_column_customized = False
        self._auto_adjusting = False
        self._last_viewport_width = self.viewport().width()

    def _on_section_resized(self, logical_index: int, old_size: int, new_size: int):
        """记录首列是否被用户手动拖动过。"""
        if logical_index == 0 and not self._auto_adjusting:
            self._first_column_customized = True

    def resizeEvent(self, event):
        """窗口尺寸变化时调整首列宽度，保持表格铺满可用区域。"""
        super().resizeEvent(event)
        self._adjust_first_column_width()

    def _adjust_first_column_width(self):
        """未手动拖动首列时让其填满剩余空间；手动拖动后仅跟随窗口宽度变化。"""
        header = self.header()
        viewport_width = self.viewport().width()
        self._auto_adjusting = True
        try:
            if self._first_column_customized:
                delta = viewport_width - self._last_viewport_width
                if delta:
                    header.resizeSection(
                        0,
                        max(self.MIN_FIRST_COLUMN_WIDTH, self.columnWidth(0) + delta),
                    )
            else:
                other_width = self.columnWidth(1) + self.columnWidth(2)
                header.resizeSection(
                    0, max(self.MIN_FIRST_COLUMN_WIDTH, viewport_width - other_width)
                )
        finally:
            self._auto_adjusting = False
        self._last_viewport_width = viewport_width
