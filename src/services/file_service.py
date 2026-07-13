import os
import shutil
from typing import List, Tuple
from ..utils.logger import logger


class FileService:
    """文件操作服务，处理文件拷贝和目录管理"""

    @staticmethod
    def _normalize_relative_path(path: str) -> str:
        """统一使用正斜杠表示仓库相对路径。"""
        return path.replace('\\', '/').strip('/')

    @classmethod
    def get_structure_root_candidates(cls, files: List[str]) -> List[str]:
        """从变更文件中提取常见的源码结构起点候选项。"""
        candidates = set()
        for file_path in files:
            parts = cls._normalize_relative_path(file_path).split('/')
            for index, part in enumerate(parts[:-1]):
                if part.lower() != 'src':
                    continue

                candidates.add('/'.join(parts[:index + 1]))
                if index + 1 < len(parts) - 1 and parts[index + 1].lower() in {'main', 'test'}:
                    candidates.add('/'.join(parts[:index + 2]))
                    if (
                        index + 2 < len(parts) - 1
                        and parts[index + 2].lower() in {'java', 'kotlin', 'resources'}
                    ):
                        candidates.add('/'.join(parts[:index + 3]))

        normalized_files = [cls._normalize_relative_path(path) for path in files]

        def score(candidate: str):
            prefix = candidate.lower() + '/'
            coverage = sum(path.lower().startswith(prefix) for path in normalized_files)
            depth = candidate.count('/') + 1
            return (-coverage, -depth, candidate.lower())

        return sorted(candidates, key=score)

    @classmethod
    def detect_structure_root(cls, files: List[str]) -> str:
        """自动选择覆盖变更文件最多且最具体的常见源码起点。"""
        candidates = cls.get_structure_root_candidates(files)
        return candidates[0] if candidates else ''

    @classmethod
    def map_output_path(cls, relative_path: str, structure_root: str = '') -> str:
        """将仓库相对路径转换为补丁包内路径。"""
        relative_path = cls._normalize_relative_path(relative_path)
        structure_root = cls._normalize_relative_path(structure_root)
        if not structure_root:
            return relative_path

        root_parts = structure_root.split('/')
        path_parts = relative_path.split('/')
        if [part.lower() for part in path_parts[:len(root_parts)]] == [
            part.lower() for part in root_parts
        ] and len(path_parts) > len(root_parts):
            return '/'.join(path_parts[len(root_parts):])
        return relative_path

    @classmethod
    def find_output_collisions(cls, files: List[str], structure_root: str = '') -> List[str]:
        """返回路径裁剪后会相互覆盖的冲突信息。"""
        output_paths = {}
        collisions = []
        for rel_path in files:
            tgt_rel_path = cls.map_output_path(rel_path, structure_root)
            collision_key = os.path.normcase(tgt_rel_path.replace('/', os.sep))
            if collision_key in output_paths and output_paths[collision_key] != rel_path:
                collisions.append(
                    f"路径冲突: {output_paths[collision_key]} 和 {rel_path} "
                    f"都会输出为 {tgt_rel_path}"
                )
            else:
                output_paths[collision_key] = rel_path
        return collisions
    
    def copy_files(self, source_dir: str, target_dir: str,
                   files: List[str], structure_root: str = '') -> Tuple[int, List[str]]:
        """
        拷贝文件到目标目录，保持目录结构
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径
            files: 要拷贝的文件相对路径列表
            structure_root: 输出目录结构起点；起点外文件保持仓库相对路径
            
        Returns:
            成功拷贝的文件数量和错误信息列表
        """
        success_count = 0
        error_messages = []
        skipped_files = []
        
        logger.info(f"开始拷贝文件: {len(files)} 个文件")
        logger.debug(f"源目录: {source_dir}")
        logger.debug(f"目标目录: {target_dir}")

        collisions = self.find_output_collisions(files, structure_root)
        if collisions:
            for message in collisions:
                logger.error(message)
            return 0, collisions
        
        for rel_path in files:
            src_path = os.path.join(source_dir, rel_path)
            tgt_rel_path = self.map_output_path(rel_path, structure_root)
            tgt_path = os.path.join(target_dir, tgt_rel_path)
            
            if os.path.exists(src_path):
                try:
                    # 确保目标文件夹存在
                    os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
                    shutil.copy2(src_path, tgt_path)
                    success_count += 1
                    logger.debug(f"拷贝成功: {rel_path}")
                except Exception as e:
                    error_messages.append(f"{rel_path}: {str(e)}")
                    logger.error(f"拷贝失败: {rel_path} - {e}")
            else:
                skipped_files.append(rel_path)
                logger.debug(f"跳过不存在的文件: {rel_path}")
        
        if skipped_files:
            logger.info(f"跳过 {len(skipped_files)} 个不存在的文件")
        
        logger.info(f"拷贝完成: 成功 {success_count}, 失败 {len(error_messages)}")
        return success_count, error_messages
    
    def clear_directory(self, dir_path: str):
        """
        清空目录中的所有内容
        
        Args:
            dir_path: 要清空的目录路径
        """
        if not os.path.exists(dir_path):
            logger.warning(f"清空目录失败: 目录不存在 - {dir_path}")
            return
        
        logger.info(f"开始清空目录: {dir_path}")
        
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    logger.debug(f"删除文件: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.debug(f"删除目录: {item_path}")
            except Exception as e:
                logger.error(f"清空目录失败 {item_path}: {e}")
        
        logger.info(f"目录清空完成: {dir_path}")
