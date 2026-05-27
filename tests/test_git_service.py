# tests/test_git_service.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.git_service import GitService

def test_parse_status_line_modified():
    """测试解析修改状态"""
    service = GitService()
    item = service._parse_status_line("M  file.txt")
    assert item.relative_path == "file.txt"
    assert item.status == "已修改"

def test_parse_status_line_added():
    """测试解析添加状态"""
    service = GitService()
    item = service._parse_status_line("A  new_file.py")
    assert item.relative_path == "new_file.py"
    assert item.status == "已添加"

def test_parse_status_line_untracked():
    """测试解析未跟踪状态"""
    service = GitService()
    item = service._parse_status_line("?? temp.txt")
    assert item.relative_path == "temp.txt"
    assert item.status == "未跟踪"

def test_parse_status_line_renamed():
    """测试解析重命名状态"""
    service = GitService()
    item = service._parse_status_line("R  old.txt -> new.txt")
    assert item.relative_path == "new.txt"
    assert item.status == "已重命名"

def test_parse_status_line_deleted():
    """测试解析删除状态"""
    service = GitService()
    item = service._parse_status_line("D  deleted.txt")
    assert item.relative_path == "deleted.txt"
    assert item.status == "已删除"

def test_parse_status_line_invalid():
    """测试解析无效行"""
    service = GitService()
    item = service._parse_status_line("X")
    assert item is None

def test_get_status_label():
    """测试状态标签映射"""
    service = GitService()
    assert service._get_status_label("M ") == "已修改"
    assert service._get_status_label(" M") == "已修改"
    assert service._get_status_label("A ") == "已添加"
    assert service._get_status_label("??") == "未跟踪"
    assert service._get_status_label("D ") == "已删除"
    assert service._get_status_label("R ") == "已重命名"
    assert service._get_status_label("XX") == "XX"  # 未知状态返回原值