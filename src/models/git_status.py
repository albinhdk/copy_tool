from typing import List, Dict
from .file_item import FileItem

class GitStatus:
    """Git状态模型，封装仓库的文件状态信息"""
    
    def __init__(self, repo_path: str, files: List[FileItem], branch: str = ""):
        """
        初始化Git状态
        
        Args:
            repo_path: 仓库根目录路径
            files: 文件项列表
            branch: 当前分支名
        """
        self.repo_path = repo_path
        self.files = files
        self.branch = branch
    
    def get_selected_files(self) -> List[str]:
        """获取所有选中的文件路径列表"""
        return [f.relative_path for f in self.files if f.selected]
    
    def get_statistics(self) -> Dict[str, object]:
        """获取统计信息，by_status 为按类型统计的已选数量"""
        total = len(self.files)
        by_status: Dict[str, int] = {}
        for f in self.files:
            if f.selected:
                by_status[f.status] = by_status.get(f.status, 0) + 1
        selected = sum(by_status.values())
        return {"total": total, "selected": selected, "by_status": by_status}