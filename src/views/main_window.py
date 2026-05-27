from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QToolButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from ..components.history_combo import HistoryComboBox
from .file_list_view import FileListView
from .file_tree_view import FileTreeView

class MainWindow(QWidget):
    """主窗口视图"""
    
    # 信号定义
    source_changed = Signal(str)  # 源目录变化
    target_changed = Signal(str)  # 目标目录变化
    scan_requested = Signal()     # 请求扫描
    copy_requested = Signal()     # 请求拷贝
    browse_source_requested = Signal()  # 请求浏览源目录
    browse_target_requested = Signal()  # 请求浏览目标目录
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        self.setWindowTitle("Git 改动文件提取工具")
        self.resize(640, 480)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 1. 源目录选择区
        self._setup_source_section(layout)
        
        # 2. 文件列表区
        self._setup_file_list_section(layout)
        
        # 3. 目标目录选择区
        self._setup_target_section(layout)
        
        # 4. 操作按钮区
        self._setup_action_buttons(layout)
        
        # 连接信号
        self.src_input.currentTextChanged.connect(self.source_changed.emit)
        self.tgt_input.currentTextChanged.connect(self.target_changed.emit)
    
    def _setup_source_section(self, parent_layout: QVBoxLayout):
        """设置源目录选择区"""
        src_layout = QHBoxLayout()
        src_layout.setSpacing(12)
        
        src_label = QLabel("Git 源目录:")
        src_label.setMinimumWidth(80)
        
        self.src_input = HistoryComboBox("请选择或输入包含 .git 的根目录...")
        
        src_btn = QPushButton("浏览...")
        src_btn.setFixedHeight(32)
        src_btn.clicked.connect(self.browse_source_requested.emit)
        
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(src_btn)
        parent_layout.addLayout(src_layout)
    
    def _setup_file_list_section(self, parent_layout: QVBoxLayout):
        """设置文件列表区"""
        list_header_layout = QHBoxLayout()
        list_label = QLabel("已改动的文件 (右键菜单可全选/反选):")
        
        # 视图切换按钮
        self.list_view_btn = QToolButton()
        self.list_view_btn.setText("列表")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setChecked(True)
        self.list_view_btn.setFixedSize(40, 24)
        self.list_view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.list_view_btn.clicked.connect(lambda: self._switch_view(0))
        
        self.tree_view_btn = QToolButton()
        self.tree_view_btn.setText("树形")
        self.tree_view_btn.setCheckable(True)
        self.tree_view_btn.setFixedSize(40, 24)
        self.tree_view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tree_view_btn.clicked.connect(lambda: self._switch_view(1))
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedSize(60, 24)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.scan_requested.emit)
        
        # 统计标签
        self.count_label = QLabel("已选: 0 / 0")
        self.count_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        list_header_layout.addWidget(list_label)
        list_header_layout.addStretch()
        list_header_layout.addWidget(self.list_view_btn)
        list_header_layout.addWidget(self.tree_view_btn)
        list_header_layout.addWidget(refresh_btn)
        list_header_layout.addWidget(self.count_label)
        
        parent_layout.addLayout(list_header_layout)
        
        # 文件视图
        self.stacked_widget = QStackedWidget()
        self.file_list_view = FileListView()
        self.file_tree_view = FileTreeView()
        
        self.stacked_widget.addWidget(self.file_list_view)
        self.stacked_widget.addWidget(self.file_tree_view)
        
        # 连接选择变化信号
        self.file_list_view.selection_changed.connect(self._update_count_label)
        self.file_tree_view.selection_changed.connect(self._update_count_label)
        
        parent_layout.addWidget(self.stacked_widget)
    
    def _setup_target_section(self, parent_layout: QVBoxLayout):
        """设置目标目录选择区"""
        tgt_layout = QHBoxLayout()
        tgt_layout.setSpacing(12)
        
        tgt_label = QLabel("目标目录:")
        tgt_label.setMinimumWidth(80)
        
        self.tgt_input = HistoryComboBox("请选择要拷贝到的目标文件夹...")
        
        tgt_btn = QPushButton("浏览...")
        tgt_btn.setFixedHeight(32)
        tgt_btn.clicked.connect(self.browse_target_requested.emit)
        
        tgt_layout.addWidget(tgt_label)
        tgt_layout.addWidget(self.tgt_input)
        tgt_layout.addWidget(tgt_btn)
        parent_layout.addLayout(tgt_layout)
    
    def _setup_action_buttons(self, parent_layout: QVBoxLayout):
        """设置操作按钮区"""
        self.copy_btn = QPushButton("开始拷贝")
        self.copy_btn.setFixedHeight(40)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0067c0;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005fb8;
            }
            QPushButton:pressed {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        parent_layout.addWidget(self.copy_btn)
    
    def _switch_view(self, index: int):
        """切换视图"""
        self.stacked_widget.setCurrentIndex(index)
        self.list_view_btn.setChecked(index == 0)
        self.tree_view_btn.setChecked(index == 1)
        self._update_count_label()
    
    def _update_count_label(self):
        """更新统计标签"""
        if self.stacked_widget.currentIndex() == 0:
            stats = self.file_list_view.get_statistics()
        else:
            stats = self.file_tree_view.get_statistics()
        
        self.count_label.setText(f"已选: {stats['selected']} / {stats['total']}")
    
    def get_selected_files(self) -> list:
        """获取选中的文件列表"""
        if self.stacked_widget.currentIndex() == 0:
            return self.file_list_view.get_selected_files()
        else:
            return self.file_tree_view.get_selected_files()
    
    def show_message(self, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information):
        """显示消息对话框"""
        QMessageBox(icon, title, message, QMessageBox.StandardButton.Ok, self).exec()
    
    def show_question(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes