import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from ..views.main_window import MainWindow
from ..services.git_service import GitService
from ..services.file_service import FileService
from ..services.config_service import ConfigService

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
        
        self._connect_signals()
        self._load_history()
    
    def _connect_signals(self):
        """连接视图信号到处理方法"""
        self.view.source_changed.connect(self._on_source_changed)
        self.view.scan_requested.connect(self._on_scan_requested)
        self.view.copy_requested.connect(self._on_copy_requested)
        self.view.browse_source_requested.connect(self._on_browse_source)
        self.view.browse_target_requested.connect(self._on_browse_target)
    
    def _load_history(self):
        """加载历史记录"""
        src_history = self.config_service.get_source_history()
        self.view.src_input.load_history(src_history)
        
        tgt_history = self.config_service.get_target_history()
        self.view.tgt_input.load_history(tgt_history)
    
    def _on_source_changed(self, path: str):
        """处理源目录变化"""
        if path and os.path.isdir(path):
            self._scan_repository(path)
    
    def _on_scan_requested(self):
        """处理扫描请求"""
        path = self.view.src_input.currentText().strip()
        if path:
            self._scan_repository(path)
    
    def _scan_repository(self, repo_path: str):
        """扫描Git仓库"""
        git_status = self.git_service.scan_repository(repo_path)
        
        if git_status is None:
            return
        
        # 更新视图
        self.view.file_list_view.load_files(git_status.files)
        self.view.file_tree_view.load_files(git_status.files)
        
        # 保存历史记录
        self.config_service.save_source_history(repo_path)
        self.view.src_input.add_to_history(repo_path)
    
    def _on_copy_requested(self):
        """处理拷贝请求"""
        src_dir = self.view.src_input.currentText().strip()
        tgt_dir = self.view.tgt_input.currentText().strip()
        
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
        
        # 确认清空目标目录
        if os.path.exists(tgt_dir) and os.listdir(tgt_dir):
            if not self.view.show_question(
                "清空目标目录确认",
                f"将要清空目标目录:\n{tgt_dir}\n\n里面现有的所有文件都会被永久删除！是否继续？"
            ):
                return
            
            try:
                self.file_service.clear_directory(tgt_dir)
            except Exception as e:
                self.view.show_message("清空失败", f"清空目标目录时发生错误:\n{str(e)}", QMessageBox.Icon.Critical)
                return
        
        # 执行拷贝
        success_count, error_messages = self.file_service.copy_files(src_dir, tgt_dir, selected_files)
        
        # 保存历史记录
        self.config_service.save_target_history(tgt_dir)
        self.view.tgt_input.add_to_history(tgt_dir)
        
        # 显示结果
        if error_messages:
            error_str = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_str += f"\n...及其他 {len(error_messages)-5} 个错误"
            self.view.show_message("完成，但有错误", f"成功拷贝 {success_count} 个文件。\n\n部分失败:\n{error_str}", QMessageBox.Icon.Warning)
        else:
            self.view.show_message("成功", f"成功拷贝了 {success_count} 个文件！\n\n已保持原始目录结构存放在:\n{tgt_dir}", QMessageBox.Icon.Information)
    
    def _on_browse_source(self):
        """处理浏览源目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择 Git 源目录")
        if dir_path:
            self.view.src_input.setCurrentText(dir_path)
    
    def _on_browse_target(self):
        """处理浏览目标目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择目标目录")
        if dir_path:
            self.view.tgt_input.setCurrentText(dir_path)