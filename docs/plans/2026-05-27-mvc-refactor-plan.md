# MVC架构重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有的单文件Git改动提取工具重构为完整的MVC架构，提高代码可维护性和可测试性

**Architecture:** 采用标准MVC模式，分离Models、Views、Controllers、Services和Components层。服务层封装业务逻辑，可独立测试；视图层只负责展示；控制器层协调各组件。

**Tech Stack:** Python 3, PySide6, pytest, pathlib

---

## Task 1: 创建目录结构和基础文件

**Files:**
- Create: `src/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/views/__init__.py`
- Create: `src/controllers/__init__.py`
- Create: `src/services/__init__.py`
- Create: `src/components/__init__.py`
- Create: `tests/__init__.py`

**Step 1: 创建目录结构**

```bash
mkdir -p src/models src/views src/controllers src/services src/components tests
```

**Step 2: 创建__init__.py文件**

```python
# src/__init__.py
# Git改动提取工具 - MVC架构

# src/models/__init__.py
from .file_item import FileItem
from .git_status import GitStatus

# src/views/__init__.py
from .main_window import MainWindow
from .file_list_view import FileListView
from .file_tree_view import FileTreeView

# src/controllers/__init__.py
from .main_controller import MainController

# src/services/__init__.py
from .git_service import GitService
from .file_service import FileService
from .config_service import ConfigService

# src/components/__init__.py
from .history_combo import HistoryComboBox

# tests/__init__.py
# 测试包
```

**Step 3: 验证目录结构**

```bash
tree src/ /F
tree tests/ /F
```

Expected: 显示完整的目录结构

**Step 4: Commit**

```bash
git add src/ tests/
git commit -m "feat: 创建MVC目录结构"
```

---

## Task 2: 实现FileItem模型

**Files:**
- Create: `src/models/file_item.py`
- Create: `tests/test_file_item.py`

**Step 1: 编写失败的测试**

```python
# tests/test_file_item.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.file_item import FileItem

def test_file_item_creation():
    """测试FileItem对象创建"""
    item = FileItem("src/main.py", "已修改", True)
    assert item.relative_path == "src/main.py"
    assert item.status == "已修改"
    assert item.selected == True

def test_file_item_default_selected():
    """测试FileItem默认选中状态"""
    item = FileItem("test.txt", "未跟踪")
    assert item.selected == True

def test_file_item_display_text():
    """测试显示文本格式"""
    item = FileItem("src/main.py", "已修改")
    assert item.get_display_text() == "[已修改] src/main.py"

def test_file_item_str_representation():
    """测试字符串表示"""
    item = FileItem("test.txt", "已添加")
    assert str(item) == "[已添加] test.txt"
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_file_item.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.models.file_item'"

**Step 3: 编写最小实现**

```python
# src/models/file_item.py
class FileItem:
    """文件项模型，封装单个文件的状态信息"""
    
    def __init__(self, relative_path: str, status: str, selected: bool = True):
        """
        初始化文件项
        
        Args:
            relative_path: 相对于仓库根目录的文件路径
            status: 文件状态（已修改、已添加、未跟踪等）
            selected: 是否选中，默认为True
        """
        self.relative_path = relative_path
        self.status = status
        self.selected = selected
    
    def get_display_text(self) -> str:
        """获取显示文本，格式为: [状态] 文件路径"""
        return f"[{self.status}] {self.relative_path}"
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.get_display_text()
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_file_item.py -v
```

Expected: 4个测试全部PASS

**Step 5: Commit**

```bash
git add src/models/file_item.py tests/test_file_item.py
git commit -m "feat: 实现FileItem模型类"
```

---

## Task 3: 实现GitStatus模型

**Files:**
- Create: `src/models/git_status.py`
- Create: `tests/test_git_status.py`

**Step 1: 编写失败的测试**

```python
# tests/test_git_status.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.file_item import FileItem
from src.models.git_status import GitStatus

def test_git_status_creation():
    """测试GitStatus对象创建"""
    files = [
        FileItem("file1.txt", "已修改"),
        FileItem("file2.txt", "已添加")
    ]
    status = GitStatus("/path/to/repo", files)
    assert status.repo_path == "/path/to/repo"
    assert len(status.files) == 2

