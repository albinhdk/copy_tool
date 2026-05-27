import os
import subprocess
import sys
from typing import Optional, List, Tuple
from ..models.file_item import FileItem
from ..models.git_status import GitStatus
from ..utils.logger import logger


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
    
    def scan_repository(self, repo_path: str) -> Tuple[Optional[GitStatus], Optional[str]]:
        """
        扫描Git仓库，获取文件状态
        
        Args:
            repo_path: 仓库根目录路径
            
        Returns:
            元组 (GitStatus对象或None, 错误信息或None)
        """
        if not repo_path or not os.path.isdir(repo_path):
            logger.warning(f"扫描失败: 路径无效或不存在 - {repo_path}")
            return None, "指定的路径不存在或不是有效目录"
        
        # 检查是否是Git仓库
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            logger.warning(f"扫描失败: 非Git仓库 - {repo_path}")
            return None, "该目录不是Git仓库（未找到.git文件夹）"
        
        try:
            logger.info(f"开始扫描Git仓库: {repo_path}")
            
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
            
            logger.info(f"扫描完成: 发现 {len(files)} 个变更文件")
            return GitStatus(repo_path, files), None
            
        except FileNotFoundError:
            logger.error("Git命令未找到，请确保已安装Git")
            return None, "未找到Git命令，请确保已安装Git并添加到系统PATH"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"Git命令执行失败: {error_msg}")
            return None, f"Git命令执行失败: {error_msg}"
        except Exception as e:
            logger.exception(f"扫描Git仓库时发生未知错误: {e}")
            return None, f"扫描Git仓库时发生错误: {str(e)}"
    
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
    
    def get_file_diff(self, repo_path: str, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取指定文件的Git差异
        
        Args:
            repo_path: 仓库根目录路径
            file_path: 相对于仓库根目录的文件路径
            
        Returns:
            元组 (差异内容或None, 错误信息或None)
        """
        if not repo_path or not os.path.isdir(repo_path):
            return None, "仓库路径无效"
        
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            # 先尝试获取暂存区的差异
            result = subprocess.run(
                ["git", "diff", "HEAD", "--", file_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            diff_output = result.stdout.strip()
            
            # 如果没有差异，尝试获取工作区的差异
            if not diff_output:
                result = subprocess.run(
                    ["git", "diff", "--", file_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags
                )
                diff_output = result.stdout.strip()
            
            # 如果仍然没有差异，可能是新文件
            if not diff_output:
                full_path = os.path.join(repo_path, file_path)
                if os.path.isfile(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        diff_output = f"+++ 新文件: {file_path}\n{content}"
                    except Exception:
                        diff_output = f"无法读取文件内容: {file_path}"
            
            return diff_output if diff_output else "没有差异", None
            
        except FileNotFoundError:
            return None, "Git命令未找到"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return None, f"Git命令执行失败: {error_msg}"
        except Exception as e:
            return None, f"获取差异时发生错误: {str(e)}"
