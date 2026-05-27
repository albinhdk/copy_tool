from PySide6.QtCore import QThread, Signal
from typing import List
from ..services.file_service import FileService


class CopyWorker(QThread):
    """异步拷贝文件的工作线程"""
    
    # 信号定义
    finished = Signal(int, list)  # 拷贝完成，传递成功数量和错误列表
    error = Signal(str)           # 拷贝出错，传递错误信息
    
    def __init__(self, file_service: FileService, source_dir: str, 
                 target_dir: str, files: List[str], parent=None):
        """
        初始化拷贝工作线程
        
        Args:
            file_service: 文件服务实例
            source_dir: 源目录
            target_dir: 目标目录
            files: 要拷贝的文件列表
            parent: 父对象
        """
        super().__init__(parent)
        self.file_service = file_service
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.files = files
    
    def run(self):
        """执行拷贝"""
        try:
            success_count, error_messages = self.file_service.copy_files(
                self.source_dir, self.target_dir, self.files
            )
            self.finished.emit(success_count, error_messages)
        except Exception as e:
            self.error.emit(str(e))