def test_git_status_get_selected_files():
    """测试获取选中的文件"""
    files = [
        FileItem("file1.txt", "已修改", True),
        FileItem("file2.txt", "已添加", False),
        FileItem("file3.txt", "未跟踪", True)
    ]
    status = GitStatus("/repo", files)
    selected = status.get_selected_files()
    assert len(selected) == 2
    assert "file1.txt" in selected
    assert "file3.txt" in selected

def test_git_status_get_statistics():
    """测试获取统计信息"""
    files = [
        FileItem("file1.txt", "已修改", True),
        FileItem("file2.txt", "已添加", False),
        FileItem("file3.txt", "未跟踪", True)
    ]
    status = GitStatus("/repo", files)
    stats = status.get_statistics()
    assert stats["total"] == 3
    assert stats["selected"] == 2

def test_git_status_empty_files():
    """测试空文件列表"""
    status = GitStatus("/repo", [])
    assert status.get_selected_files() == []
    assert status.get_statistics() == {"total": 0, "selected": 0}
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_git_status.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.models.git_status'"

**Step 3: 编写最小实现**

```python
# src/models/git_status.py
from typing import List, Dict
from .file_item import FileItem

class GitStatus:
    """Git状态模型，封装仓库的文件状态信息"""
    
    def __init__(self, repo_path: str, files: List[FileItem]):
        """
        初始化Git状态
        
        Args:
            repo_path: 仓库根目录路径
            files: 文件项列表
        """
        self.repo_path = repo_path
        self.files = files
    
    def get_selected_files(self) -> List[str]:
        """获取所有选中的文件路径列表"""
        return [f.relative_path for f in self.files if f.selected]
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        total = len(self.files)
        selected = sum(1 for f in self.files if f.selected)
        return {"total": total, "selected": selected}
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_git_status.py -v
```

Expected: 4个测试全部PASS

**Step 5: Commit**

```bash
git add src/models/git_status.py tests/test_git_status.py
git commit -m "feat: 实现GitStatus模型类"
```

---

## Task 4: 实现ConfigService

**Files:**
- Create: `src/services/config_service.py`
- Create: `tests/test_config_service.py`

**Step 1: 编写失败的测试**

```python
# tests/test_config_service.py
import pytest
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtCore import QSettings
from src.services.config_service import ConfigService

@pytest.fixture
def config_service():
    """创建临时配置服务实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = QSettings(os.path.join(tmpdir, "test.ini"), QSettings.Format.IniFormat)
        service = ConfigService(settings)
        yield service

def test_get_source_history_empty(config_service):
    """测试获取空源目录历史"""
    history = config_service.get_source_history()
    assert history == []

def test_save_and_get_source_history(config_service):
    """测试保存和获取源目录历史"""
    config_service.save_source_history("/path/to/repo1")
    config_service.save_source_history("/path/to/repo2")
    
    history = config_service.get_source_history()
    assert len(history) == 2
    assert history[0] == "/path/to/repo2"  # 最新的在前
    assert history[1] == "/path/to/repo1"

def test_source_history_max_items(config_service):
    """测试历史记录最大数量限制"""
    for i in range(15):
        config_service.save_source_history(f"/repo/{i}")
    
    history = config_service.get_source_history()
    assert len(history) == 10  # 最多保留10条
    assert history[0] == "/repo/14"  # 最新的在前

def test_source_history_dedup(config_service):
    """测试历史记录去重"""
    config_service.save_source_history("/repo1")
    config_service.save_source_history("/repo2")
    config_service.save_source_history("/repo1")  # 重复
    
    history = config_service.get_source_history()
    assert len(history) == 2
    assert history[0] == "/repo1"  # 移到最前
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_config_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.config_service'"

**Step 3: 编写最小实现**

```python
# src/services/config_service.py
from typing import List
from PySide6.QtCore import QSettings

