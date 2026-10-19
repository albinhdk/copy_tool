# tests/test_config_service.py
import pytest
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtCore import QSettings
from src.services.config_service import ConfigService

@pytest.fixture
def config_service():
    """创建临时配置服务实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = QSettings(os.path.join(tmpdir, "test.ini"), QSettings.Format.IniFormat)
        service = ConfigService(settings)
        yield service

# ========== 源目录历史记录测试 ==========

def test_get_source_history_empty(config_service):
    """测试获取空源目录历史"""
    history = config_service.get_source_history()
    assert history == []

def test_save_and_get_source_history(config_service):
    """测试保存和获取源目录历史"""
    config_service.save_source_history("/path/to/repo1")
    config_service.save_source_history("/path/to/repo2")
    
    history = config_service.get_source_history()
    assert len(history) == 2
    assert history[0] == "/path/to/repo2"  # 最新的在前
    assert history[1] == "/path/to/repo1"

def test_source_history_max_items(config_service):
    """测试历史记录最大数量限制"""
    for i in range(15):
        config_service.save_source_history(f"/repo/{i}")
    
    history = config_service.get_source_history()
    assert len(history) == 10  # 最多保留10条
    assert history[0] == "/repo/14"  # 最新的在前

def test_source_history_dedup(config_service):
    """测试历史记录去重"""
    config_service.save_source_history("/repo1")
    config_service.save_source_history("/repo2")
    config_service.save_source_history("/repo1")  # 重复
    
    history = config_service.get_source_history()
    assert len(history) == 2
    assert history[0] == "/repo1"  # 移到最前

def test_save_source_history_empty_path(config_service):
    """测试保存空路径"""
    config_service.save_source_history("")
    history = config_service.get_source_history()
    assert history == []

# ========== 目标目录历史记录测试 ==========

def test_get_target_history_empty(config_service):
    """测试获取空目标目录历史"""
    history = config_service.get_target_history()
    assert history == []

def test_save_and_get_target_history(config_service):
    """测试保存和获取目标目录历史"""
    config_service.save_target_history("/path/to/target1")
    config_service.save_target_history("/path/to/target2")
    
    history = config_service.get_target_history()
    assert len(history) == 2
    assert history[0] == "/path/to/target2"  # 最新的在前
    assert history[1] == "/path/to/target1"

def test_target_history_max_items(config_service):
    """测试目标目录历史记录最大数量限制"""
    for i in range(15):
        config_service.save_target_history(f"/target/{i}")
    
    history = config_service.get_target_history()
    assert len(history) == 10  # 最多保留10条
    assert history[0] == "/target/14"  # 最新的在前

def test_target_history_dedup(config_service):
    """测试目标目录历史记录去重"""
    config_service.save_target_history("/target1")
    config_service.save_target_history("/target2")
    config_service.save_target_history("/target1")  # 重复
    
    history = config_service.get_target_history()
    assert len(history) == 2
    assert history[0] == "/target1"  # 移到最前

def test_save_target_history_empty_path(config_service):
    """测试保存空目标路径"""
    config_service.save_target_history("")
    history = config_service.get_target_history()
    assert history == []

# ========== 源和目标独立性测试 ==========

def test_source_and_target_independent(config_service):
    """测试源和目标历史记录相互独立"""
    config_service.save_source_history("/source")
    config_service.save_target_history("/target")
    
    src_history = config_service.get_source_history()
    tgt_history = config_service.get_target_history()
    
    assert len(src_history) == 1
    assert len(tgt_history) == 1
    assert src_history[0] == "/source"
    assert tgt_history[0] == "/target"

# ========== 自定义max_items测试 ==========

def test_custom_max_items(config_service):
    """测试自定义最大记录数量"""
    for i in range(5):
        config_service.save_source_history(f"/repo/{i}", max_items=3)
    
    history = config_service.get_source_history()
    assert len(history) == 3
    assert history[0] == "/repo/4"

# ========== 整体重写历史记录测试（删除/清空场景） ==========

def test_replace_source_history(config_service):
    """测试整体重写源目录历史"""
    config_service.save_source_history("/repo1")
    config_service.save_source_history("/repo2")
    
    config_service.replace_source_history(["/repo2"])
    
    history = config_service.get_source_history()
    assert history == ["/repo2"]

def test_replace_target_history(config_service):
    """测试整体重写目标目录历史"""
    config_service.save_target_history("/target1")
    config_service.save_target_history("/target2")
    
    config_service.replace_target_history(["/target1", "/target3"])
    
    history = config_service.get_target_history()
    assert history == ["/target1", "/target3"]

def test_clear_source_history_via_replace(config_service):
    """测试清空源目录历史"""
    config_service.save_source_history("/repo1")
    
    config_service.replace_source_history([])
    
    assert config_service.get_source_history() == []

def test_clear_target_history_via_replace(config_service):
    """测试清空目标目录历史"""
    config_service.save_target_history("/target1")
    
    config_service.replace_target_history([])
    
    assert config_service.get_target_history() == []

def test_replace_source_then_save_keeps_order(config_service):
    """测试重写后继续保存，新条目仍在最前"""
    config_service.replace_source_history(["/repo_old"])
    config_service.save_source_history("/repo_new")
    
    history = config_service.get_source_history()
    assert history == ["/repo_new", "/repo_old"]


def test_structure_root_is_saved_per_repository(config_service):
    """不同仓库分别保存目录结构起点。"""
    config_service.save_structure_root("C:/work/vue-app", "src")
    config_service.save_structure_root("C:/work/java-app", "src/main/java")

    assert config_service.get_structure_root("C:/work/vue-app") == "src"
    assert config_service.get_structure_root("C:/work/java-app") == "src/main/java"


def test_structure_root_returns_none_when_not_configured(config_service):
    """未手动选择时返回 None，以便控制器采用自动识别。"""
    assert config_service.get_structure_root("C:/work/new-app") is None
