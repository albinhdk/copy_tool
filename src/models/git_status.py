from typing import List, Dict
from .file_item import FileItem

class GitStatus:
    """Git状态模型，封装仓库的文件状态信息"""
    
    def __init__(self, repo_path: str, files: List[FileItem]):
        """
        初始化Git状态
        
        Args:
            repo_path: 仓库根目录路径
            files: 文件项列表
        """
        self.repo_path = repo_path
        self.files = files
    
    def get_selected_files(self) -> List[str]:
        """获取所有选中的文件路径列表"""
        return [f.relative_path for f in self.files if f.selected]
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        total = len(self.files)
        selected = sum(1 for f in self.files if f.selected)
        return {"total": total, "selected": selected}