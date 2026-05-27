from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QToolButton, QMessageBox, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..components.history_combo import HistoryComboBox
from ..models.file_item import FileItem
from .file_list_view import FileListView
from .file_tree_view import FileTreeView
from ..config import (
    DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, MAIN_BUTTON_STYLE,
    STATUS_LABEL_STYLE, MAX_HISTORY_ITEMS
)


class MainWindow(QWidget):
    """主窗口视图"""
    
    # 信号定义
    source_changed = Signal(str)  # 源目录变化
    target_changed = Signal(str)  # 目标目录变化
    scan_requested = Signal()     # 请求扫描
    copy_requested = Signal()     # 请求拷贝
    browse_source_requested = Signal()  # 请求浏览源目录
    browse_target_requested = Signal()  # 请求浏览目标目录
    filter_history_changed = Signal(list)  # 过滤历史变化
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        self.setWindowTitle("Git 改动文件提取工具")
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        self._all_files = []  # 保存完整文件列表
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
        
        # 5. 状态栏（加载提示）
        self._setup_status_bar(layout)
        
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
        # 第一行：标题和视图切换
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
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(60, 24)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.scan_requested.emit)
        
        # 统计标签
        self.count_label = QLabel("已选: 0 / 0")
        self.count_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        list_header_layout.addWidget(list_label)
        list_header_layout.addStretch()
        list_header_layout.addWidget(self.list_view_btn)
        list_header_layout.addWidget(self.tree_view_btn)
        list_header_layout.addWidget(self.refresh_btn)
        list_header_layout.addWidget(self.count_label)
        
        parent_layout.addLayout(list_header_layout)
        
        # 第二行：搜索过滤框
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        filter_label = QLabel("过滤:")
        filter_label.setFixedWidth(35)
        
        # 搜索历史下拉框
        self.filter_history_combo = QComboBox()
        self.filter_history_combo.setEditable(True)
        self.filter_history_combo.setFixedHeight(28)
        self.filter_history_combo.setMinimumWidth(150)
        self.filter_history_combo.setMaxVisibleItems(10)
        self.filter_history_combo.setPlaceholderText("输入或选择历史记录...")
        self.filter_history_combo.currentTextChanged.connect(self._on_filter_changed)
        self.filter_input = self.filter_history_combo.lineEdit()
        self.filter_input.setPlaceholderText("输入文件名或扩展名过滤，如 .py  src/  main")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.returnPressed.connect(self._save_filter_history)
        
        # 快捷过滤按钮 - 扩展名列表
        quick_filters = [".py", ".js", ".java", ".vue", ".go", ".c", ".cpp", ".html"]
        
        clear_filter_btn = QPushButton("清除")
        clear_filter_btn.setFixedSize(45, 24)
        clear_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_filter_btn.clicked.connect(lambda: self.filter_input.setText(""))
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_history_combo)
        
        # 添加快捷过滤按钮
        for ext in quick_filters:
            btn = QPushButton(ext)
            btn.setFixedSize(45, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, e=ext: self._set_filter(e))
            filter_layout.addWidget(btn)
        
        filter_layout.addWidget(clear_filter_btn)
        
        parent_layout.addLayout(filter_layout)
        
        # 文件视图
        self.stacked_widget = QStackedWidget()
        self.file_list_view = FileListView()
        self.file_tree_view = FileTreeView()
        
        self.stacked_widget.addWidget(self.file_list_view)
        self.stacked_widget.addWidget(self.file_tree_view)
        
        # 连接选择变化信号
        self.file_list_view.selection_changed.connect(self._update_count_label)
        self.file_tree_view.selection_changed.connect(self._update_count_label)
        
        # 连接双击信号
        self.file_list_view.file_double_clicked.connect(self.file_double_clicked.emit)
        self.file_tree_view.file_double_clicked.connect(self.file_double_clicked.emit)
        
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
        self.copy_btn.setStyleSheet(MAIN_BUTTON_STYLE)
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        parent_layout.addWidget(self.copy_btn)
    
    def _setup_status_bar(self, parent_layout: QVBoxLayout):
        """设置状态栏（加载提示）"""
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(STATUS_LABEL_STYLE)
        self.status_label.hide()
        parent_layout.addWidget(self.status_label)
    
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
    
    def _set_filter(self, text: str):
        """设置过滤文本"""
        self.filter_input.setText(text)
        self._save_filter_history()
    
    def _on_filter_changed(self, text: str):
        """过滤文本变化"""
        self._apply_filter(text)
    
    def _save_filter_history(self):
        """保存当前过滤文本到历史记录"""
        text = self.filter_input.text().strip()
        if text:
            # 检查是否已存在
            index = self.filter_history_combo.findText(text)
            if index >= 0:
                # 移到最前
                self.filter_history_combo.removeItem(index)
            self.filter_history_combo.insertItem(0, text)
            # 限制历史记录数量
            while self.filter_history_combo.count() > MAX_HISTORY_ITEMS:
                self.filter_history_combo.removeItem(self.filter_history_combo.count() - 1)
            
            # 发送历史变化信号
            history = [self.filter_history_combo.itemText(i) for i in range(self.filter_history_combo.count())]
            self.filter_history_changed.emit(history)
    
    def set_filter_history(self, history: List[str]):
        """设置过滤历史记录"""
        self.filter_history_combo.blockSignals(True)
        self.filter_history_combo.clear()
        if history:
            self.filter_history_combo.addItems(history)
        self.filter_history_combo.setCurrentText("")
        self.filter_history_combo.blockSignals(False)
    
    def _apply_filter(self, filter_text: str):
        """应用过滤"""
        if not filter_text:
            filtered_files = self._all_files
        else:
            filter_lower = filter_text.lower()
            filtered_files = [
                f for f in self._all_files
                if filter_lower in f.relative_path.lower()
            ]
        
        self.file_list_view.load_files(filtered_files)
        self.file_tree_view.load_files(filtered_files)
    
    # ========== 公共接口方法（供Controller调用） ==========
    
    def get_source_path(self) -> str:
        """获取源目录路径"""
        return self.src_input.currentText().strip()
    
    def set_source_path(self, path: str):
        """设置源目录路径"""
        self.src_input.setCurrentText(path)
    
    def get_target_path(self) -> str:
        """获取目标目录路径"""
        return self.tgt_input.currentText().strip()
    
    def set_target_path(self, path: str):
        """设置目标目录路径"""
        self.tgt_input.setCurrentText(path)
    
    def set_source_history(self, history: List[str]):
        """设置源目录历史记录"""
        self.src_input.load_history(history)
    
    def set_target_history(self, history: List[str]):
        """设置目标目录历史记录"""
        self.tgt_input.load_history(history)
    
    def add_source_to_history(self, path: str):
        """添加源目录到历史记录"""
        self.src_input.add_to_history(path)
    
    def add_target_to_history(self, path: str):
        """添加目标目录到历史记录"""
        self.tgt_input.add_to_history(path)
    
    def load_files(self, files: List[FileItem]):
        """加载文件列表到视图"""
        self._all_files = files  # 保存完整列表
        self._apply_filter(self.filter_input.text())  # 应用当前过滤
    
    def get_selected_files(self) -> list:
        """获取选中的文件列表"""
        if self.stacked_widget.currentIndex() == 0:
            return self.file_list_view.get_selected_files()
        else:
            return self.file_tree_view.get_selected_files()
    
    def set_loading(self, loading: bool, message: str = ""):
        """设置加载状态"""
        if loading:
            self.status_label.setText(message)
            self.status_label.show()
            self.copy_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.src_input.setEnabled(False)
        else:
            self.status_label.hide()
            self.copy_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.src_input.setEnabled(True)
    
    def set_copy_button_enabled(self, enabled: bool):
        """设置拷贝按钮启用状态"""
        self.copy_btn.setEnabled(enabled)
    
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