class ConfigService:
    """配置管理服务，处理历史记录和用户配置"""
    
    def __init__(self, settings: QSettings):
        """
        初始化配置服务
        
        Args:
            settings: QSettings实例，用于持久化存储
        """
        self.settings = settings
    
    def get_source_history(self) -> List[str]:
        """获取源目录历史记录"""
        return self.settings.value("src_history", [])
    
    def save_source_history(self, path: str, max_items: int = 10):
        """
        保存源目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认为10
        """
        if not path:
            return
        
        history = self.get_source_history()
        
        # 移除已存在的路径（如果有的话）
        if path in history:
            history.remove(path)
        
        # 添加到最前面
        history.insert(0, path)
        
        # 限制最大数量
        history = history[:max_items]
        
        self.settings.setValue("src_history", history)
    
    def get_target_history(self) -> List[str]:
        """获取目标目录历史记录"""
        return self.settings.value("tgt_history", [])
    
    def save_target_history(self, path: str, max_items: int = 10):
        """
        保存目标目录到历史记录
        
        Args:
            path: 目录路径
            max_items: 最大记录数量，默认为10
        """
        if not path:
            return
        
        history = self.get_target_history()
        
        if path in history:
            history.remove(path)
        
        history.insert(0, path)
        history = history[:max_items]
        
        self.settings.setValue("tgt_history", history)
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_config_service.py -v
```

Expected: 4个测试全部PASS

**Step 5: Commit**

```bash
git add src/services/config_service.py tests/test_config_service.py
git commit -m "feat: 实现ConfigService配置管理服务"
```

---

## Task 5: 实现GitService

**Files:**
- Create: `src/services/git_service.py`
- Create: `tests/test_git_service.py`

**Step 1: 编写失败的测试**

```python
# tests/test_git_service.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.git_service import GitService

def test_parse_status_line_modified():
    """测试解析修改状态"""
    service = GitService()
    item = service._parse_status_line("M  file.txt")
    assert item.relative_path == "file.txt"
    assert item.status == "已修改"

def test_parse_status_line_added():
    """测试解析添加状态"""
    service = GitService()
    item = service._parse_status_line("A  new_file.py")
    assert item.relative_path == "new_file.py"
    assert item.status == "已添加"

def test_parse_status_line_untracked():
    """测试解析未跟踪状态"""
    service = GitService()
    item = service._parse_status_line("?? temp.txt")
    assert item.relative_path == "temp.txt"
    assert item.status == "未跟踪"

def test_parse_status_line_renamed():
    """测试解析重命名状态"""
    service = GitService()
    item = service._parse_status_line("R  old.txt -> new.txt")
    assert item.relative_path == "new.txt"
    assert item.status == "已重命名"

def test_parse_status_line_deleted():
    """测试解析删除状态"""
    service = GitService()
    item = service._parse_status_line("D  deleted.txt")
    assert item.relative_path == "deleted.txt"
    assert item.status == "已删除"

def test_parse_status_line_invalid():
    """测试解析无效行"""
    service = GitService()
    item = service._parse_status_line("X")
    assert item is None

def test_get_status_label():
    """测试状态标签映射"""
    service = GitService()
    assert service._get_status_label("M ") == "已修改"
    assert service._get_status_label(" M") == "已修改"
    assert service._get_status_label("A ") == "已添加"
    assert service._get_status_label("??") == "未跟踪"
    assert service._get_status_label("D ") == "已删除"
    assert service._get_status_label("R ") == "已重命名"
    assert service._get_status_label("XX") == "XX"  # 未知状态返回原值
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_git_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.git_service'"

**Step 3: 编写最小实现**

