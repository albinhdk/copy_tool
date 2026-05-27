from PySide6.QtCore import QThread, Signal
from typing import Optional
from ..models.git_status import GitStatus
from ..services.git_service import GitService


class ScanWorker(QThread):
    """异步扫描Git仓库的工作线程"""
    
    # 信号定义
    finished = Signal(object)  # 扫描完成，传递GitStatus或None
    error = Signal(str)        # 扫描出错，传递错误信息
    
    def __init__(self, git_service: GitService, repo_path: str, parent=None):
        """
        初始化扫描工作线程
        
        Args:
            git_service: Git服务实例
            repo_path: 仓库路径
            parent: 父对象
        """
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
    
    def run(self):
        """执行扫描"""
        try:
            result, error_msg = self.git_service.scan_repository(self.repo_path)
            if error_msg:
                self.error.emit(error_msg)
            else:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
