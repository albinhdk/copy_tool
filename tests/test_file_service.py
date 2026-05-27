# tests/test_file_service.py
import pytest
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.file_service import FileService

@pytest.fixture
def file_service():
    """创建FileService实例"""
    return FileService()

@pytest.fixture
def temp_dirs():
    """创建临时源目录和目标目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(src_dir)
        os.makedirs(tgt_dir)
        
        # 创建测试文件结构
        os.makedirs(os.path.join(src_dir, "subdir"))
        with open(os.path.join(src_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(src_dir, "subdir", "file2.txt"), "w") as f:
            f.write("content2")
        
        yield src_dir, tgt_dir

def test_copy_files_success(file_service, temp_dirs):
    """测试成功拷贝文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["file1.txt", "subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 2
    assert len(errors) == 0
    assert os.path.exists(os.path.join(tgt_dir, "file1.txt"))
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))
    
    # 验证内容
    with open(os.path.join(tgt_dir, "file1.txt")) as f:
        assert f.read() == "content1"

def test_copy_files_preserve_structure(file_service, temp_dirs):
    """测试保持目录结构"""
    src_dir, tgt_dir = temp_dirs
    files = ["subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 1
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))

def test_copy_files_nonexistent(file_service, temp_dirs):
    """测试拷贝不存在的文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["nonexistent.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 0
    assert len(errors) == 0  # 不存在的文件被静默跳过

def test_clear_directory(file_service, temp_dirs):
    """测试清空目录"""
    _, tgt_dir = temp_dirs
    
    # 创建一些文件
    with open(os.path.join(tgt_dir, "test.txt"), "w") as f:
        f.write("test")
    os.makedirs(os.path.join(tgt_dir, "subdir"))
    
    file_service.clear_directory(tgt_dir)
    
    # 验证目录为空
    assert len(os.listdir(tgt_dir)) == 0

def test_clear_nonexistent_directory(file_service):
    """测试清空不存在的目录"""
    # 应该不抛出异常
    file_service.clear_directory("/nonexistent/path")