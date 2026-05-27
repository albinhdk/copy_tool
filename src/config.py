"""
应用配置常量集中管理
"""

# 应用信息
APP_NAME = "GitCopyTool"
APP_COMPANY = "GitCopyTool"
APP_VERSION = "1.0.0"

# 窗口配置
DEFAULT_WINDOW_SIZE = (800, 600)
MIN_WINDOW_SIZE = (640, 480)

# 历史记录配置
MAX_HISTORY_ITEMS = 10

# 扫描配置
SCAN_DEBOUNCE_MS = 500  # 防抖延迟（毫秒）

# UI样式
MAIN_BUTTON_STYLE = """
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
"""

LIST_VIEW_STYLE = """
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
"""

TREE_VIEW_STYLE = """
    QTreeWidget {
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 8px;
        background-color: #ffffff;
    }
    QTreeWidget::item {
        padding: 4px;
        border-radius: 4px;
    }
    QTreeWidget::item:hover {
        background-color: #f3f4f6;
    }
    QTreeWidget::item:selected {
        background-color: #e5e7eb;
        color: #111827;
    }
"""

CONTEXT_MENU_STYLE = """
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
"""

STATUS_LABEL_STYLE = """
    QLabel {
        color: #0067c0;
        font-size: 12px;
        padding: 4px;
    }
"""

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
