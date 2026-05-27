# tests/test_git_service.py
import pytest
import sys
import os
import tempfile
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.git_service import GitService

# ========== 状态解析测试 ==========

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

# ========== scan_repository测试 ==========

def test_scan_repository_invalid_path():
    """测试扫描无效路径"""
    service = GitService()
    result, error = service.scan_repository("/nonexistent/path")
    assert result is None
    assert error is not None
    assert "不存在" in error

def test_scan_repository_not_git_dir():
    """测试扫描非Git目录"""
    service = GitService()
    with tempfile.TemporaryDirectory() as tmpdir:
        result, error = service.scan_repository(tmpdir)
        assert result is None
        assert error is not None
        assert "不是Git仓库" in error

def test_scan_repository_empty_path():
    """测试扫描空路径"""
    service = GitService()
    result, error = service.scan_repository("")
    assert result is None
    assert error is not None

def test_scan_repository_valid_git_repo():
    """测试扫描有效的Git仓库"""
    service = GitService()
    with tempfile.TemporaryDirectory() as tmpdir:
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        
        # 创建一个文件
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        result, error = service.scan_repository(tmpdir)
        assert error is None
        assert result is not None
        assert result.repo_path == tmpdir
        assert len(result.files) == 1
        assert result.files[0].relative_path == "test.txt"
        assert result.files[0].status == "未跟踪"

def test_scan_repository_with_modified_file():
    """测试扫描包含修改文件的Git仓库"""
    service = GitService()
    with tempfile.TemporaryDirectory() as tmpdir:
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        
        # 创建并提交一个文件
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("original content")
        subprocess.run(["git", "add", "test.txt"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)
        
        # 修改文件
        with open(test_file, "w") as f:
            f.write("modified content")
        
        result, error = service.scan_repository(tmpdir)
        assert error is None
        assert result is not None
        assert len(result.files) == 1
        assert result.files[0].relative_path == "test.txt"
        assert result.files[0].status == "已修改"