```python
# src/services/git_service.py
import subprocess
import sys
from typing import Optional, List
from ..models.file_item import FileItem
from ..models.git_status import GitStatus

class GitService:
    """Git操作服务，执行Git命令并解析结果"""
    
    def __init__(self):
        """初始化Git服务"""
        self._status_map = {
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
    
    def scan_repository(self, repo_path: str) -> Optional[GitStatus]:
        """
        扫描Git仓库，获取文件状态
        
        Args:
            repo_path: 仓库根目录路径
            
        Returns:
            GitStatus对象，失败时返回None
        """
        import os
        
        if not repo_path or not os.path.isdir(repo_path):
            return None
        
        # 检查是否是Git仓库
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            return None
        
        try:
            # 执行git status命令
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                ["git", "-c", "core.quotepath=false", "status", "--porcelain", "-u"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )
            
            # 解析输出
            files = []
            for line in result.stdout.splitlines():
                item = self._parse_status_line(line)
                if item:
                    # 检查文件是否存在（排除已删除的文件）
                    full_path = os.path.join(repo_path, item.relative_path)
                    if os.path.isfile(full_path) or 'D' in line[:2]:
                        files.append(item)
            
            # 按路径排序
            files.sort(key=lambda x: x.relative_path)
            
            return GitStatus(repo_path, files)
            
        except Exception as e:
            print(f"扫描Git仓库失败: {e}")
            return None
    
    def _parse_status_line(self, line: str) -> Optional[FileItem]:
        """
        解析单行git status输出
        
        Args:
            line: git status --porcelain的输出行
            
        Returns:
            FileItem对象，无效行返回None
        """
        if len(line) < 4:
            return None
        
        # 提取状态和文件名
        status = line[:2]
        filename = line[3:].strip()
        
        # 处理重命名情况: "R  old -> new"
        if "->" in filename:
            filename = filename.split("->")[1].strip()
        
        # 去除可能的引号
        filename = filename.strip('"\'')
        
        # 获取友好的状态标签
        status_label = self._get_status_label(status)
        
        return FileItem(filename, status_label)
    
    def _get_status_label(self, status: str) -> str:
        """
        将git status状态码转换为友好的中文标签
        
        Args:
            status: 两个字符的状态码
            
        Returns:
            中文状态标签
        """
        return self._status_map.get(status, status)
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_git_service.py -v
```

Expected: 7个测试全部PASS

**Step 5: Commit**

```bash
git add src/services/git_service.py tests/test_git_service.py
git commit -m "feat: 实现GitService服务"
```

---

## Task 6: 实现FileService

**Files:**
- Create: `src/services/file_service.py`
- Create: `tests/test_file_service.py`

**Step 1: 编写失败的测试**

```python
# tests/test_file_service.py
import pytest
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.file_service import FileService

@pytest.fixture
def file_service():
    """创建FileService实例"""
    return FileService()

@pytest.fixture
def temp_dirs():
    """创建临时源目录和目标目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(src_dir)
        os.makedirs(tgt_dir)
        
        # 创建测试文件结构
        os.makedirs(os.path.join(src_dir, "subdir"))
        with open(os.path.join(src_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(src_dir, "subdir", "file2.txt"), "w") as f:
            f.write("content2")
        
        yield src_dir, tgt_dir

def test_copy_files_success(file_service, temp_dirs):
    """测试成功拷贝文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["file1.txt", "subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 2
    assert len(errors) == 0
    assert os.path.exists(os.path.join(tgt_dir, "file1.txt"))
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))
    
    # 验证内容
    with open(os.path.join(tgt_dir, "file1.txt")) as f:
        assert f.read() == "content1"

def test_copy_files_preserve_structure(file_service, temp_dirs):
    """测试保持目录结构"""
    src_dir, tgt_dir = temp_dirs
    files = ["subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 1
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))

def test_copy_files_nonexistent(file_service, temp_dirs):
    """测试拷贝不存在的文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["nonexistent.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 0
    assert len(errors) == 0  # 不存在的文件被静默跳过

def test_clear_directory(file_service, temp_dirs):
    """测试清空目录"""
    _, tgt_dir = temp_dirs
    
    # 创建一些文件
    with open(os.path.join(tgt_dir, "test.txt"), "w") as f:
        f.write("test")
    os.makedirs(os.path.join(tgt_dir, "subdir"))
    
    file_service.clear_directory(tgt_dir)
    
    # 验证目录为空
    assert len(os.listdir(tgt_dir)) == 0

def test_clear_nonexistent_directory(file_service):
    """测试清空不存在的目录"""
    # 应该不抛出异常
    file_service.clear_directory("/nonexistent/path")
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_file_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.file_service'"

**Step 3: 编写最小实现**

```python
# src/services/file_service.py
import os
import shutil
from typing import List, Tuple

