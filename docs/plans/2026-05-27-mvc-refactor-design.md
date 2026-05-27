# MVC架构重构设计文档

## 1. 项目概述

### 当前状态
- 所有代码集中在`main.py`的`GitCopyTool`类中（约580行）
- UI逻辑、业务逻辑、数据访问混合在一起
- 难以测试和维护

### 重构目标
- 实现完整的MVC分层架构
- 分离关注点，提高代码可维护性
- 添加基础单元测试
- 保持功能向后兼容

## 2. 目录结构设计

```
copy_tool/
├── src/
│   ├── models/           # 数据模型层
│   │   ├── __init__.py
│   │   ├── file_item.py      # 文件项模型
│   │   └── git_status.py     # Git状态模型
│   ├── views/            # 视图层
│   │   ├── __init__.py
│   │   ├── main_window.py    # 主窗口视图
│   │   ├── file_list_view.py # 文件列表视图
│   │   └── file_tree_view.py # 文件树视图
│   ├── controllers/      # 控制器层
│   │   ├── __init__.py
│   │   └── main_controller.py # 主控制器
│   ├── services/         # 服务层
│   │   ├── __init__.py
│   │   ├── git_service.py    # Git操作服务
│   │   ├── file_service.py   # 文件操作服务
│   │   └── config_service.py # 配置管理服务
│   └── components/       # 可复用UI组件
│       ├── __init__.py
│       └── history_combo.py  # 历史记录下拉框
├── tests/                # 测试目录
│   ├── __init__.py
│   ├── test_git_service.py
│   └── test_file_service.py
├── main.py              # 应用入口
├── requirements.txt
└── README.md
```

## 3. 各层职责与接口设计

### 3.1 Models层（数据模型）

#### FileItem类
```python
class FileItem:
    def __init__(self, relative_path: str, status: str, selected: bool = True):
        self.relative_path = relative_path
        self.status = status
        self.selected = selected
    
    def get_display_text(self) -> str:
        return f"[{self.status}] {self.relative_path}"
```

#### GitStatus类
```python
class GitStatus:
    def __init__(self, repo_path: str, files: list[FileItem]):
        self.repo_path = repo_path
        self.files = files
    
    def get_selected_files(self) -> list[str]:
        return [f.relative_path for f in self.files if f.selected]
    
    def get_statistics(self) -> dict:
        total = len(self.files)
        selected = sum(1 for f in self.files if f.selected)
        return {"total": total, "selected": selected}
```

### 3.2 Views层（视图）

#### MainWindow
- 负责UI布局和组件展示
- 转发用户交互信号（按钮点击、目录选择等）
- 不包含业务逻辑

#### FileListView / FileTreeView
- 展示文件列表/树形结构
- 支持复选框选择
- 发出选择变化信号

### 3.3 Controllers层（控制器）

#### MainController
```python
class MainController:
    def __init__(self, view: MainWindow, git_service: GitService, 
                 file_service: FileService, config_service: ConfigService):
        self.view = view
        self.git_service = git_service
        self.file_service = file_service
        self.config_service = config_service
        self._connect_signals()
    
    def _connect_signals(self):
        # 连接视图信号到处理方法
        pass
    
    def on_source_changed(self, path: str):
        # 处理源目录变化
        pass
    
    def on_start_copy(self):
        # 处理开始拷贝
        pass
```

### 3.4 Services层（服务）

#### GitService
```python
class GitService:
    def scan_repository(self, repo_path: str) -> GitStatus:
        # 执行git status命令并解析结果
        pass
    
    def _parse_status_line(self, line: str) -> FileItem:
        # 解析单行git status输出
        pass
```

#### FileService
```python
class FileService:
    def copy_files(self, source_dir: str, target_dir: str, 
                   files: list[str]) -> tuple[int, list[str]]:
        # 拷贝文件到目标目录，保持目录结构
        pass
    
    def clear_directory(self, dir_path: str):
        # 清空目录内容
        pass
```

