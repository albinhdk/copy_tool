class FileItem:
    """文件项模型，封装单个文件的状态信息"""
    
    def __init__(self, relative_path: str, status: str, selected: bool = True):
        """
        初始化文件项
        
        Args:
            relative_path: 相对于仓库根目录的文件路径
            status: 文件状态（已修改、已添加、未跟踪等）
            selected: 是否选中，默认为True
        """
        self.relative_path = relative_path
        self.status = status
        self.selected = selected
    
    def get_display_text(self) -> str:
        """获取显示文本，格式为: [状态] 文件路径"""
        return f"[{self.status}] {self.relative_path}"
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.get_display_text()