class FileService:
    """文件操作服务，处理文件拷贝和目录管理"""
    
    def copy_files(self, source_dir: str, target_dir: str, 
                   files: List[str]) -> Tuple[int, List[str]]:
        """
        拷贝文件到目标目录，保持目录结构
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径
            files: 要拷贝的文件相对路径列表
            
        Returns:
            成功拷贝的文件数量和错误信息列表
        """
        success_count = 0
        error_messages = []
        
        for rel_path in files:
            src_path = os.path.join(source_dir, rel_path)
            tgt_path = os.path.join(target_dir, rel_path)
            
            if os.path.exists(src_path):
                try:
                    # 确保目标文件夹存在
                    os.makedirs(os.path.dirname(tgt_path), exist_ok=True)
                    shutil.copy2(src_path, tgt_path)
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"{rel_path}: {str(e)}")
            # 不存在的文件静默跳过（可能是已删除的文件）
        
        return success_count, error_messages
    
    def clear_directory(self, dir_path: str):
        """
        清空目录中的所有内容
        
        Args:
            dir_path: 要清空的目录路径
        """
        if not os.path.exists(dir_path):
            return
        
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"清空目录失败 {item_path}: {e}")
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_file_service.py -v
```

Expected: 5个测试全部PASS

**Step 5: Commit**

```bash
git add src/services/file_service.py tests/test_file_service.py
git commit -m "feat: 实现FileService文件操作服务"
```

---

## Task 7: 实现HistoryComboBox组件

**Files:**
- Create: `src/components/history_combo.py`

**Step 1: 编写实现**

```python
# src/components/history_combo.py
from typing import List
from PySide6.QtWidgets import QComboBox

class HistoryComboBox(QComboBox):
    """带历史记录的下拉框组件"""
    
    def __init__(self, placeholder: str = "", parent=None):
        """
        初始化历史记录下拉框
        
        Args:
            placeholder: 占位符文本
            parent: 父组件
        """
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText(placeholder)
        self.setFixedHeight(32)
    
    def load_history(self, history: List[str]):
        """
        加载历史记录
        
        Args:
            history: 历史记录列表
        """
        self.blockSignals(True)
        self.clear()
        if history:
            self.addItems(history)
        self.setCurrentText("")
        self.blockSignals(False)
    
    def add_to_history(self, path: str, max_items: int = 10):
        """
        添加路径到历史记录
        
        Args:
            path: 要添加的路径
            max_items: 最大记录数量
        """
        if not path:
            return
        
        # 获取当前所有项
        history = [self.itemText(i) for i in range(self.count())]
        
        # 移除已存在的路径
        if path in history:
            history.remove(path)
        
        # 添加到最前面
        history.insert(0, path)
        
        # 限制最大数量
        history = history[:max_items]
        
        # 刷新下拉框
        self.blockSignals(True)
        self.clear()
        self.addItems(history)
        self.setCurrentText(path)
        self.blockSignals(False)
        
        return history
```

**Step 2: Commit**

```bash
git add src/components/history_combo.py
git commit -m "feat: 实现HistoryComboBox组件"
```

---

## Task 8: 实现FileListView

**Files:**
- Create: `src/views/file_list_view.py`

**Step 1: 编写实现**

```python
# src/views/file_list_view.py
from typing import List
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem

