# tests/test_history_combo.py
import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QEvent, Qt
from PySide6.QtGui import QMouseEvent
from src.components.history_combo import HistoryComboBox, HistoryItemDelegate


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def combo(qapp):
    """创建带历史记录的下拉框实例"""
    combo = HistoryComboBox("test:")
    combo.load_history(["/repo/a", "/repo/b", "/repo/c"])
    yield combo
    combo.deleteLater()


def _mouse_event(event_type, pos, button, buttons):
    """构造合成鼠标事件"""
    return QMouseEvent(event_type, QPointF(pos[0], pos[1]), button, buttons,
                       Qt.KeyboardModifier.NoModifier)


# ========== 历史记录加载测试 ==========

def test_load_history(combo):
    """测试加载历史记录"""
    assert combo.count() == 3
    assert combo.itemText(0) == "/repo/a"


def test_get_history(combo):
    """测试获取当前所有历史记录"""
    assert combo.get_history() == ["/repo/a", "/repo/b", "/repo/c"]


# ========== 弹出视图安装测试 ==========

def test_popup_setup_on_show_popup(combo):
    """测试弹出下拉列表后，弹出视图已启用鼠标跟踪并安装自定义委托"""
    combo.showPopup()
    view = combo.view()
    assert view.hasMouseTracking()
    assert isinstance(view.itemDelegate(), HistoryItemDelegate)
    combo.hidePopup()


# ========== 悬停与×按钮命中测试 ==========

def test_delete_button_rect_on_right_side():
    """测试×按钮位于条目矩形右侧垂直居中（允许整数舍入±1px）"""
    from PySide6.QtCore import QRect
    item_rect = QRect(0, 0, 200, 24)
    rect = HistoryItemDelegate.delete_button_rect(item_rect)
    assert abs(rect.center().y() - item_rect.center().y()) <= 1
    assert rect.right() <= item_rect.right()
    assert rect.left() > item_rect.center().x()


def test_mouse_move_sets_hover_state(combo):
    """测试鼠标移动后委托记录悬停行"""
    combo.showPopup()
    view = combo.view()
    item_rect = view.visualRect(view.model().index(0, 0))
    pos = item_rect.left() + 5, item_rect.center().y()
    move = _mouse_event(QEvent.Type.MouseMove, pos,
                        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton)
    combo.eventFilter(view.viewport(), move)
    assert combo._history_delegate._hovered_row == 0
    assert not combo._history_delegate._delete_hovered
    combo.hidePopup()


def test_mouse_move_over_delete_button_marks_delete_hover(combo):
    """测试鼠标移到×按钮区域后委托标记按钮悬停"""
    combo.showPopup()
    view = combo.view()
    btn_rect = HistoryItemDelegate.delete_button_rect(
        view.visualRect(view.model().index(0, 0)))
    pos = btn_rect.center().x(), btn_rect.center().y()
    move = _mouse_event(QEvent.Type.MouseMove, pos,
                        Qt.MouseButton.NoButton, Qt.MouseButton.NoButton)
    combo.eventFilter(view.viewport(), move)
    assert combo._history_delegate._hovered_row == 0
    assert combo._history_delegate._delete_hovered
    combo.hidePopup()


# ========== 点击删除测试 ==========

def test_click_on_delete_button_removes_item(combo):
    """测试点击×按钮后条目被删除，且事件被拦截（不选中、不关闭）"""
    received = []
    combo.history_changed.connect(received.append)
    combo.showPopup()
    view = combo.view()
    btn_rect = HistoryItemDelegate.delete_button_rect(
        view.visualRect(view.model().index(0, 0)))
    center = btn_rect.center().x(), btn_rect.center().y()

    press = _mouse_event(QEvent.Type.MouseButtonPress, center,
                         Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
    release = _mouse_event(QEvent.Type.MouseButtonRelease, center,
                           Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton)
    assert combo.eventFilter(view.viewport(), press) is True
    assert combo.eventFilter(view.viewport(), release) is True

    assert combo.get_history() == ["/repo/b", "/repo/c"]
    assert received == [["/repo/b", "/repo/c"]]
    combo.hidePopup()


def test_click_outside_delete_button_not_intercepted(combo):
    """测试点击条目其他区域不拦截事件、不删除条目"""
    combo.showPopup()
    view = combo.view()
    item_rect = view.visualRect(view.model().index(0, 0))
    pos = item_rect.left() + 5, item_rect.center().y()
    press = _mouse_event(QEvent.Type.MouseButtonPress, pos,
                         Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
    assert combo.eventFilter(view.viewport(), press) is False
    assert combo.count() == 3
    combo.hidePopup()


# ========== 删除行为测试 ==========

def test_remove_item_deletes_row_and_emits_signal(combo):
    """测试删除指定行后发出历史变化信号"""
    received = []
    combo.history_changed.connect(received.append)

    combo._remove_item(1)

    assert combo.get_history() == ["/repo/a", "/repo/c"]
    assert received == [["/repo/a", "/repo/c"]]


def test_remove_item_keeps_line_edit_text(combo):
    """测试删除当前项时输入框文本保留"""
    combo.setCurrentText("/repo/b")

    combo._remove_item(1)

    assert combo.currentText() == "/repo/b"


def test_remove_item_invalid_row_no_signal(combo):
    """测试删除无效行号不发出信号也不改变内容"""
    received = []
    combo.history_changed.connect(received.append)

    combo._remove_item(-1)
    combo._remove_item(99)

    assert received == []
    assert combo.count() == 3


def test_remove_item_does_not_trigger_current_text_changed(combo):
    """测试删除操作不会误触发currentTextChanged（避免误启动扫描）"""
    triggered = []
    combo.currentTextChanged.connect(triggered.append)

    combo.setCurrentText("/repo/b")
    triggered.clear()

    combo._remove_item(1)

    assert triggered == []
