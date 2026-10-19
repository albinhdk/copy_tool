# tests/test_main_controller.py
import pytest
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QSettings
from src.controllers.main_controller import MainController
from src.services.git_service import GitService
from src.services.file_service import FileService
from src.services.config_service import ConfigService
from src.models.file_item import FileItem
from src.models.git_status import GitStatus


@pytest.fixture
def mock_view():
    """创建模拟的视图对象"""
    view = Mock()
    view.src_input = Mock()
    view.tgt_input = Mock()
    view.file_list_view = Mock()
    view.file_tree_view = Mock()
    view.get_source_path = Mock(return_value="")
    view.get_target_path = Mock(return_value="")
    view.get_selected_files = Mock(return_value=[])
    view.get_structure_root = Mock(return_value="")
    view.set_source_history = Mock()
    view.set_target_history = Mock()
    view.add_source_to_history = Mock()
    view.add_target_to_history = Mock()
    view.load_files = Mock()
    view.set_loading = Mock()
    view.set_copy_button_enabled = Mock()
    view.copy_directory_to_clipboard = Mock()
    view.show_message = Mock()
    view.show_question = Mock(return_value=True)
    view.set_source_path = Mock()
    view.set_target_path = Mock()
    view.set_structure_root_options = Mock()
    view.add_structure_root_option = Mock()
    return view


@pytest.fixture
def config_service():
    """创建临时配置服务实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = QSettings(os.path.join(tmpdir, "test.ini"), QSettings.Format.IniFormat)
        service = ConfigService(settings)
        yield service


@pytest.fixture
def controller(mock_view, config_service):
    """创建控制器实例"""
    git_service = GitService()
    file_service = FileService()
    return MainController(mock_view, git_service, file_service, config_service)


# ========== 历史记录加载测试 ==========

def test_load_history_on_init(mock_view, config_service):
    """测试初始化时加载历史记录"""
    # 预设历史记录
    config_service.save_source_history("/source/path")
    config_service.save_target_history("/target/path")
    
    git_service = GitService()
    file_service = FileService()
    
    controller = MainController(mock_view, git_service, file_service, config_service)
    
    # 验证历史记录被加载
    mock_view.set_source_history.assert_called_once()
    mock_view.set_target_history.assert_called_once()


# ========== 目录历史删除/清空持久化测试 ==========

def test_on_source_history_changed_persists(controller, config_service):
    """测试源目录历史变化后整体重写持久化"""
    config_service.save_source_history("/old/repo")
    
    controller._on_source_history_changed(["/new/repo"])
    
    assert config_service.get_source_history() == ["/new/repo"]


def test_on_target_history_changed_persists(controller, config_service):
    """测试目标目录历史变化后整体重写持久化"""
    config_service.save_target_history("/old/target")
    
    controller._on_target_history_changed([])
    
    assert config_service.get_target_history() == []


# ========== 扫描请求测试 ==========

def test_on_scan_requested_empty_path(controller, mock_view):
    """测试扫描请求时路径为空"""
    mock_view.get_source_path.return_value = ""
    
    controller._on_scan_requested()
    
    # 不应该触发扫描
    mock_view.set_loading.assert_not_called()


def test_on_scan_requested_valid_path(controller, mock_view):
    """测试扫描请求时路径有效"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_view.get_source_path.return_value = tmpdir
        
        # 模拟GitService返回结果
        with patch.object(controller.git_service, 'scan_repository') as mock_scan:
            mock_scan.return_value = (GitStatus(tmpdir, []), None)
            
            controller._on_scan_requested()
            
            # 验证加载状态被设置
            mock_view.set_loading.assert_any_call(True, "正在扫描Git仓库...")


# ========== 拷贝请求验证测试 ==========

def test_on_copy_requested_no_source(controller, mock_view):
    """测试拷贝请求时源目录无效"""
    mock_view.get_source_path.return_value = ""
    
    controller._on_copy_requested()
    
    mock_view.show_message.assert_called_once()
    assert "源目录" in mock_view.show_message.call_args[0][1]


def test_on_copy_requested_no_target(controller, mock_view):
    """测试拷贝请求时目标目录为空"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, ".git"))
        mock_view.get_source_path.return_value = tmpdir
        mock_view.get_target_path.return_value = ""
        
        controller._on_copy_requested()
        
        mock_view.show_message.assert_called_once()
        assert "目标目录" in mock_view.show_message.call_args[0][1]


def test_on_copy_requested_no_files_selected(controller, mock_view):
    """测试拷贝请求时没有选中文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, ".git"))
        mock_view.get_source_path.return_value = tmpdir
        mock_view.get_target_path.return_value = "/target/path"
        mock_view.get_selected_files.return_value = []
        
        controller._on_copy_requested()
        
        mock_view.show_message.assert_called_once()
        assert "没有选中" in mock_view.show_message.call_args[0][1]