class FileListView(QListWidget):
    """文件列表视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    
    def __init__(self, parent=None):
        """初始化文件列表视图"""
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self._setup_style()
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
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
    
    def load_files(self, files: List[FileItem]):
        """
        加载文件列表
        
        Args:
            files: 文件项列表
        """
        self.blockSignals(True)
        self.clear()
        
        for file_item in files:
            item = QListWidgetItem(file_item.get_display_text())
            item.setData(Qt.ItemDataRole.UserRole, file_item.relative_path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
            self.addItem(item)
        
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表"""
        selected = []
        for i in range(self.count()):
            item = self.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total = self.count()
        selected = sum(1 for i in range(total) if self.item(i).checkState() == Qt.CheckState.Checked)
        return {"total": total, "selected": selected}
    
    def set_all_checked(self, checked: bool):
        """设置所有项的选中状态"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.blockSignals(True)
        for i in range(self.count()):
            self.item(i).setCheckState(state)
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _on_item_changed(self, item: QListWidgetItem):
        """项状态变化处理"""
        self.selection_changed.emit()
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
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
        
        select_all = QAction("全选", self)
        select_all.triggered.connect(lambda: self.set_all_checked(True))
        
        deselect_all = QAction("全不选", self)
        deselect_all.triggered.connect(lambda: self.set_all_checked(False))
        
        menu.addAction(select_all)
        menu.addAction(deselect_all)
        
        menu.exec(self.mapToGlobal(pos))
```

**Step 2: Commit**

```bash
git add src/views/file_list_view.py
git commit -m "feat: 实现FileListView组件"
```

---

## Task 9: 实现FileTreeView

**Files:**
- Create: `src/views/file_tree_view.py`

**Step 1: 编写实现**

```python
# src/views/file_tree_view.py
from typing import List, Dict
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from ..models.file_item import FileItem

class FileTreeView(QTreeWidget):
    """文件树视图组件"""
    
    selection_changed = Signal()  # 选择变化信号
    
    def __init__(self, parent=None):
        """初始化文件树视图"""
        super().__init__(parent)
        self.setHeaderLabels(["文件路径", "状态"])
        self.setColumnCount(2)
        self.setColumnWidth(0, 400)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self._setup_style()
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
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
        """)
    
    def load_files(self, files: List[FileItem]):
        """
        加载文件列表，构建树形结构
        
        Args:
            files: 文件项列表
        """
        self.blockSignals(True)
        self.clear()
        
        # 构建树形结构
        for file_item in files:
            parts = file_item.relative_path.replace("\\", "/").split("/")
            parent = self.invisibleRootItem()
            
            # 创建或查找目录节点
            for i, part in enumerate(parts[:-1]):
                found = None
                for j in range(parent.childCount()):
                    if parent.child(j).text(0) == part:
                        found = parent.child(j)
                        break
                
                if found is None:
                    found = QTreeWidgetItem(parent, [part, ""])
                    found.setFlags(found.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    found.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
                    parent = found
                else:
                    parent = found
            
            # 创建文件节点
            file_item_widget = QTreeWidgetItem(parent, [parts[-1], file_item.status])
            file_item_widget.setData(0, Qt.ItemDataRole.UserRole, file_item.relative_path)
            file_item_widget.setFlags(file_item_widget.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            file_item_widget.setCheckState(0, Qt.CheckState.Checked if file_item.selected else Qt.CheckState.Unchecked)
        
        self.expandAll()
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表"""
        selected = []
        self._collect_checked(self.invisibleRootItem(), selected)
        return selected
    
    def _collect_checked(self, parent: QTreeWidgetItem, selected: List[str]):
        """递归收集选中的文件"""
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.childCount() == 0:  # 叶子节点（文件）
                if item.checkState(0) == Qt.CheckState.Checked:
                    rel_path = item.data(0, Qt.ItemDataRole.UserRole)
                    if rel_path:
                        selected.append(rel_path)
            else:
                self._collect_checked(item, selected)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        total, selected = self._count_items(self.invisibleRootItem())
        return {"total": total, "selected": selected}
    
    def _count_items(self, parent: QTreeWidgetItem) -> tuple:
        """递归统计文件数量"""
        total = 0
        selected = 0
        
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.childCount() == 0:  # 叶子节点
                total += 1
                if item.checkState(0) == Qt.CheckState.Checked:
                    selected += 1
            else:
                t, s = self._count_items(item)
                total += t
                selected += s
        
        return total, selected
    
    def set_all_checked(self, checked: bool):
        """设置所有项的选中状态"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.blockSignals(True)
        self._set_checked_recursive(self.invisibleRootItem(), state)
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _set_checked_recursive(self, parent: QTreeWidgetItem, state: Qt.CheckState):
        """递归设置选中状态"""
        for i in range(parent.childCount()):
            item = parent.child(i)
            item.setCheckState(0, state)
            self._set_checked_recursive(item, state)
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """项状态变化处理"""
        # 级联更新子项
        self.blockSignals(True)
        self._propagate_check(item, item.checkState(0))
        self.blockSignals(False)
        self.selection_changed.emit()
    
    def _propagate_check(self, item: QTreeWidgetItem, state: Qt.CheckState):
        """级联传播选中状态到子项"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._propagate_check(child, state)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
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
        
        select_all = QAction("全选", self)
        select_all.triggered.connect(lambda: self.set_all_checked(True))
        
        deselect_all = QAction("全不选", self)
        deselect_all.triggered.connect(lambda: self.set_all_checked(False))
        
        menu.addAction(select_all)
        menu.addAction(deselect_all)
        
        menu.exec(self.mapToGlobal(pos))
```

**Step 2: Commit**

```bash
git add src/views/file_tree_view.py
git commit -m "feat: 实现FileTreeView组件"
```

---

## Task 10: 实现MainWindow

**Files:**
- Create: `src/views/main_window.py`

**Step 1: 编写实现**

```python
# src/views/main_window.py
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
```

**Step 2: Commit**

```bash
git add src/views/main_window.py
git commit -m "feat: 实现MainWindow主窗口视图"
```

---

## Task 11: 实现MainController

**Files:**
- Create: `src/controllers/main_controller.py`

**Step 1: 编写实现**

```python
# src/controllers/main_controller.py
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from ..views.main_window import MainWindow
from ..services.git_service import GitService
from ..services.file_service import FileService
from ..services.config_service import ConfigService

class MainController:
    """主控制器，协调视图和服务层"""
    
    def __init__(self, view: MainWindow, git_service: GitService,
                 file_service: FileService, config_service: ConfigService):
        """
        初始化主控制器
        
        Args:
            view: 主窗口视图
            git_service: Git服务
            file_service: 文件服务
            config_service: 配置服务
        """
        self.view = view
        self.git_service = git_service
        self.file_service = file_service
        self.config_service = config_service
        
        self._connect_signals()
        self._load_history()
    
    def _connect_signals(self):
        """连接视图信号到处理方法"""
        self.view.source_changed.connect(self._on_source_changed)
        self.view.scan_requested.connect(self._on_scan_requested)
        self.view.copy_requested.connect(self._on_copy_requested)
        self.view.browse_source_requested.connect(self._on_browse_source)
        self.view.browse_target_requested.connect(self._on_browse_target)
    
    def _load_history(self):
        """加载历史记录"""
        src_history = self.config_service.get_source_history()
        self.view.src_input.load_history(src_history)
        
        tgt_history = self.config_service.get_target_history()
        self.view.tgt_input.load_history(tgt_history)
    
    def _on_source_changed(self, path: str):
        """处理源目录变化"""
        if path and os.path.isdir(path):
            self._scan_repository(path)
    
    def _on_scan_requested(self):
        """处理扫描请求"""
        path = self.view.src_input.currentText().strip()
        if path:
            self._scan_repository(path)
    
    def _scan_repository(self, repo_path: str):
        """扫描Git仓库"""
        git_status = self.git_service.scan_repository(repo_path)
        
        if git_status is None:
            return
        
        # 更新视图
        self.view.file_list_view.load_files(git_status.files)
        self.view.file_tree_view.load_files(git_status.files)
        
        # 保存历史记录
        self.config_service.save_source_history(repo_path)
        self.view.src_input.add_to_history(repo_path)
    
    def _on_copy_requested(self):
        """处理拷贝请求"""
        src_dir = self.view.src_input.currentText().strip()
        tgt_dir = self.view.tgt_input.currentText().strip()
        
        # 验证路径
        if not src_dir or not os.path.exists(src_dir):
            self.view.show_message("错误", "源目录无效或不存在！", QMessageBox.Icon.Warning)
            return
        
        if not tgt_dir:
            self.view.show_message("错误", "请选择目标目录！", QMessageBox.Icon.Warning)
            return
        
        # 获取选中的文件
        selected_files = self.view.get_selected_files()
        
        if not selected_files:
            self.view.show_message("提示", "没有选中任何文件。", QMessageBox.Icon.Information)
            return
        
        # 确认清空目标目录
        if os.path.exists(tgt_dir) and os.listdir(tgt_dir):
            if not self.view.show_question(
                "清空目标目录确认",
                f"将要清空目标目录:\n{tgt_dir}\n\n里面现有的所有文件都会被永久删除！是否继续？"
            ):
                return
            
            try:
                self.file_service.clear_directory(tgt_dir)
            except Exception as e:
                self.view.show_message("清空失败", f"清空目标目录时发生错误:\n{str(e)}", QMessageBox.Icon.Critical)
                return
        
        # 执行拷贝
        success_count, error_messages = self.file_service.copy_files(src_dir, tgt_dir, selected_files)
        
        # 保存历史记录
        self.config_service.save_target_history(tgt_dir)
        self.view.tgt_input.add_to_history(tgt_dir)
        
        # 显示结果
        if error_messages:
            error_str = "\n".join(error_messages[:5])
            if len(error_messages) > 5:
                error_str += f"\n...及其他 {len(error_messages)-5} 个错误"
            self.view.show_message("完成，但有错误", f"成功拷贝 {success_count} 个文件。\n\n部分失败:\n{error_str}", QMessageBox.Icon.Warning)
        else:
            self.view.show_message("成功", f"成功拷贝了 {success_count} 个文件！\n\n已保持原始目录结构存放在:\n{tgt_dir}", QMessageBox.Icon.Information)
    
    def _on_browse_source(self):
        """处理浏览源目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择 Git 源目录")
        if dir_path:
            self.view.src_input.setCurrentText(dir_path)
    
    def _on_browse_target(self):
        """处理浏览目标目录"""
        dir_path = QFileDialog.getExistingDirectory(self.view, "选择目标目录")
        if dir_path:
            self.view.tgt_input.setCurrentText(dir_path)
```

**Step 2: Commit**

```bash
git add src/controllers/main_controller.py
git commit -m "feat: 实现MainController主控制器"
```

---

## Task 12: 更新main.py入口

**Files:**
- Modify: `main.py`

**Step 1: 更新main.py**

```python
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
```

**Step 2: 验证应用运行**

```bash
python main.py
```

Expected: 应用正常启动，界面与原版一致

**Step 3: Commit**

```bash
git add main.py
git commit -m "refactor: 更新main.py使用MVC架构"
```

---

## Task 13: 添加pytest依赖并运行所有测试

**Files:**
- Modify: `requirements.txt`

**Step 1: 更新requirements.txt**

```
PySide6>=6.0.0
pyinstaller>=6.0.0
pytest>=7.0.0
```

**Step 2: 安装依赖**

```bash
pip install -r requirements.txt
```

**Step 3: 运行所有测试**

```bash
pytest tests/ -v
```

Expected: 所有测试通过

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: 添加pytest依赖"
```

---

## Task 14: 更新README文档

**Files:**
- Modify: `README.md`

**Step 1: 更新README.md**

在README.md中添加项目结构说明：

```markdown
## 📁 项目结构

```
copy_tool/
├── src/
│   ├── models/           # 数据模型
│   ├── views/            # 视图层
│   ├── controllers/      # 控制器层
│   ├── services/         # 服务层
│   └── components/       # UI组件
├── tests/                # 单元测试
├── main.py              # 应用入口
└── requirements.txt     # 依赖列表
```

## 🧪 运行测试

```bash
pytest tests/ -v
```
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: 更新README添加项目结构说明"
```

---

## Task 15: 最终验证

**Step 1: 运行完整测试套件**

```bash
pytest tests/ -v --tb=short
```

Expected: 所有测试通过

**Step 2: 启动应用验证功能**

```bash
python main.py
```

验证点：
- 界面显示正常
- 源目录选择和扫描功能正常
- 文件列表和树形视图切换正常
- 目标目录选择正常
- 拷贝功能正常
- 历史记录功能正常

**Step 3: 打包验证**

```bash
./build.ps1
```

验证点：
- 打包成功
- 生成的exe可正常运行

**Step 4: 最终Commit**

```bash
git add .
git commit -m "feat: 完成MVC架构重构"
```

---

## 执行选项

**计划已保存到 `docs/plans/2026-05-27-mvc-refactor-plan.md`**

两种执行方式：

**1. 子代理驱动（当前会话）** - 我为每个任务分发新的子代理，任务间进行代码审查，快速迭代

**2. 并行会话（单独）** - 在新会话中打开执行计划，批量执行并设置检查点

**选择哪种方式？**