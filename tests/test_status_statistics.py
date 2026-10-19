import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.config import STATUS_ORDER
from src.models.file_item import FileItem
from src.views.file_list_view import FileListView
from src.views.file_tree_view import FileTreeView
from src.views.main_window import MainWindow
from src.views.status_badge_bar import (
    StatusBadgeBar, ordered_status_items, status_badge_colors,
)


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_ordered_status_items_follow_status_order():
    """统计项按固定状态顺序排列，0 数量不显示，未知状态排在最后。"""
    counts = {"未跟踪": 2, "已删除": 4, "已修改": 8, "未知状态": 1, "已添加": 0}
    assert ordered_status_items(counts) == [
        ("已修改", 8), ("已删除", 4), ("未跟踪", 2), ("未知状态", 1),
    ]


def test_status_badge_colors_fall_back_for_unknown_status():
    """已知状态有专属配色，未知状态使用默认配色。"""
    assert status_badge_colors("已删除") != status_badge_colors("已修改")
    assert status_badge_colors("奇怪状态") == status_badge_colors("另一个状态")


def test_status_badge_bar_renders_badges_and_total(qapp):
    """徽章栏列出每类已选数量，并显示已选/总计。"""
    bar = StatusBadgeBar()
    bar.set_counts({"已修改": 8, "已删除": 4, "已添加": 5}, selected=17, total=30)
    bar.show()

    assert bar.badge_texts() == ["修改 8", "添加 5", "删除 4"]
    assert bar._total_badge.text() == "已选 17 / 30"


def test_status_badge_bar_hides_stale_badges(qapp):
    """类型数量减少后多余徽章会被隐藏。"""
    bar = StatusBadgeBar()
    bar.show()
    bar.set_counts({"已修改": 3, "已删除": 2, "未跟踪": 1}, selected=6, total=6)
    assert len(bar.badge_texts()) == 3

    bar.set_counts({"已修改": 1}, selected=1, total=6)
    assert bar.badge_texts() == ["修改 1"]
    assert bar._total_badge.text() == "已选 1 / 6"


def test_status_badge_bar_empty_counts(qapp):
    """没有文件时只显示总计徽章。"""
    bar = StatusBadgeBar()
    bar.show()
    bar.set_counts({}, 0, 0)
    assert bar.badge_texts() == []
    assert bar._total_badge.text() == "已选 0 / 0"


def test_file_list_view_statistics_by_status(qapp):
    """列表视图按类型统计已勾选数量。"""
    files = [
        FileItem("a.py", "已修改"),
        FileItem("b.py", "已修改"),
        FileItem("c.py", "已删除"),
        FileItem("d.py", "已添加", selected=False),
        FileItem("e.py", "未跟踪"),
    ]
    view = FileListView()
    view.load_files(files)
    view.item(4).setCheckState(0, Qt.CheckState.Unchecked)

    stats = view.get_statistics()
    assert stats["total"] == 5
    assert stats["selected"] == 3
    assert stats["by_status"] == {"已修改": 2, "已删除": 1}


def test_file_tree_view_statistics_by_status(qapp):
    """树形视图按类型统计已勾选数量（只统计文件叶子节点）。"""
    files = [
        FileItem("pkg/a.py", "已修改"),
        FileItem("pkg/b.py", "已删除"),
        FileItem("pkg/sub/c.py", "已删除"),
        FileItem("d.py", "已添加", selected=False),
    ]
    view = FileTreeView()
    view.load_files(files)

    stats = view.get_statistics()
    assert stats["total"] == 4
    assert stats["selected"] == 3
    assert stats["by_status"] == {"已修改": 1, "已删除": 2}


def test_main_window_updates_badges_on_selection_change(qapp):
    """勾选变化后主窗口徽章同步刷新，切换视图同样刷新。"""
    window = MainWindow()
    window.show()
    window.load_files([
        FileItem("a.py", "已修改"),
        FileItem("b.py", "已修改"),
        FileItem("c.py", "已删除"),
        FileItem("d.py", "已添加"),
    ])

    assert window.stats_bar.badge_texts() == ["修改 2", "添加 1", "删除 1"]
    assert window.stats_bar._total_badge.text() == "已选 4 / 4"

    window.file_list_view.item(2).setCheckState(0, Qt.CheckState.Unchecked)
    assert window.stats_bar.badge_texts() == ["修改 2", "添加 1"]
    assert window.stats_bar._total_badge.text() == "已选 3 / 4"

    # 切到树形视图：c.py 重新勾选后徽章随视图数据刷新
    window.tree_view_btn.click()
    assert window.stacked_widget.currentIndex() == 1
    assert window.file_tree_view.get_statistics()["by_status"] == {
        "已修改": 2, "已添加": 1, "已删除": 1,
    }
    assert window.stats_bar.badge_texts() == ["修改 2", "添加 1", "删除 1"]
    assert window.stats_bar._total_badge.text() == "已选 4 / 4"


def test_status_order_is_shared_config():
    """两个视图的状态顺序来自同一配置，保证排序与统计一致。"""
    assert FileListView()._status_order == STATUS_ORDER
    assert FileTreeView()._status_order == STATUS_ORDER
