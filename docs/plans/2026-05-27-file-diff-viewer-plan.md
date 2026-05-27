# 文件差异查看功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现双击文件列表中的文件时，弹出对话框显示该文件的Git差异内容

**Architecture:** 
- 在GitService中添加`get_file_diff()`方法，调用`git diff`命令获取文件差异
- 创建DiffViewerDialog对话框组件，用于显示差异内容（带语法高亮）
- 在FileListView和FileTreeView中添加双击事件信号
- 在MainController中处理双击事件，调用GitService获取差异并显示对话框

**Tech Stack:** Python, PySide6, Git CLI

---

## Task 1: 在GitService中添加获取文件差异的方法

**Files:**
- Modify: `src/services/git_service.py:10-132`

**Step 1: 添加get_file_diff方法**

在GitService类中添加新方法：

```python
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
                # 对于新文件，显示文件内容
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
```

**Step 2: 测试方法**

在Python控制台或测试中验证方法可以正常调用。

**Step 3: 提交**

```bash
git add src/services/git_service.py
git commit -m "feat: add get_file_diff method to GitService"
```

---

## Task 2: 创建差异查看对话框

**Files:**
- Create: `src/views/diff_dialog.py`

**Step 1: 创建差异查看对话框类**

```python
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from ..config import DIFF_DIALOG_STYLE


class DiffHighlighter(QSyntaxHighlighter):
    """差异内容语法高亮器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # 新增行（绿色）
        addition_format = QTextCharFormat()
        addition_format.setForeground(QColor("#22863a"))
        addition_format.setBackground(QColor("#e6ffec"))
        self.highlighting_rules.append((r'^\+.*$', addition_format))
        
        # 删除行（红色）
        deletion_format = QTextCharFormat()
        deletion_format.setForeground(QColor("#cb2431"))
        deletion_format.setBackground(QColor("#ffeef0"))
        self.highlighting_rules.append((r'^\-.*$', deletion_format))
        
        # 差异头部（蓝色）
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#005cc5"))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^@@.*@@', header_format))
        
        # 文件头部
        file_header_format = QTextCharFormat()
        file_header_format.setForeground(QColor("#6f42c1"))
        file_header_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^(diff|---|\+\+\+).*$', file_header_format))
    
    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            expression = re.compile(pattern)
            match = expression.match(text)
            if match:
                self.setFormat(match.start(), match.end() - match.start(), format)


class DiffViewerDialog(QDialog):
    """差异查看对话框"""
    
    def __init__(self, file_path: str, diff_content: str, parent=None):
        """
        初始化差异查看对话框
        
        Args:
            file_path: 文件路径
            diff_content: 差异内容
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle(f"文件差异 - {file_path}")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        self._setup_ui(file_path, diff_content)
    
    def _setup_ui(self, file_path: str, diff_content: str):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 文件路径标签
        path_label = QLabel(f"文件: {file_path}")
        path_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(path_label)
        
        # 差异内容显示
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setFont(QFont("Consolas", 10))
        self.diff_text.setPlainText(diff_content)
        
        # 应用语法高亮
        self.highlighter = DiffHighlighter(self.diff_text.document())
        
        layout.addWidget(self.diff_text)
        
        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 应用样式
        self.setStyleSheet(DIFF_DIALOG_STYLE)
```

**Step 2: 添加对话框样式到config.py**

在`src/config.py`中添加：

```python
DIFF_DIALOG_STYLE = """
    QDialog {
        background-color: #ffffff;
    }
    QTextEdit {
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px;
        background-color: #fafbfc;
        font-family: "Consolas", "Courier New", monospace;
    }
    QPushButton {
        background-color: #0067c0;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #005fb8;
    }
    QPushButton:pressed {
        background-color: #0052a3;
    }
"""
```

**Step 3: 测试对话框**

创建简单的测试脚本验证对话框可以正常显示。

**Step 4: 提交**

```bash
git add src/views/diff_dialog.py src/config.py
git commit -m "feat: add DiffViewerDialog for displaying file differences"
```

---

## Task 3: 在文件视图中添加双击事件

**Files:**
- Modify: `src/views/file_list_view.py:1-88`
- Modify: `src/views/file_tree_view.py:1-157`

**Step 1: 在FileListView中添加双击信号和处理**

在FileListView类中：

```python
from PySide6.QtCore import Qt, Signal

class FileListView(QListWidget):
    """文件列表视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    
    def __init__(self, parent=None):
        """初始化文件列表视图"""
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """处理双击事件"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_double_clicked.emit(file_path)
```

