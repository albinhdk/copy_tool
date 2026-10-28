import pytest
import sys
from PySide6.QtWidgets import QApplication, QHeaderView
from PySide6.QtCore import Qt
from src.views.file_list_view import FileListView
from src.views.file_tree_view import FileTreeView


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _show_offscreen(view):
    """在不弹出窗口的情况下触发尺寸布局。"""
    view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    view.resize(800, 400)
    view.show()
    QApplication.processEvents()


@pytest.mark.parametrize("view_class", [FileListView, FileTreeView])
def test_all_columns_are_draggable(qapp, view_class):
    """三列均为可拖动模式，首列自动填满剩余宽度。"""
    view = view_class()
    _show_offscreen(view)

    header = view.header()
    assert all(
        header.sectionResizeMode(column) == QHeaderView.ResizeMode.Interactive
        for column in range(3)
    )
    assert view.columnWidth(0) == max(
        160, view.viewport().width() - view.columnWidth(1) - view.columnWidth(2)
    )
    view.close()


@pytest.mark.parametrize("view_class", [FileListView, FileTreeView])
def test_manual_column_width_survives_window_resize(qapp, view_class):
    """用户拖动首列后，窗口缩放只按变化量同步，不覆盖手动宽度。"""
    view = view_class()
    _show_offscreen(view)

    view.header().resizeSection(0, 250)
    assert view.columnWidth(0) == 250

    view.resize(900, 400)
    QApplication.processEvents()
    assert view.columnWidth(0) == 350

    view.resize(700, 400)
    QApplication.processEvents()
    assert view.columnWidth(0) == 160  # 不小于首列最小宽度
    view.close()