def test_scan_finished_populates_detected_structure_roots(controller, mock_view):
    """测试扫描完成后提供自动识别的目录结构起点。"""
    result = GitStatus(
        "C:/work/java-app",
        [FileItem("src/main/java/com/demo/App.java", "已修改")],
    )

    controller._on_scan_finished(result)

    mock_view.set_structure_root_options.assert_called_once()
    candidates, auto_root, selected_root = mock_view.set_structure_root_options.call_args[0]
    assert "src/main/java" in candidates
    assert auto_root == "src/main/java"
    assert selected_root is None


def test_copy_collision_is_reported_before_target_is_cleared(controller, mock_view):
    """测试路径冲突在清理目标目录前终止。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = os.path.join(tmpdir, "repo")
        target_dir = os.path.join(tmpdir, "target")
        os.makedirs(os.path.join(repo_dir, ".git"))
        os.makedirs(target_dir)
        with open(os.path.join(target_dir, "keep.txt"), "w") as f:
            f.write("keep")

        mock_view.get_source_path.return_value = repo_dir
        mock_view.get_target_path.return_value = target_dir
        mock_view.get_structure_root.return_value = "src"
        mock_view.get_selected_files.return_value = [
            "src/config/app.yml",
            "config/app.yml",
        ]

        controller._on_copy_requested()

        assert os.path.exists(os.path.join(target_dir, "keep.txt"))
        assert "冲突" in mock_view.show_message.call_args[0][0]


def test_copy_to_clipboard_requested_starts_copy_with_clipboard_flag(controller):
    """测试“拷贝到内存”会复用拷贝流程并携带剪贴板标记。"""
    with patch.object(controller, '_on_copy_requested') as mock_copy:
        controller._on_copy_to_clipboard_requested()

    mock_copy.assert_called_once_with(copy_to_clipboard=True)


def test_copy_finished_places_target_directory_on_clipboard(controller, mock_view):
    """测试拷贝完全成功后将目标目录放入剪贴板并提示路径。"""
    target_dir = os.path.normpath("C:/target/copied-files")
    controller._pending_tgt_dir = target_dir
    controller._copy_target_to_clipboard = True

    controller._on_copy_finished(3, [])

    mock_view.copy_directory_to_clipboard.assert_called_once_with(target_dir)
    message = mock_view.show_message.call_args[0][1]
    assert target_dir in message
    assert "可直接粘贴" in message


def test_copy_finished_with_errors_does_not_update_clipboard(controller, mock_view):
    """测试存在文件拷贝错误时不把不完整目录放入剪贴板。"""
    controller._pending_tgt_dir = os.path.normpath("C:/target/copied-files")
    controller._copy_target_to_clipboard = True

    controller._on_copy_finished(2, ["failed.txt"])

    mock_view.copy_directory_to_clipboard.assert_not_called()


# ========== 浏览目录测试 ==========

def test_on_browse_source(controller, mock_view):
    """测试浏览源目录"""
    with patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
        mock_dialog.return_value = "/selected/path"
        
        controller._on_browse_source()
        
        mock_view.set_source_path.assert_called_once_with("/selected/path")


def test_on_browse_source_cancelled(controller, mock_view):
    """测试取消浏览源目录"""
    with patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
        mock_dialog.return_value = ""
        
        controller._on_browse_source()
        
        mock_view.set_source_path.assert_not_called()


def test_on_browse_target(controller, mock_view):
    """测试浏览目标目录"""
    with patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
        mock_dialog.return_value = "/selected/target"
        
        controller._on_browse_target()
        
        mock_view.set_target_path.assert_called_once_with("/selected/target")


# ========== 防抖机制测试 ==========

def test_debounce_mechanism(controller, mock_view):
    """测试防抖机制"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_view.get_source_path.return_value = tmpdir
        
        # 快速连续触发多次
        controller._on_source_changed(tmpdir)
        controller._on_source_changed(tmpdir)
        controller._on_source_changed(tmpdir)
        
        # 定时器应该被重启，而不是立即扫描
        assert not controller._scan_timer.isActive() or controller._scan_timer.remainingTime() > 0
