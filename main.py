import sys
import os
import shutil
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QMenu, QStyleFactory, QComboBox
)
from PySide6.QtCore import Qt, QSize, QSettings
from PySide6.QtGui import QAction, QFont, QIcon

class GitCopyTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git 改动文件提取工具")
        self.resize(640, 480)
        self.setup_ui()

    def setup_ui(self):
        # 整体布局：Windows 11 风格的宽裕边距和间距
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 1. 源目录选择区
        src_layout = QHBoxLayout()
        src_layout.setSpacing(12)
        
        self.src_label = QLabel("Git 源目录:")
        self.src_label.setMinimumWidth(80)
        
        self.src_input = QComboBox()
        self.src_input.setEditable(True)
        self.src_input.lineEdit().setPlaceholderText("请选择或输入包含 .git 的根目录...")
        self.src_input.setFixedHeight(32)
        
        self.src_btn = QPushButton("浏览...")
        self.src_btn.setFixedHeight(32)
        self.src_btn.clicked.connect(self.browse_source)
        
        src_layout.addWidget(self.src_label)
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(self.src_btn)
        layout.addLayout(src_layout)

        # 2. 文件列表区 (带右键菜单和数量统计)
        list_header_layout = QHBoxLayout()
        self.list_label = QLabel("已改动的文件 (右键菜单可全选/反选):")
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(60, 24)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.scan_git_files)
        
        self.count_label = QLabel("已选: 0 / 0")
        self.count_label.setStyleSheet("color: #6b7280; font-weight: bold;")
        
        list_header_layout.addWidget(self.list_label)
        list_header_layout.addStretch()
        list_header_layout.addWidget(self.refresh_btn)
        list_header_layout.addWidget(self.count_label)
        
        layout.addLayout(list_header_layout)

        self.file_list = QListWidget()
        # 允许通过右键呼出菜单
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        # 绑定点击复选框时的统计更新
        self.file_list.itemChanged.connect(self.update_count_label)
        
        # 增加内边距，使其不贴边，呈现现代感
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #e5e7eb;
                color: #111827;
            }
        """)
        layout.addWidget(self.file_list)

        # 3. 目标目录选择区
        tgt_layout = QHBoxLayout()
        tgt_layout.setSpacing(12)
        
        self.tgt_label = QLabel("目标目录:")
        self.tgt_label.setMinimumWidth(80)
        
        self.tgt_input = QComboBox()
        self.tgt_input.setEditable(True)
        self.tgt_input.lineEdit().setPlaceholderText("请选择要拷贝到的目标文件夹...")
        self.tgt_input.setFixedHeight(32)
        
        self.tgt_btn = QPushButton("浏览...")
        self.tgt_btn.setFixedHeight(32)
        self.tgt_btn.clicked.connect(self.browse_target)
        
        tgt_layout.addWidget(self.tgt_label)
        tgt_layout.addWidget(self.tgt_input)
        tgt_layout.addWidget(self.tgt_btn)
        layout.addLayout(tgt_layout)

        # 4. 操作按钮区
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
        self.copy_btn.clicked.connect(self.start_copy)
        layout.addWidget(self.copy_btn)

        # 绑定信号：源目录输入变化时触发扫描
        self.src_input.currentTextChanged.connect(self.scan_git_files)
        
        # 初始化配置并加载历史记录
        self.settings = QSettings("MyCompany", "GitCopyTool")
        self.load_history()

    def load_history(self):
        src_history = self.settings.value("src_history", [])
        if src_history:
            # 阻止信号触发，以免刚加载就报错或扫描
            self.src_input.blockSignals(True)
            self.src_input.addItems(src_history)
            self.src_input.setCurrentText("") # 默认留空，等待用户选择
            self.src_input.blockSignals(False)

        tgt_history = self.settings.value("tgt_history", [])
        if tgt_history:
            self.tgt_input.blockSignals(True)
            self.tgt_input.addItems(tgt_history)
            self.tgt_input.setCurrentText("")
            self.tgt_input.blockSignals(False)

    def save_history(self, path):
        if not path:
            return
        # 获取当前所有项
        history = [self.src_input.itemText(i) for i in range(self.src_input.count())]
        
        # 移除已存在的该路径（如果有的话），把它移到最前面
        if path in history:
            history.remove(path)
        history.insert(0, path)
        
        # 最多保留 10 条记录
        history = history[:10]
        
        self.settings.setValue("src_history", history)
        
        # 刷新下拉框
        self.src_input.blockSignals(True)
        self.src_input.clear()
        self.src_input.addItems(history)
        self.src_input.setCurrentText(path)
        self.src_input.blockSignals(False)

    def save_tgt_history(self, path):
        if not path:
            return
        history = [self.tgt_input.itemText(i) for i in range(self.tgt_input.count())]
        
        if path in history:
            history.remove(path)
        history.insert(0, path)
        history = history[:10]
        
        self.settings.setValue("tgt_history", history)
        
        self.tgt_input.blockSignals(True)
        self.tgt_input.clear()
        self.tgt_input.addItems(history)
        self.tgt_input.setCurrentText(path)
        self.tgt_input.blockSignals(False)

    def update_count_label(self):
        total = self.file_list.count()
        selected = sum(1 for i in range(total) if self.file_list.item(i).checkState() == Qt.CheckState.Checked)
        self.count_label.setText(f"已选: {selected} / {total}")

    def browse_source(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择 Git 源目录")
        if dir_path:
            self.src_input.setCurrentText(dir_path)

    def browse_target(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if dir_path:
            self.tgt_input.setCurrentText(dir_path)

    def scan_git_files(self):
        repo_path = self.src_input.currentText().strip()
        self.file_list.clear()
        
        if not repo_path or not os.path.isdir(repo_path):
            return
            
        # 检查是否是 Git 仓库
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            return

        try:
            # 运行 git status，关闭 core.quotepath 避免中文乱码
            # 针对 PyInstaller 打包后的 noconsole 模式，需要隐藏子进程窗口并重定向 stdin，否则会导致严重的阻塞和卡顿
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                ["git", "-c", "core.quotepath=false", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            lines = result.stdout.splitlines()
            for line in lines:
                if len(line) < 4:
                    continue
                
                # Git porcelain 输出格式为 "XY filename"
                status = line[:2]
                filename = line[3:].strip()
                
                # 处理重命名情况: "R  old -> new"
                if "->" in filename:
                    filename = filename.split("->")[1].strip()
                    
                # 去除可能的引号
                filename = filename.strip('"\'')

                full_path = os.path.join(repo_path, filename)
                
                # 只列出文件（忽略纯目录的变更）
                if os.path.isfile(full_path) or status[1] == 'D':
                    # 将状态码转换为友好的中文标签
                    status_label = self.get_status_label(status)
                    
                    # 在界面上展示：[状态] 文件路径
                    display_text = f"[{status_label}] {filename}"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, filename) # 存储纯净的相对路径
                    
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked) # 默认选中
                    self.file_list.addItem(item)
                    
            # 扫描结束后更新统计
            self.update_count_label()
                    
        except Exception as e:
            # 静默处理或打印错误
            print(f"扫描 Git 失败: {e}")
            self.update_count_label()

    def get_status_label(self, status):
        """将 git status --porcelain 的状态码转换为友好的中文标签"""
        status_map = {
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
        return status_map.get(status, status)

    def show_context_menu(self, pos):
        # 响应右键，提供全选/反选操作
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
            }
        """)
        
        action_select_all = QAction("全选", self)
        action_select_all.triggered.connect(lambda: self.set_all_checked(Qt.CheckState.Checked))
        
        action_deselect_all = QAction("全不选", self)
        action_deselect_all.triggered.connect(lambda: self.set_all_checked(Qt.CheckState.Unchecked))
        
        menu.addAction(action_select_all)
        menu.addAction(action_deselect_all)
        
        menu.exec(self.file_list.mapToGlobal(pos))

    def set_all_checked(self, state):
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(state)

    def start_copy(self):
        src_dir = self.src_input.currentText().strip()
        tgt_dir = self.tgt_input.currentText().strip()

        if not src_dir or not os.path.exists(src_dir):
            QMessageBox.warning(self, "错误", "源目录无效或不存在！")
            return
            
        if not tgt_dir:
            QMessageBox.warning(self, "错误", "请选择目标目录！")
            return

        # 收集被选中的文件相对路径
        selected_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                rel_path = item.data(Qt.ItemDataRole.UserRole)
                selected_files.append(rel_path)

        if not selected_files:
            QMessageBox.information(self, "提示", "没有选中任何文件。")
            return

        # 危险操作提醒：清空目标目录
        if os.path.exists(tgt_dir) and os.listdir(tgt_dir):
            reply = QMessageBox.question(
                self, 
                "清空目标目录确认", 
                f"将要清空目标目录:\n{tgt_dir}\n\n里面现有的所有文件都会被永久删除！是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            
            try:
                # 清空目标目录中的所有内容
                for item in os.listdir(tgt_dir):
                    item_path = os.path.join(tgt_dir, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            except Exception as e:
                QMessageBox.critical(self, "清空失败", f"清空目标目录时发生错误:\n{str(e)}")
                return

        # 执行拷贝前，保存历史记录
        self.save_history(src_dir)
        self.save_tgt_history(tgt_dir)

        success_count = 0
        error_messages = []
        
        for rel_path in selected_files:
            src_path = os.path.join(src_dir, rel_path)
            tgt_path = os.path.join(tgt_dir, rel_path)

            if os.path.exists(src_path):
                try:
                    # 确保目标文件夹存在，保持原有目录结构
                    os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
                    shutil.copy2(src_path, tgt_path)
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"{rel_path}: {str(e)}")
            else:
                # 文件可能已被删除（比如 git status 中的 'D ' 状态）
                # 这里我们选择跳过它
                pass

        # 结果反馈
        if error_messages:
            error_str = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_str += f"\n...及其他 {len(error_messages)-5} 个错误"
            QMessageBox.warning(self, "完成，但有错误", f"成功拷贝 {success_count} 个文件。\n\n部分失败:\n{error_str}")
        else:
            QMessageBox.information(self, "成功", f"成功拷贝了 {success_count} 个文件！\n\n已保持原始目录结构存放在:\n{tgt_dir}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体 (Windows 友好)
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)
    
    # 使用 Fusion 风格作为现代 UI 的基础
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 全局颜色微调 (可选)
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, Qt.GlobalColor.white)
    app.setPalette(palette)

    window = GitCopyTool()
    window.show()
    sys.exit(app.exec())
