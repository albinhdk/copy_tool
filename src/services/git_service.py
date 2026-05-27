import subprocess
import sys
from typing import Optional, List
from ..models.file_item import FileItem
from ..models.git_status import GitStatus

class GitService:
    """Git操作服务，执行Git命令并解析结果"""
    
    def __init__(self):
        """初始化Git服务"""
        self._status_map = {
            'M ': '已修改',
            ' M': '已修改',
            'A ': '已添加',
            '??': '未跟踪',
            'D ': '已删除',
            ' D': '已删除',
            'R ': '已重命名',
            'C ': '已复制',
            '!!': '已忽略',
            'AM': '已添加',
            'MM': '已修改',
            'AD': '已添加',
        }
    
    def scan_repository(self, repo_path: str) -> Optional[GitStatus]:
        """
        扫描Git仓库，获取文件状态
        
        Args:
            repo_path: 仓库根目录路径
            
        Returns:
            GitStatus对象，失败时返回None
        """
        import os
        
        if not repo_path or not os.path.isdir(repo_path):
            return None
        
        # 检查是否是Git仓库
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            return None
        
        try:
            # 执行git status命令
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                ["git", "-c", "core.quotepath=false", "status", "--porcelain", "-u"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            # 解析输出
            files = []
            for line in result.stdout.splitlines():
                item = self._parse_status_line(line)
                if item:
                    # 检查文件是否存在（排除已删除的文件）
                    full_path = os.path.join(repo_path, item.relative_path)
                    if os.path.isfile(full_path) or 'D' in line[:2]:
                        files.append(item)
            
            # 按路径排序
            files.sort(key=lambda x: x.relative_path)
            
            return GitStatus(repo_path, files)
            
        except Exception as e:
            print(f"扫描Git仓库失败: {e}")
            return None
    
    def _parse_status_line(self, line: str) -> Optional[FileItem]:
        """
        解析单行git status输出
        
        Args:
            line: git status --porcelain的输出行
            
        Returns:
            FileItem对象，无效行返回None
        """
        if len(line) < 4:
            return None
        
        # 提取状态和文件名
        status = line[:2]
        filename = line[3:].strip()
        
        # 处理重命名情况: "R  old -> new"
        if "->" in filename:
            filename = filename.split("->")[1].strip()
        
        # 去除可能的引号
        filename = filename.strip('"\'')
        
        # 获取友好的状态标签
        status_label = self._get_status_label(status)
        
        return FileItem(filename, status_label)
    
    def _get_status_label(self, status: str) -> str:
        """
        将git status状态码转换为友好的中文标签
        
        Args:
            status: 两个字符的状态码
            
        Returns:
            中文状态标签
        """
        return self._status_map.get(status, status)