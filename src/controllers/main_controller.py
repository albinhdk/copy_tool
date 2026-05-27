import os
from typing import List
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QTimer
from ..views.main_window import MainWindow
from ..views.diff_dialog import DiffViewerDialog
from ..services.git_service import GitService
from ..services.file_service import FileService
from ..services.config_service import ConfigService
from ..workers.scan_worker import ScanWorker
from ..workers.copy_worker import CopyWorker
from ..utils.logger import logger
from ..config import SCAN_DEBOUNCE_MS


class MainController:
    """主控制器，协调视图和服务层"""
    
    def __init__(self, view: MainWindow, git_service: GitService,
                 file_service: FileService, config_service: ConfigService):
        """
        初始化主控制器
        
        Args:
            view: 主窗口视图
            git_service: Git服务
            file_service: 文件服务
            config_service: 配置服务
        """
        self.view = view
        self.git_service = git_service
        self.file_service = file_service
        self.config_service = config_service
        
        self._scan_worker = None
        self._copy_worker = None
        self._pending_tgt_dir = None
        
        # 防抖定时器
        self._scan_timer = QTimer()
        self._scan_timer.setSingleShot(True)
        self._scan_timer.timeout.connect(self._do_scan)
        
        self._connect_signals()
        self._load_history()
        
        logger.info("应用程序启动")
    
    def _connect_signals(self):
        """连接视图信号到处理方法"""
        self.view.source_changed.connect(self._on_source_changed)
        self.view.scan_requested.connect(self._on_scan_requested)
        self.view.copy_requested.connect(self._on_copy_requested)
        self.view.browse_source_requested.connect(self._on_browse_source)
        self.view.browse_target_requested.connect(self._on_browse_target)
        self.view.filter_history_changed.connect(self._on_filter_history_changed)
        self.view.file_double_clicked.connect(self._on_file_double_clicked)
    
    def _load_history(self):
        """加载历史记录"""
        src_history = self.config_service.get_source_history()
        self.view.set_source_history(src_history)
        
        tgt_history = self.config_service.get_target_history()
        self.view.set_target_history(tgt_history)
        
        filter_history = self.config_service.get_filter_history()
        self.view.set_filter_history(filter_history)
        
        logger.debug(f"加载历史记录: 源目录 {len(src_history)} 条, 目标目录 {len(tgt_history)} 条, 过滤历史 {len(filter_history)} 条")
    
    def _on_source_changed(self, path: str):
        """处理源目录变化（带防抖）"""
        if path and os.path.isdir(path):
            # 重置防抖定时器
            self._scan_timer.start(SCAN_DEBOUNCE_MS)
    
    def _do_scan(self):
        """执行扫描（防抖后）"""
        path = self.view.get_source_path()
        if path:
            self._scan_repository(path)
    
    def _on_scan_requested(self):
        """处理扫描请求（手动刷新，无防抖）"""
        path = self.view.get_source_path()
        if path:
            self._scan_repository(path)
    
    def _scan_repository(self, repo_path: str):
        """异步扫描Git仓库"""
        # 如果已有扫描任务在运行，先等待完成
        if self._scan_worker and self._scan_worker.isRunning():
            logger.debug("扫描任务已在运行，跳过")
            return
        
        # 显示加载状态
        self.view.set_loading(True, "正在扫描Git仓库...")
        
        # 创建并启动工作线程
        self._scan_worker = ScanWorker(self.git_service, repo_path)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()
    
    def _on_scan_finished(self, result):
        """扫描完成回调"""
        self.view.set_loading(False)
        
        if result is None:
            # 扫描失败（错误已在_on_scan_error中处理）
            return
        
        # 更新视图
        self.view.load_files(result.files)
        
        # 保存历史记录
        repo_path = result.repo_path
        self.config_service.save_source_history(repo_path)
        self.view.add_source_to_history(repo_path)
    
    def _on_scan_error(self, error_msg: str):
        """扫描出错回调"""
        logger.error(f"扫描失败: {error_msg}")
        self.view.set_loading(False)
        self.view.show_message("扫描失败", error_msg, QMessageBox.Icon.Warning)
    
    def _on_copy_requested(self):
        """处理拷贝请求"""
        src_dir = self.view.get_source_path()
        tgt_dir = self.view.get_target_path()
        
        # 验证路径
        if not src_dir or not os.path.exists(src_dir):
            self.view.show_message("错误", "源目录无效或不存在！", QMessageBox.Icon.Warning)
            return
        
        if not tgt_dir:
            self.view.show_message("错误", "请选择目标目录！", QMessageBox.Icon.Warning)
            return
        
        # 获取选中的文件
        selected_files = self.view.get_selected_files()
        
        if not selected_files:
            self.view.show_message("提示", "没有选中任何文件。", QMessageBox.Icon.Information)
            return
        
        logger.info(f"用户请求拷贝: {len(selected_files)} 个文件")
        
        # 确认清空目标目录
        if os.path.exists(tgt_dir) and os.listdir(tgt_dir):
            if not self.view.show_question(
                "清空目标目录确认",
                f"将要清空目标目录:\n{tgt_dir}\n\n里面现有的所有文件都会被永久删除！是否继续？"
            ):
                logger.info("用户取消拷贝操作")
                return
            
            try:
                self.file_service.clear_directory(tgt_dir)
            except Exception as e:
                logger.error(f"清空目标目录失败: {e}")
                self.view.show_message("清空失败", f"清空目标目录时发生错误:\n{str(e)}", QMessageBox.Icon.Critical)
                return
        
        # 异步执行拷贝
        self._start_copy(src_dir, tgt_dir, selected_files)
    
    def _start_copy(self, src_dir: str, tgt_dir: str, files: list):
        """异步执行文件拷贝"""
        # 如果已有拷贝任务在运行，先等待完成
        if self._copy_worker and self._copy_worker.isRunning():
            logger.debug("拷贝任务已在运行，跳过")
            return
        
        # 显示加载状态
        self.view.set_loading(True, "正在拷贝文件...")
        self.view.set_copy_button_enabled(False)
        
        # 保存目标路径用于后续使用
        self._pending_tgt_dir = tgt_dir
        
        # 创建并启动工作线程
        self._copy_worker = CopyWorker(self.file_service, src_dir, tgt_dir, files)
        self._copy_worker.finished.connect(self._on_copy_finished)
        self._copy_worker.error.connect(self._on_copy_error)
        self._copy_worker.start()
    
    def _on_copy_finished(self, success_count: int, error_messages: list):
        """拷贝完成回调"""
        self.view.set_loading(False)
        self.view.set_copy_button_enabled(True)
        
        # 保存历史记录
        tgt_dir = self._pending_tgt_dir
        self.config_service.save_target_history(tgt_dir)
        self.view.add_target_to_history(tgt_dir)
        
        # 显示结果
        if error_messages:
            error_str = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_str += f"\n...及其他 {len(error_messages)-5} 个错误"
            logger.warning(f"拷贝完成但有错误: 成功 {success_count}, 失败 {len(error_messages)}")
            self.view.show_message("完成，但有错误", f"成功拷贝 {success_count} 个文件。\n\n部分失败:\n{error_str}", QMessageBox.Icon.Warning)
        else:
            logger.info(f"拷贝成功: {success_count} 个文件")
            self.view.show_message("成功", f"成功拷贝了 {success_count} 个文件！\n\n已保持原始目录结构存放在:\n{tgt_dir}", QMessageBox.Icon.Information)
    
    def _on_copy_error(self, error_msg: str):
        """拷贝出错回调"""
        logger.error(f"拷贝失败: {error_msg}")
        self.view.set_loading(False)
        self.view.set_copy_button_enabled(True)
        self.view.show_message("拷贝失败", f"拷贝文件时发生错误:\n{error_msg}", QMessageBox.Icon.Critical)
    
    def _on_browse_source(self):
        """处理浏览源目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择 Git 源目录")
        if dir_path:
            self.view.set_source_path(dir_path)
            logger.debug(f"用户选择源目录: {dir_path}")
    
    def _on_browse_target(self):
        """处理浏览目标目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择目标目录")
        if dir_path:
            self.view.set_target_path(dir_path)
            logger.debug(f"用户选择目标目录: {dir_path}")
    
    def _on_filter_history_changed(self, history: List[str]):
        """处理过滤历史变化"""
        # 保存到配置服务
        for text in history:
            self.config_service.save_filter_history(text)
        logger.debug(f"保存过滤历史: {len(history)} 条")
    
    def _on_file_double_clicked(self, file_path: str):
        """处理文件双击事件，显示差异"""
        repo_path = self.view.get_source_path()
        
        if not repo_path:
            self.view.show_message("提示", "请先选择Git源目录", QMessageBox.Icon.Information)
            return
        
        logger.info(f"用户双击查看文件差异: {file_path}")
        
        # 获取差异
        diff_content, error = self.git_service.get_file_diff(repo_path, file_path)
        
        if error:
            logger.error(f"获取文件差异失败: {error}")
            self.view.show_message("获取差异失败", error, QMessageBox.Icon.Warning)
            return
        
        # 显示差异对话框
        dialog = DiffViewerDialog(file_path, diff_content, self.view)
        dialog.exec()
