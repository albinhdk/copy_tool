import os
import shutil
from typing import List, Tuple

class FileService:
    """文件操作服务，处理文件拷贝和目录管理"""
    
    def copy_files(self, source_dir: str, target_dir: str, 
                   files: List[str]) -> Tuple[int, List[str]]:
        """
        拷贝文件到目标目录，保持目录结构
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径
            files: 要拷贝的文件相对路径列表
            
        Returns:
            成功拷贝的文件数量和错误信息列表
        """
        success_count = 0
        error_messages = []
        
        for rel_path in files:
            src_path = os.path.join(source_dir, rel_path)
            tgt_path = os.path.join(target_dir, rel_path)
            
            if os.path.exists(src_path):
                try:
                    # 确保目标文件夹存在
                    os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
                    shutil.copy2(src_path, tgt_path)
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"{rel_path}: {str(e)}")
            # 不存在的文件静默跳过（可能是已删除的文件）
        
        return success_count, error_messages
    
    def clear_directory(self, dir_path: str):
        """
        清空目录中的所有内容
        
        Args:
            dir_path: 要清空的目录路径
        """
        if not os.path.exists(dir_path):
            return
        
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"清空目录失败 {item_path}: {e}")