#### ConfigService
```python
class ConfigService:
    def __init__(self, settings: QSettings):
        self.settings = settings
    
    def get_source_history(self) -> list[str]:
        # 获取源目录历史记录
        pass
    
    def save_source_history(self, path: str):
        # 保存源目录历史记录
        pass
```

### 3.5 Components层（组件）

#### HistoryComboBox
```python
class HistoryComboBox(QComboBox):
    def __init__(self, placeholder: str = ""):
        super().__init__()
        self.setEditable(True)
        self.lineEdit().setPlaceholderText(placeholder)
    
    def load_history(self, history: list[str]):
        # 加载历史记录
        pass
    
    def add_to_history(self, path: str, max_items: int = 10):
        # 添加到历史记录
        pass
```

## 4. 实施步骤

### 阶段一：基础架构搭建
1. 创建目录结构和`__init__.py`文件
2. 定义基础模型类（FileItem、GitStatus）
3. 实现ConfigService（从原代码提取历史记录逻辑）

### 阶段二：服务层实现
1. 实现GitService（封装原scan_git_files逻辑）
2. 实现FileService（封装原start_copy中的文件操作）
3. 确保服务层可独立测试，不依赖PySide6

### 阶段三：视图层重构
1. 提取HistoryComboBox组件
2. 拆分FileListView和FileTreeView
3. 重构MainWindow，移除业务逻辑

### 阶段四：控制器层实现
1. 创建MainController，连接视图和服务
2. 实现信号槽连接和业务流程
3. 处理异常和用户反馈

### 阶段五：测试与验证
1. 为GitService和FileService编写单元测试
2. 集成测试：验证完整工作流程
3. 更新main.py入口和打包配置

## 5. 测试策略

### 单元测试
- 使用pytest框架
- 重点测试GitService和FileService
- 对Git命令执行进行Mock，避免依赖真实仓库

### 关键测试场景
1. Git状态解析：各种文件状态（M、A、D、R、??）的正确识别
2. 文件拷贝：目录结构保持、错误处理、权限问题
3. 历史记录：保存、加载、去重、最大数量限制
4. 异常处理：Git命令失败、路径不存在、磁盘空间不足

### 测试示例
```python
# test_git_service.py
def test_parse_status_line_modified():
    service = GitService()
    item = service._parse_status_line("M  file.txt")
    assert item.relative_path == "file.txt"
    assert item.status == "已修改"

def test_parse_status_line_renamed():
    service = GitService()
    item = service._parse_status_line("R  old.txt -> new.txt")
    assert item.relative_path == "new.txt"
    assert item.status == "已重命名"
```

## 6. 风险控制

### 向后兼容
- 重构后功能行为不变
- 保持原有的用户界面和交互流程

### 渐进式验证
- 每完成一个阶段都运行现有功能
- 确保每个模块可独立工作

### 回滚机制
- 使用Git分支进行重构
- 失败可随时回滚到原始代码

### 打包验证
- 重构后确保PyInstaller打包正常
- 验证可执行文件功能完整

## 7. 依赖管理

### requirements.txt更新
```
PySide6>=6.0.0
pyinstaller>=6.0.0
pytest>=7.0.0
```

### 可选：开发依赖分离
```
# requirements-dev.txt
pytest>=7.0.0
pytest-mock>=3.0.0
```

## 8. 预期收益

1. **可维护性**：代码结构清晰，易于理解和修改
2. **可测试性**：服务层可独立测试，提高代码质量
3. **可扩展性**：新增功能只需添加相应模块
4. **团队协作**：不同开发者可并行开发不同层
5. **代码复用**：组件和服务可在其他项目中复用

## 9. 后续优化方向

1. 添加更多单元测试，提高测试覆盖率
2. 实现依赖注入，进一步解耦组件
3. 添加日志系统，便于调试和监控
4. 支持插件机制，扩展功能
5. 优化性能，支持大仓库场景