Write-Host "启动自动编译监控..." -ForegroundColor Cyan
Write-Host "监控目录: src/ 和 main.py" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止" -ForegroundColor Yellow
Write-Host ""

# 要监控的路径
$watchPaths = @(
    "$PSScriptRoot\src",
    "$PSScriptRoot\main.py"
)

# 创建文件系统监控器
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "$PSScriptRoot\src"
$watcher.IncludeSubdirectories = $true
$watcher.Filter = "*.py"
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName

# 防抖计时器
$global:lastBuildTime = [DateTime]::MinValue
$global:buildPending = $false

function Start-Build {
    $now = Get-Date
    $elapsed = ($now - $global:lastBuildTime).TotalSeconds
    
    # 防抖：2秒内不重复编译
    if ($elapsed -lt 2) {
        $global:buildPending = $true
        return
    }
    
    $global:lastBuildTime = $now
    Write-Host "
[$(Get-Date -Format 'HH:mm:ss')] 检测到变更，开始编译..." -ForegroundColor Cyan
    
    # 删除旧文件
    Remove-Item "dist\GitCopyTool.exe" -Force -ErrorAction SilentlyContinue
    
    # 执行编译
    $result = pyinstaller --noconsole --onefile --windowed --clean --name "GitCopyTool" main.py 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 编译成功! -> dist\GitCopyTool.exe" -ForegroundColor Green
    } else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 编译失败!" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
}

# 注册文件变更事件
$action = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 文件变更: $name" -ForegroundColor Yellow
    Start-Build
}

Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

# 保持脚本运行
Write-Host "
监控已启动，等待文件变更..." -ForegroundColor Green
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($global:buildPending) {
            $global:buildPending = $false
            Start-Build
        }
    }
} finally {
    $watcher.Dispose()
    Write-Host "
监控已停止" -ForegroundColor Red
}