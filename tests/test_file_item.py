# tests/test_file_item.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.file_item import FileItem

def test_file_item_creation():
    """测试FileItem对象创建"""
    item = FileItem("src/main.py", "已修改", True)
    assert item.relative_path == "src/main.py"
    assert item.status == "已修改"
    assert item.selected == True

def test_file_item_default_selected():
    """测试FileItem默认选中状态"""
    item = FileItem("test.txt", "未跟踪")
    assert item.selected == True

def test_file_item_display_text():
    """测试显示文本格式"""
    item = FileItem("src/main.py", "已修改")
    assert item.get_display_text() == "[已修改] src/main.py"

def test_file_item_str_representation():
    """测试字符串表示"""
    item = FileItem("test.txt", "已添加")
    assert str(item) == "[已添加] test.txt"