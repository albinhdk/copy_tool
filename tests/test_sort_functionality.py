import pytest
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.models.file_item import FileItem
from src.views.file_list_view import FileListView
from src.views.file_tree_view import FileTreeView
from src.views.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_file_list_view_sort_by_status(qapp):
    """测试FileListView按状态排序功能"""
    # 创建测试文件列表
    files = [
        FileItem("file1.py", "已修改"),
        FileItem("file2.py", "已添加"),
        FileItem("file3.py", "已删除"),
        FileItem("file4.py", "未跟踪"),
        FileItem("file5.py", "已修改"),
    ]
    
    # 测试默认不排序
    view = FileListView()
    view.load_files(files)
    
    # 验证默认顺序（按原始顺序）：状态独立成列，文件路径列不带状态前缀
    assert view.item(0).text(0) == "file1.py"
    assert view.item(0).text(1) == "已修改"
    assert view.item(1).text(1) == "已添加"
    assert view.item(2).text(1) == "已删除"
    assert view.item(3).text(1) == "未跟踪"
    assert view.item(4).text(1) == "已修改"
    
    # 启用按状态排序
    view.set_sort_by_status(True)
    view.load_files(files)
    
    # 验证排序后顺序：已修改、已添加、已删除、未跟踪
    assert view.item(0).text(1) == "已修改"
    assert view.item(1).text(1) == "已修改"
    assert view.item(2).text(1) == "已添加"
    assert view.item(3).text(1) == "已删除"
    assert view.item(4).text(1) == "未跟踪"


def test_file_list_view_displays_and_sorts_by_modified_time(qapp):
    """最后修改时间列支持降序、升序，并保留勾选状态。"""
    files = [
        FileItem("old.py", "已修改", modified_time=100.0),
        FileItem("deleted.py", "已删除"),
        FileItem("new.py", "已添加", modified_time=300.0),
    ]
    view = FileListView()
    view.load_files(files)
    view.item(0).setCheckState(0, Qt.CheckState.Unchecked)

    assert view.headerItem().text(1) == "状态"
    assert view.headerItem().text(2) == "最后修改时间"
    assert view.item(1).text(2) == "—"

    view.header().sectionClicked.emit(2)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["new.py", "old.py", "deleted.py"]
    assert view.get_selected_files() == ["new.py", "deleted.py"]

    view.header().sectionClicked.emit(2)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["old.py", "new.py", "deleted.py"]


def test_file_tree_view_sort_by_status(qapp):
    """测试FileTreeView按状态排序功能"""
    # 创建测试文件列表
    files = [
        FileItem("dir1/file1.py", "已修改"),
        FileItem("dir1/file2.py", "已添加"),
        FileItem("dir2/file3.py", "已删除"),
        FileItem("file4.py", "未跟踪"),
    ]
    
    # 测试默认不排序
    view = FileTreeView()
    view.load_files(files)
    
    # 启用按状态排序
    view.set_sort_by_status(True)
    view.load_files(files)
    
    # 验证排序功能正常工作（不抛出异常）
    assert view.topLevelItemCount() > 0


def test_file_tree_view_displays_modified_time(qapp):
    """树形视图为文件节点显示最后修改时间，目录节点留空。"""
    files = [
        FileItem("pkg/a.py", "已修改", modified_time=100.0),
        FileItem("pkg/deleted.py", "已删除"),
    ]
    view = FileTreeView()
    view.load_files(files)

    assert view.headerItem().text(2) == "最后修改时间"
    pkg = view.topLevelItem(0)
    assert pkg.text(2) == ""
    assert pkg.child(0).text(2) == FileItem("a.py", "", modified_time=100.0).get_modified_time_text()
    assert pkg.child(1).text(2) == "—"


def test_file_item_modified_time_text():
    """时间文本按本地时间格式化，缺失时用占位符。"""
    assert FileItem("a.py", "已修改").get_modified_time_text() == "—"
    assert FileItem("a.py", "已修改", modified_time=100.0).get_modified_time_text() != "—"


def test_sort_order_consistency(qapp):
    """测试排序顺序一致性"""
    view = FileListView()
    
    # 测试状态顺序
    expected_order = ['已修改', '已添加', '已删除', '已重命名', '已复制', '未跟踪', '已忽略']
    assert view._status_order == expected_order


def test_file_list_view_sort_by_path(qapp):
    """点击文件路径表头按路径升/降序排序，并保留勾选状态。"""
    files = [
        FileItem("src/b.py", "已修改"),
        FileItem("src/a.py", "已添加"),
        FileItem("README.md", "未跟踪"),
    ]
    view = FileListView()
    view.load_files(files)
    view.item(0).setCheckState(0, Qt.CheckState.Unchecked)  # src/b.py 取消勾选

    view.header().sectionClicked.emit(0)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["README.md", "src/a.py", "src/b.py"]
    # 重排后勾选状态保留
    assert view.get_selected_files() == ["README.md", "src/a.py"]

    view.header().sectionClicked.emit(0)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["src/b.py", "src/a.py", "README.md"]


