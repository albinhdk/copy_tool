# Git 改动文件提取工具 (Git Copy Tool)

这是一个基于 Python 和 PySide6 构建的现代化桌面应用程序。它的主要功能是：自动解析 Git 仓库中的文件变更（如新增、修改的文件），并允许用户将这些变动的文件一键提取/拷贝到目标目录，同时**自动保持原始的文件夹层级结构**。

对于需要将部分改动打包发送给其他人，或者进行增量部署的开发者来说，这能极大节省手动提取文件的时间。

## ✨ 核心特性

- **一键提取 Git 变动**：自动调用 `git status --porcelain`，精准提取所有待提交或未提交的文件改动。
- **自动还原目录结构**：拷贝到目标路径时，自动重建源文件所在的嵌套目录，无需手动逐层创建文件夹。
- **现代且舒适的 UI**：基于 Windows 11 设计语言的宽裕边距、圆角与色彩搭配，界面清新现代，交互流畅。
- **智能历史记忆**：自动记忆并保存最近 10 次使用过的“源目录”和“目标目录”，下次打开下拉即可选择。
- **边界与异常安全**：
  - 自动处理中文路径乱码。
  - 自动处理 Git 文件重命名（`R` 状态）的解析。
  - 清空目标目录前进行强制二次确认，防止误删重要文件。
  - 针对 Windows 打包的无头进程优化，避免运行卡死。

## 🚀 快速运行

本项目无需复杂配置即可运行。请确保您已经安装了 Python 3 并在机器上配置了 Git 环境。

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
2. **运行程序**
   您可以直接运行 Python 文件：
   ```bash
   python main.py
   ```
   或者直接双击运行项目提供的快捷脚本：
   - Windows 批处理: `run.bat`
   - PowerShell 脚本: `run.ps1`

## 📦 打包为独立执行程序 (EXE)

如果您希望在没有 Python 环境的电脑上运行，可以将其打包为一个独立的 EXE 文件。

运行我们提供的打包脚本：
```powershell
./build.ps1
```
打包完成后，可以在 `dist/` 文件夹中找到 `Git改动提取工具.exe`，直接双击运行即可。

## 🛠️ 技术栈

- **语言**: Python 3
- **GUI 框架**: PySide6 (Qt for Python)
- **测试框架**: pytest
- **其他依赖**: Git (依赖系统的 `git` 命令行)

## 📁 项目结构

```
copy_tool/
├── src/
│   ├── models/           # 数据模型层
│   │   ├── file_item.py      # 文件项模型
│   │   └── git_status.py     # Git状态模型
│   ├── views/            # 视图层
│   │   ├── main_window.py    # 主窗口视图
│   │   ├── file_list_view.py # 文件列表视图
│   │   └── file_tree_view.py # 文件树视图
│   ├── controllers/      # 控制器层
│   │   └── main_controller.py # 主控制器
│   ├── services/         # 服务层
│   │   ├── git_service.py    # Git操作服务
│   │   ├── file_service.py   # 文件操作服务
│   │   └── config_service.py # 配置管理服务
│   └── components/       # 可复用UI组件
│       └── history_combo.py  # 历史记录下拉框
├── tests/                # 单元测试
├── main.py              # 应用入口
├── requirements.txt     # 依赖列表
└── README.md
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_git_service.py -v
```

## 📄 许可

MIT License
