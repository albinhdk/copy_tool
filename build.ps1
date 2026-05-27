Write-Host "开始编译为可执行程序..." -ForegroundColor Cyan

# 确保在虚拟环境中安装了 pyinstaller
if (-Not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "正在安装打包工具 PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# 使用 PyInstaller 进行打包
# --noconsole: 运行时不显示黑色命令行窗口
# --onefile: 打包成单文件 (如果想要启动更快，可以去掉这个参数变成文件夹形式)
# --clean: 清理之前的缓存
# --windowed: 明确指定为窗口程序
Write-Host "执行 PyInstaller 打包..." -ForegroundColor Yellow
pyinstaller --noconsole --onefile --windowed --clean --name "GitCopyTool" main.py

Write-Host "`n编译完成！" -ForegroundColor Green
Write-Host "你的可执行文件在: .\dist\GitCopyTool.exe" -ForegroundColor Green
