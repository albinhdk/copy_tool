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

# 文件状态顺序（按类型排序、按类型统计共用）
STATUS_ORDER = ['已修改', '已添加', '已删除', '已重命名', '已复制', '未跟踪', '已忽略']

# 文件状态徽章配色：状态 -> (背景色, 文字色)
STATUS_BADGE_COLORS = {
    '已修改': ('#fef3c7', '#92400e'),
    '已添加': ('#dcfce7', '#166534'),
    '已删除': ('#fee2e2', '#991b1b'),
    '已重命名': ('#ede9fe', '#5b21b6'),
    '已复制': ('#cffafe', '#155e75'),
    '未跟踪': ('#e5e7eb', '#4b5563'),
    '已忽略': ('#f3f4f6', '#9ca3af'),
}
DEFAULT_STATUS_BADGE_COLORS = ('#e0e7ff', '#3730a3')
BADGE_TOTAL_BACKGROUND = '#eef2f7'

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
    QTreeWidget {
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 4px;
        background-color: #ffffff;
    }
    QTreeWidget::item {
        padding: 6px;
        border-radius: 4px;
    }
    QTreeWidget::item:hover {
        background-color: #f3f4f6;
    }
    QTreeWidget::item:selected {
        background-color: #e5e7eb;
        color: #111827;
    }
    QHeaderView::section {
        background-color: #f8fafc;
        color: #374151;
        border: none;
        border-bottom: 1px solid #d1d5db;
        padding: 7px 8px;
        font-weight: bold;
    }
    QHeaderView::section:hover {
        background-color: #eef2f7;
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
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
    QPushButton[secondary="true"] {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
    }
    QPushButton[secondary="true"]:hover {
        background-color: #e5e7eb;
    }
    QPushButton[secondary="true"]:pressed {
        background-color: #d1d5db;
    }
"""
