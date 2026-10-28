from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QStackedWidget, QToolButton, QMessageBox, QLineEdit, QComboBox
)
from PySide6.QtCore import QMimeData, Qt, QUrl, Signal
from PySide6.QtGui import QAction
from ..components.history_combo import HistoryComboBox
from ..models.file_item import FileItem
from .file_list_view import FileListView
from .file_tree_view import FileTreeView
from .status_badge_bar import StatusBadgeBar
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
    copy_to_clipboard_requested = Signal()  # 请求拷贝后将目标目录放入剪贴板
    browse_source_requested = Signal()  # 请求浏览源目录
    browse_target_requested = Signal()  # 请求浏览目标目录
    open_target_folder_requested = Signal()  # 请求打开目标目录
    structure_root_changed = Signal(str)  # 目录结构起点变化
    browse_structure_root_requested = Signal()  # 请求手动选择目录结构起点
    filter_history_changed = Signal(list)  # 过滤历史变化
    source_history_changed = Signal(list)  # 源目录历史变化（下拉框中删除/清空）
    target_history_changed = Signal(list)  # 目标目录历史变化（下拉框中删除/清空）
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    window_activated = Signal()   # 窗口激活信号
    
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
        self.src_input.history_changed.connect(self.source_history_changed.emit)
        self.tgt_input.history_changed.connect(self.target_history_changed.emit)
    
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
        
        # 当前分支显示
        self.branch_label = QLabel("")
        self.branch_label.setStyleSheet(
            "color: #0067c0; font-weight: bold; padding: 2px 8px;"
            "border: 1px solid #0067c0; border-radius: 4px;"
        )
        self.branch_label.hide()
        
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(src_btn)
        src_layout.addWidget(self.branch_label)
        parent_layout.addLayout(src_layout)
    
    def _setup_file_list_section(self, parent_layout: QVBoxLayout):
        """设置文件列表区"""
        # 第一行：标题和视图切换
        list_header_layout = QHBoxLayout()
        list_label = QLabel("文件:")
        
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
        
        # 排序按钮
        self.sort_by_status_btn = QPushButton("按类型排序")
        self.sort_by_status_btn.setCheckable(True)
        self.sort_by_status_btn.setFixedSize(80, 24)
        self.sort_by_status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_by_status_btn.clicked.connect(self._on_sort_by_status_clicked)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(60, 24)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.scan_requested.emit)
        
        # 统计徽章（按类型显示已选数量）
        self.stats_bar = StatusBadgeBar()
        self.stats_bar.set_counts({}, 0, 0)
        self.count_label = self.stats_bar  # 兼容旧接口
        
        list_header_layout.addWidget(list_label)
        list_header_layout.addStretch()
        # 统计徽章放在按钮左侧：徽章宽度随数量变化时只挤占左侧空白，
        # 右侧操作按钮始终紧贴窗口右边缘，位置不会跳动
        list_header_layout.addWidget(self.stats_bar)
        list_header_layout.addSpacing(8)
        list_header_layout.addWidget(self.list_view_btn)
        list_header_layout.addWidget(self.tree_view_btn)
        list_header_layout.addWidget(self.sort_by_status_btn)
        list_header_layout.addWidget(self.refresh_btn)
        
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
        self.file_list_view.header_sort_activated.connect(self._on_header_sort_activated)
        
        # 连接双击信号
        self.file_list_view.file_double_clicked.connect(self.file_double_clicked.emit)
        self.file_tree_view.file_double_clicked.connect(self.file_double_clicked.emit)
        
        parent_layout.addWidget(self.stacked_widget)
    
    def _setup_target_section(self, parent_layout: QVBoxLayout):
        """设置目标目录选择区（目标目录 + 结构起点，使用网格布局对齐）"""
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # --- Row 0: 目标目录 ---
        tgt_label = QLabel("目标目录:")

        self.tgt_input = HistoryComboBox("请选择要拷贝到的目标文件夹...")

        tgt_btn = QPushButton("浏览...")
        tgt_btn.setFixedHeight(32)
        tgt_btn.setFixedWidth(90)
        tgt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tgt_btn.clicked.connect(self.browse_target_requested.emit)

        self.open_folder_btn = QPushButton("打开文件夹")
        self.open_folder_btn.setFixedHeight(32)
        self.open_folder_btn.setFixedWidth(90)
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self.open_target_folder_requested.emit)

        grid.addWidget(tgt_label, 0, 0)
        grid.addWidget(self.tgt_input, 0, 1)
        grid.addWidget(tgt_btn, 0, 2)
        grid.addWidget(self.open_folder_btn, 0, 3)

        # --- Row 1: 结构起点 ---
        root_label = QLabel("结构起点:")

        self.structure_root_combo = QComboBox()
        self.structure_root_combo.setFixedHeight(32)
        self.structure_root_combo.setToolTip(
            "起点内的文件会裁掉该目录前缀；起点外的文件保持仓库相对路径"
        )
        self.structure_root_combo.currentIndexChanged.connect(
            self._emit_structure_root_changed
        )

        self.structure_root_btn = QPushButton("选择目录...")
        self.structure_root_btn.setFixedHeight(32)
        self.structure_root_btn.setFixedWidth(90)
        self.structure_root_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.structure_root_btn.clicked.connect(self.browse_structure_root_requested.emit)

        grid.addWidget(root_label, 1, 0)
        grid.addWidget(self.structure_root_combo, 1, 1)
        grid.addWidget(self.structure_root_btn, 1, 2)

        # 列属性：标签列固定宽度，下拉框列拉伸填充
        grid.setColumnMinimumWidth(0, 80)
        grid.setColumnStretch(1, 1)

        parent_layout.addLayout(grid)
    
    def _setup_action_buttons(self, parent_layout: QVBoxLayout):
        """设置操作按钮区"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.copy_btn = QPushButton("开始拷贝")
        self.copy_btn.setFixedHeight(40)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet(MAIN_BUTTON_STYLE)
        self.copy_btn.clicked.connect(self.copy_requested.emit)

        self.copy_to_clipboard_btn = QPushButton("拷贝到内存")
        self.copy_to_clipboard_btn.setFixedHeight(40)
        self.copy_to_clipboard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_to_clipboard_btn.setToolTip("先拷贝到目标目录，再将该目录放入剪贴板")
        self.copy_to_clipboard_btn.clicked.connect(self.copy_to_clipboard_requested.emit)

        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.copy_to_clipboard_btn)
        parent_layout.addLayout(button_layout)
    
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

    def _emit_structure_root_changed(self):
        """发送当前目录结构起点。"""
        self.structure_root_changed.emit(self.get_structure_root())
    
    def _on_sort_by_status_clicked(self):
        """处理按类型排序按钮点击"""
        enabled = self.sort_by_status_btn.isChecked()
        self.file_list_view.set_sort_by_status(enabled)
        self.file_tree_view.set_sort_by_status(enabled)
        # 重新加载文件列表以应用排序
        self._apply_filter(self.filter_input.text())

    def _on_header_sort_activated(self, column: int, ascending: bool):
        """表头排序接管后，同步“按类型排序”按钮与树形视图的排序状态。"""
        # 列表按状态升序时与按钮语义一致，按钮保持选中；其余情况取消选中
        status_asc_active = column == 1 and ascending
        self.sort_by_status_btn.setChecked(status_asc_active)
        self.file_tree_view.set_sort_by_status(status_asc_active)

    def _update_count_label(self):
        """更新统计徽章（总计 + 按类型列出已选数量）"""
        if self.stacked_widget.currentIndex() == 0:
            stats = self.file_list_view.get_statistics()
        else:
            stats = self.file_tree_view.get_statistics()

        self.stats_bar.set_counts(
            stats.get("by_status", {}),
            stats.get("selected", 0),
            stats.get("total", 0),
        )
    
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
            self.filter_history_combo.blockSignals(True)
            # 检查是否已存在
            index = self.filter_history_combo.findText(text)
            if index >= 0:
                # 移到最前
                self.filter_history_combo.removeItem(index)
            self.filter_history_combo.insertItem(0, text)
            self.filter_history_combo.setCurrentText(text)
            # 限制历史记录数量
            while self.filter_history_combo.count() > MAX_HISTORY_ITEMS:
                self.filter_history_combo.removeItem(self.filter_history_combo.count() - 1)
            self.filter_history_combo.blockSignals(False)
            
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
    
    def set_branch(self, branch: str):
        """设置当前分支显示"""
        if branch:
            self.branch_label.setText(f" {branch} ")
            self.branch_label.show()
        else:
            self.branch_label.hide()
    
    def get_target_path(self) -> str:
        """获取目标目录路径"""
        return self.tgt_input.currentText().strip()

    def get_structure_root(self) -> str:
        """获取相对于 Git 仓库的目录结构起点。"""
        value = self.structure_root_combo.currentData()
        return str(value) if value is not None else ""

    def set_structure_root_options(self, candidates: List[str], auto_root: str,
                                   selected_root=None):
        """刷新自动识别和可选的目录结构起点。"""
        self.structure_root_combo.blockSignals(True)
        self.structure_root_combo.clear()

        auto_label = f"自动识别：{auto_root or '仓库根目录'}"
        self.structure_root_combo.addItem(auto_label, auto_root)
        self.structure_root_combo.addItem("仓库根目录（不裁剪）", "")

        for root in candidates:
            if root != auto_root:
                self.structure_root_combo.addItem(root, root)

        target_root = auto_root if selected_root is None else selected_root
        target_index = -1
        for index in range(self.structure_root_combo.count()):
            if self.structure_root_combo.itemData(index) == target_root:
                target_index = index
                break
        if target_index < 0:
            self.structure_root_combo.addItem(f"已保存：{target_root}", target_root)
            target_index = self.structure_root_combo.count() - 1

        self.structure_root_combo.setCurrentIndex(target_index)
        self.structure_root_combo.blockSignals(False)

    def add_structure_root_option(self, structure_root: str):
        """添加并选择手动指定的目录结构起点。"""
        for index in range(self.structure_root_combo.count()):
            if self.structure_root_combo.itemData(index) == structure_root:
                self.structure_root_combo.setCurrentIndex(index)
                return
        self.structure_root_combo.addItem(f"手动选择：{structure_root}", structure_root)
        self.structure_root_combo.setCurrentIndex(self.structure_root_combo.count() - 1)
    
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
            self.copy_to_clipboard_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.src_input.setEnabled(False)
            self.structure_root_combo.setEnabled(False)
            self.structure_root_btn.setEnabled(False)
        else:
            self.status_label.hide()
            self.copy_btn.setEnabled(True)
            self.copy_to_clipboard_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.src_input.setEnabled(True)
            self.structure_root_combo.setEnabled(True)
            self.structure_root_btn.setEnabled(True)
    
    def set_copy_button_enabled(self, enabled: bool):
        """设置拷贝按钮启用状态"""
        self.copy_btn.setEnabled(enabled)
        self.copy_to_clipboard_btn.setEnabled(enabled)

    def copy_directory_to_clipboard(self, directory: str):
        """将目录内容（而非目录本身）作为可粘贴的文件对象放入系统剪贴板。"""
        import os
        mime_data = QMimeData()
        urls = []
        if os.path.isdir(directory):
            for item in os.listdir(directory):
                urls.append(QUrl.fromLocalFile(os.path.join(directory, item)))
        mime_data.setUrls(urls)
        QApplication.clipboard().setMimeData(mime_data)
    
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
    
    def changeEvent(self, event):
        """窗口状态变化事件"""
        if event.type() == event.Type.WindowStateChange:
            # 窗口从最小化恢复或从后台切换到前台时触发刷新
            if self.windowState() == Qt.WindowState.WindowNoState:
                self.window_activated.emit()
        super().changeEvent(event)
