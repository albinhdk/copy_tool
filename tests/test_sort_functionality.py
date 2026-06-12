import pytest
import sys
from PySide6.QtWidgets import QApplication
from src.models.file_item import FileItem
from src.views.file_list_view import FileListView
from src.views.file_tree_view import FileTreeView


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
    
    # 验证默认顺序（按原始顺序）
    assert view.item(0).text() == "[已修改] file1.py"
    assert view.item(1).text() == "[已添加] file2.py"
    assert view.item(2).text() == "[已删除] file3.py"
    assert view.item(3).text() == "[未跟踪] file4.py"
    assert view.item(4).text() == "[已修改] file5.py"
    
    # 启用按状态排序
    view.set_sort_by_status(True)
    view.load_files(files)
    
    # 验证排序后顺序：已修改、已添加、已删除、未跟踪
    assert view.item(0).text() == "[已修改] file1.py"
    assert view.item(1).text() == "[已修改] file5.py"
    assert view.item(2).text() == "[已添加] file2.py"
    assert view.item(3).text() == "[已删除] file3.py"
    assert view.item(4).text() == "[未跟踪] file4.py"


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


def test_sort_order_consistency(qapp):
    """测试排序顺序一致性"""
    view = FileListView()
    
    # 测试状态顺序
    expected_order = ['已修改', '已添加', '已删除', '已重命名', '已复制', '未跟踪', '已忽略']
    assert view._status_order == expected_order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])