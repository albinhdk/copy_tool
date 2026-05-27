# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QStyleFactory

from src.views.main_window import MainWindow
from src.controllers.main_controller import MainController
from src.services.git_service import GitService
from src.services.file_service import FileService
from src.services.config_service import ConfigService

def main():
    """应用主入口"""
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)
    
    # 使用Fusion风格
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 全局颜色设置
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    # 初始化服务
    settings = QSettings("MyCompany", "GitCopyTool")
    git_service = GitService()
    file_service = FileService()
    config_service = ConfigService(settings)
    
    # 初始化视图和控制器
    view = MainWindow()
    controller = MainController(view, git_service, file_service, config_service)
    
    # 显示窗口
    view.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()