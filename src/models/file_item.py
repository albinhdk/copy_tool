from datetime import datetime
from typing import Optional

class FileItem:
    """文件项模型，封装单个文件的状态信息"""
    
    def __init__(
        self,
        relative_path: str,
        status: str,
        selected: bool = True,
        modified_time: Optional[float] = None,
    ):
        """
        初始化文件项
        
        Args:
            relative_path: 相对于仓库根目录的文件路径
            status: 文件状态（已修改、已添加、未跟踪等）
            selected: 是否选中，默认为True
            modified_time: 文件最后修改时间的 Unix 时间戳；文件不存在时为 None
        """
        self.relative_path = relative_path
        self.status = status
        self.selected = selected
        self.modified_time = modified_time

    def get_modified_time_text(self) -> str:
        """获取最后修改时间的显示文本；文件不存在时返回占位符"""
        if self.modified_time is None:
            return "—"
        return datetime.fromtimestamp(self.modified_time).strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        """字符串表示"""
        return self.relative_path