**Step 2: 在FileTreeView中添加双击信号和处理**

在FileTreeView类中：

```python
from PySide6.QtCore import Qt, Signal

class FileTreeView(QTreeWidget):
    """文件树视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    file_double_clicked = Signal(str)  # 文件双击信号，传递文件路径
    
    def __init__(self, parent=None):
        """初始化文件树视图"""
        super().__init__(parent)
        self.setHeaderLabels(["文件路径", "状态"])
        self.setColumnCount(2)
        self.setColumnWidth(0, 400)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._setup_style()
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """处理双击事件"""
        # 只处理文件节点（叶子节点），忽略目录节点
        if item.childCount() == 0:
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_double_clicked.emit(file_path)
```

**Step 3: 提交**

```bash
git add src/views/file_list_view.py src/views/file_tree_view.py
git commit -m "feat: add double-click signals to file views"
```

---

## Task 4: 在MainWindow中连接双击信号

**Files:**
- Modify: `src/views/main_window.py:1-358`

**Step 1: 添加文件双击信号**

在MainWindow类的信号定义部分添加：

```python
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
```

**Step 2: 连接文件视图的双击信号**

在`_setup_file_list_section`方法中，连接两个视图的双击信号：

```python
# 连接选择变化信号
self.file_list_view.selection_changed.connect(self._update_count_label)
self.file_tree_view.selection_changed.connect(self._update_count_label)

# 连接双击信号
self.file_list_view.file_double_clicked.connect(self.file_double_clicked.emit)
self.file_tree_view.file_double_clicked.connect(self.file_double_clicked.emit)
```

**Step 3: 提交**

```bash
git add src/views/main_window.py
git commit -m "feat: connect file double-click signals in MainWindow"
```

---

## Task 5: 在MainController中处理双击事件

**Files:**
- Modify: `src/controllers/main_controller.py:1-234`

**Step 1: 导入DiffViewerDialog**

```python
from ..views.diff_dialog import DiffViewerDialog
```

**Step 2: 连接双击信号**

在`_connect_signals`方法中添加：

```python
def _connect_signals(self):
    """连接视图信号到处理方法"""
    self.view.source_changed.connect(self._on_source_changed)
    self.view.scan_requested.connect(self._on_scan_requested)
    self.view.copy_requested.connect(self._on_copy_requested)
    self.view.browse_source_requested.connect(self._on_browse_source)
    self.view.browse_target_requested.connect(self._on_browse_target)
    self.view.filter_history_changed.connect(self._on_filter_history_changed)
    self.view.file_double_clicked.connect(self._on_file_double_clicked)  # 新增
```

**Step 3: 添加双击事件处理方法**

```python
def _on_file_double_clicked(self, file_path: str):
    """处理文件双击事件，显示差异"""
    repo_path = self.view.get_source_path()
    
    if not repo_path:
        self.view.show_message("提示", "请先选择Git源目录", QMessageBox.Icon.Information)
        return
    
    logger.info(f"用户双击查看文件差异: {file_path}")
    
    # 获取差异
    diff_content, error = self.git_service.get_file_diff(repo_path, file_path)
    
    if error:
        logger.error(f"获取文件差异失败: {error}")
        self.view.show_message("获取差异失败", error, QMessageBox.Icon.Warning)
        return
    
    # 显示差异对话框
    dialog = DiffViewerDialog(file_path, diff_content, self.view)
    dialog.exec()
```

**Step 4: 测试完整功能**

运行应用程序，选择一个Git仓库，双击某个文件，验证差异对话框是否正常显示。

**Step 5: 提交**

```bash
git add src/controllers/main_controller.py
git commit -m "feat: handle file double-click to show diff dialog"
```

---

## Task 6: 最终测试和优化

**Files:**
- Test: 手动测试整个功能流程

**Step 1: 运行应用程序**

```bash
python main.py
```

**Step 2: 测试场景**

1. 选择一个有改动文件的Git仓库
2. 在文件列表中双击一个已修改的文件
3. 验证差异对话框正确显示差异内容
4. 测试新文件、已删除文件的差异显示
5. 在树形视图中测试相同功能

**Step 3: 最终提交**

```bash
git add .
git commit -m "feat: complete file diff viewer feature"
```

---

## 注意事项

1. 确保Git命令可用
2. 处理中文路径和文件名编码问题
3. 对于大文件，差异内容可能很长，需要确保对话框性能
4. 考虑添加复制差异内容的功能
