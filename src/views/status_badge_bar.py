from typing import Dict, List, Tuple

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from ..config import (
    STATUS_ORDER, STATUS_BADGE_COLORS, DEFAULT_STATUS_BADGE_COLORS,
    BADGE_TOTAL_BACKGROUND,
)


def ordered_status_items(counts: Dict[str, int]) -> List[Tuple[str, int]]:
    """按 STATUS_ORDER 排列统计项，数量为 0 的状态不展示，未知状态排在最后。"""
    known = [(status, counts[status]) for status in STATUS_ORDER if counts.get(status)]
    unknown = sorted(
        (status, count)
        for status, count in counts.items()
        if status not in STATUS_ORDER and count
    )
    return known + unknown


def status_badge_colors(status: str) -> Tuple[str, str]:
    """返回状态对应的徽章配色（背景色, 文字色）。"""
    return STATUS_BADGE_COLORS.get(status, DEFAULT_STATUS_BADGE_COLORS)


def badge_style(background: str, foreground: str) -> str:
    """生成单个徽章的样式表（文字内边距由 _Badge.sizeHint 提供）。"""
    return (
        f"QLabel {{ background-color: {background}; color: {foreground};"
        f" border-radius: 10px; font-weight: bold; }}"
    )


class _Badge(QLabel):
    """圆角徽章标签：字体内边距由 sizeHint 显式叠加，避免被布局裁切。"""

    H_PADDING = 9
    V_PADDING = 3

    def __init__(self, parent=None):
        """初始化标签，固定尺寸策略保证布局严格按 sizeHint 分配。"""
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        """文字尺寸 + 左右/上下内边距。"""
        metrics = self.fontMetrics()
        return QSize(
            metrics.horizontalAdvance(self.text()) + self.H_PADDING * 2,
            metrics.height() + self.V_PADDING * 2,
        )

    def minimumSizeHint(self) -> QSize:
        """最小尺寸与 sizeHint 一致，窗口变窄也不截断文字。"""
        return self.sizeHint()


class StatusBadgeBar(QWidget):
    """按文件类型（状态）展示数量的彩色徽章栏。"""

    def __init__(self, parent=None):
        """初始化徽章栏。"""
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._badges: List[_Badge] = []
        self._total_badge = self._create_badge()
        self._layout.addWidget(self._total_badge)
        self._layout.addStretch(1)

    def _create_badge(self) -> _Badge:
        """创建一枚徽章标签。"""
        return _Badge(self)

    def set_counts(self, counts: Dict[str, int], selected: int = 0,
                   total: int = 0) -> None:
        """刷新徽章：显示每类已选数量以及“已选 / 总计”。"""
        items = ordered_status_items(counts)
        while len(self._badges) < len(items):
            badge = self._create_badge()
            badge.setVisible(False)
            self._layout.insertWidget(self._layout.count() - 1, badge)
            self._badges.append(badge)

        for index, badge in enumerate(self._badges):
            if index >= len(items):
                badge.hide()
                continue
            status, count = items[index]
            background, foreground = status_badge_colors(status)
            self._apply_badge(
                badge,
                f"{self._short_name(status)} {count}",
                badge_style(background, foreground),
            )
            badge.setToolTip(f"{status}：已选 {count} 个文件")
            badge.setVisible(True)

        self._apply_badge(
            self._total_badge,
            f"已选 {selected} / {total}",
            badge_style(BADGE_TOTAL_BACKGROUND, '#374151'),
        )
        self._total_badge.setToolTip(f"已选中 {selected} 个文件，共 {total} 个文件")
        self._total_badge.setVisible(True)

    @staticmethod
    def _apply_badge(badge: _Badge, text: str, style: str) -> None:
        """更新徽章文字与样式，并通知布局重新计算尺寸。"""
        badge.setStyleSheet(style)
        badge.setText(text)
        badge.updateGeometry()

    def badge_texts(self) -> List[str]:
        """返回当前可见的类型徽章文本，用于测试与调试。"""
        return [badge.text() for badge in self._badges if badge.isVisible()]

    def total_text(self) -> str:
        """返回总计徽章文本。"""
        return self._total_badge.text()

    @staticmethod
    def _short_name(status: str) -> str:
        """把“已修改”简写为“修改”，便于徽章紧凑展示。"""
        if status.startswith('已') and len(status) > 1:
            return status[1:]
        return status
