import logging
import os
from datetime import datetime


def setup_logger(name: str = "GitCopyTool") -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 日志目录
    log_dir = os.path.join(os.path.expanduser("~"), ".git_copy_tool", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件名（按日期）
    log_file = os.path.join(log_dir, f"{datetime.now():%Y%m%d}.log")
    
    # 文件处理器 - 记录所有日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)
    
    return logger


# 全局日志记录器
logger = setup_logger()
