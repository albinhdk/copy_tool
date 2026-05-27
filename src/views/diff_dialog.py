from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
import re
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
        for pattern, fmt in self.highlighting_rules:
            expression = re.compile(pattern)
            match = expression.match(text)
            if match:
                self.setFormat(match.start(), match.end() - match.start(), fmt)


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
