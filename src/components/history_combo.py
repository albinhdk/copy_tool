from typing import List
from PySide6.QtCore import QEvent, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate
from ..config import MAX_HISTORY_ITEMS


class HistoryItemDelegate(QStyledItemDelegate):
    """历史记录条目委托：悬停条目时在行尾绘制"×"删除按钮"""

    DELETE_BUTTON_SIZE = 20   # 按钮区域边长
    DELETE_BUTTON_MARGIN = 6  # 按钮距条目右边缘的距离

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered_row = -1
        self._delete_hovered = False

    def set_hover(self, row: int, over_delete: bool):
        """更新悬停状态（行号 + 是否悬停在×按钮上）"""
        self._hovered_row = row
        self._delete_hovered = over_delete

    @classmethod
    def delete_button_rect(cls, item_rect: QRect) -> QRect:
        """计算条目矩形内"×"按钮的区域（右侧垂直居中）"""
        size = cls.DELETE_BUTTON_SIZE
        return QRect(
            item_rect.right() - size - cls.DELETE_BUTTON_MARGIN,
            item_rect.center().y() - size // 2,
            size,
            size,
        )

    def paint(self, painter: QPainter, option, index):
        """先按默认方式绘制文本，悬停时在行尾追加"×"按钮"""
        super().paint(painter, option, index)

        if index.row() != self._hovered_row:
            return

        btn_rect = self.delete_button_rect(option.rect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._delete_hovered:
            # 悬停在按钮上：红色圆底 + 白色 ×
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#ef4444"))
            painter.drawEllipse(btn_rect)
            color = QColor("#ffffff")
        else:
            color = QColor("#9ca3af")

        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        cx, cy = btn_rect.center().x(), btn_rect.center().y()
        r = 4
        painter.drawLine(cx - r, cy - r, cx + r, cy + r)
        painter.drawLine(cx - r, cy + r, cx + r, cy - r)
        painter.restore()


class HistoryComboBox(QComboBox):
    """带历史记录的下拉框组件：悬停历史条目时行尾出现"×"，点击即可删除该条"""

    history_changed = Signal(list)  # 删除条目后发出，携带最新历史列表

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
        self._history_delegate = None
        self._popup_ready = False

    def showPopup(self):
        """显示下拉列表前，为弹出视图安装悬停删除功能"""
        super().showPopup()
        self._setup_popup()

    def hidePopup(self):
        """关闭下拉列表时重置悬停状态"""
        super().hidePopup()
        if self._history_delegate is not None:
            self._history_delegate.set_hover(-1, False)

    def _setup_popup(self):
        """为弹出视图启用鼠标跟踪并安装自定义委托与事件过滤器"""
        if self._popup_ready:
            return
        view = self.view()
        view.setMouseTracking(True)
        self._history_delegate = HistoryItemDelegate(view)
        view.setItemDelegate(self._history_delegate)
        view.viewport().installEventFilter(self)
        self._popup_ready = True

    def eventFilter(self, obj, event):
        """拦截弹出视图的鼠标事件：×按钮区域点击删除条目，其余照常选择"""
        view = self.view()
        if obj is view.viewport() and self._history_delegate is not None:
            et = event.type()
            if et == QEvent.Type.MouseMove:
                self._update_hover(event.position().toPoint())
            elif et == QEvent.Type.Leave:
                self._history_delegate.set_hover(-1, False)
                view.viewport().update()
            elif et in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                if event.button() == Qt.MouseButton.LeftButton:
                    pos = event.position().toPoint()
                    if self._in_delete_button(pos):
                        if et == QEvent.Type.MouseButtonPress:
                            index = view.indexAt(pos)
                            self._remove_item(index.row())
                            # 条目删除后行上移，按当前鼠标位置刷新悬停状态
                            self._update_hover(view.viewport().mapFromGlobal(QCursor.pos()))
                        return True  # 吞掉事件：不选中、不关闭下拉
        return super().eventFilter(obj, event)

    def _update_hover(self, pos):
        """根据鼠标位置更新悬停行与×按钮悬停状态"""
        view = self.view()
        index = view.indexAt(pos)
        if index.isValid():
            self._history_delegate.set_hover(index.row(), self._in_delete_button(pos))
        else:
            self._history_delegate.set_hover(-1, False)
        view.viewport().update()

    def _in_delete_button(self, pos) -> bool:
        """判断视口坐标是否落在某条目的×按钮区域内"""
        view = self.view()
        index = view.indexAt(pos)
        if not index.isValid():
            return False
        rect = HistoryItemDelegate.delete_button_rect(view.visualRect(index))
        return rect.contains(pos)

    def get_history(self) -> List[str]:
        """获取当前下拉列表中的所有历史记录"""
        return [self.itemText(i) for i in range(self.count())]

    def _remove_item(self, row: int):
        """删除指定行并发出历史变化信号

        Args:
            row: 要删除的行号
        """
        if row < 0 or row >= self.count():
            return

        current_text = self.currentText()
        self.blockSignals(True)
        self.removeItem(row)
        # 恢复输入框文本，避免当前项被删除时清空输入框
        if self.currentText() != current_text:
            self.setEditText(current_text)
        self.blockSignals(False)

        self.history_changed.emit(self.get_history())

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

    def add_to_history(self, path: str, max_items: int = None):
        """
        添加路径到历史记录

        Args:
            path: 要添加的路径
            max_items: 最大记录数量，默认使用配置常量
        """
        if not path:
            return

        if max_items is None:
            max_items = MAX_HISTORY_ITEMS

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