def test_file_list_view_sort_by_status_header(qapp):
    """点击状态表头按预设状态顺序排序，未知状态始终排在末尾。"""
    files = [
        FileItem("f1.py", "未跟踪"),
        FileItem("f2.py", "已修改"),
        FileItem("f3.py", "奇怪状态"),
        FileItem("f4.py", "已添加"),
    ]
    view = FileListView()
    view.load_files(files)

    view.header().sectionClicked.emit(1)
    assert [view.item(index).text(1) for index in range(view.count())] == [
        "已修改", "已添加", "未跟踪", "奇怪状态",
    ]

    view.header().sectionClicked.emit(1)
    assert [view.item(index).text(1) for index in range(view.count())] == [
        "未跟踪", "已添加", "已修改", "奇怪状态",
    ]


def test_file_list_view_sort_survives_reload(qapp):
    """表头排序状态在重新加载（过滤、刷新）后保持。"""
    files = [
        FileItem("b.py", "已修改", modified_time=100.0),
        FileItem("a.py", "已修改", modified_time=200.0),
    ]
    view = FileListView()
    view.load_files(files)

    view.header().sectionClicked.emit(2)  # 时间降序
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["a.py", "b.py"]

    view.load_files(files)  # 重新加载后仍保持时间降序
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["a.py", "b.py"]
    assert view.header().sortIndicatorSection() == 2


def test_file_list_view_status_button_and_header_interaction(qapp):
    """“按类型排序”按钮与状态表头点击互相联动。"""
    files = [
        FileItem("f1.py", "未跟踪"),
        FileItem("f2.py", "已修改"),
    ]
    view = FileListView()
    view.load_files(files)

    # 按钮启用状态排序（升序），并在状态列显示排序箭头
    view.set_sort_by_status(True)
    view.load_files(files)
    assert [view.item(index).text(1) for index in range(view.count())] == [
        "已修改", "未跟踪",
    ]
    assert view.header().sortIndicatorSection() == 1
    assert view.header().sortIndicatorOrder() == Qt.SortOrder.AscendingOrder

    # 点击状态表头切换到降序，并发出信号通知主窗口
    signals = []
    view.header_sort_activated.connect(
        lambda column, ascending: signals.append((column, ascending))
    )
    view.header().sectionClicked.emit(1)
    assert [view.item(index).text(1) for index in range(view.count())] == [
        "未跟踪", "已修改",
    ]
    assert signals == [(1, False)]

    # 再次点击恢复升序
    view.header().sectionClicked.emit(1)
    assert signals == [(1, False), (1, True)]

    # 取消按钮选中后恢复原始顺序
    view.set_sort_by_status(False)
    view.load_files(files)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["f1.py", "f2.py"]
    assert not view.header().isSortIndicatorShown()


def test_file_list_view_button_off_keeps_header_sort(qapp):
    """取消“按类型排序”不影响通过表头设置的其它列排序。"""
    files = [
        FileItem("b.py", "已修改"),
        FileItem("a.py", "已添加"),
    ]
    view = FileListView()
    view.load_files(files)
    view.header().sectionClicked.emit(0)  # 路径升序

    view.set_sort_by_status(False)
    view.load_files(files)
    assert [
        view.item(index).data(0, Qt.ItemDataRole.UserRole)
        for index in range(view.count())
    ] == ["a.py", "b.py"]


def test_main_window_syncs_sort_button_with_header_sort(qapp):
    """表头排序与“按类型排序”按钮、树形视图状态保持同步。"""
    window = MainWindow()
    window.load_files([
        FileItem("a.py", "未跟踪"),
        FileItem("b.py", "已修改"),
    ])

    # 点击状态表头升序：按钮与树形视图同步进入按状态排序
    window.file_list_view.header().sectionClicked.emit(1)
    assert window.sort_by_status_btn.isChecked()
    assert window.file_tree_view._sort_by_status

    # 再次点击切到降序：按钮与树形视图同步退出
    window.file_list_view.header().sectionClicked.emit(1)
    assert not window.sort_by_status_btn.isChecked()
    assert not window.file_tree_view._sort_by_status

    # 点击其它列同样取消按钮选中
    window.sort_by_status_btn.click()
    assert window.sort_by_status_btn.isChecked()
    window.file_list_view.header().sectionClicked.emit(0)
    assert not window.sort_by_status_btn.isChecked()
    assert not window.file_tree_view._sort_by_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])