# tests/test_git_status.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.file_item import FileItem
from src.models.git_status import GitStatus

def test_git_status_creation():
    """测试GitStatus对象创建"""
    files = [
        FileItem("file1.txt", "已修改"),
        FileItem("file2.txt", "已添加")
    ]
    status = GitStatus("/path/to/repo", files)
    assert status.repo_path == "/path/to/repo"
    assert len(status.files) == 2

def test_git_status_get_selected_files():
    """测试获取选中的文件"""
    files = [
        FileItem("file1.txt", "已修改", True),
        FileItem("file2.txt", "已添加", False),
        FileItem("file3.txt", "未跟踪", True)
    ]
    status = GitStatus("/repo", files)
    selected = status.get_selected_files()
    assert len(selected) == 2
    assert "file1.txt" in selected
    assert "file3.txt" in selected

def test_git_status_get_statistics():
    """测试获取统计信息"""
    files = [
        FileItem("file1.txt", "已修改", True),
        FileItem("file2.txt", "已添加", False),
        FileItem("file3.txt", "未跟踪", True)
    ]
    status = GitStatus("/repo", files)
    stats = status.get_statistics()
    assert stats["total"] == 3
    assert stats["selected"] == 2

def test_git_status_empty_files():
    """测试空文件列表"""
    status = GitStatus("/repo", [])
    assert status.get_selected_files() == []
    assert status.get_statistics() == {"total": 0, "selected": 0}