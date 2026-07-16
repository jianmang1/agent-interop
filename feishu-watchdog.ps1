# feishu-watchdog.ps1 — 飞书连接看门狗
# 确保 Gateway 始终运行，飞书 WebSocket 不掉线
# 建议开机自启：放在启动文件夹或通过任务计划程序

param(
    [int]$CheckInterval = 30,          # 检查间隔（秒）
    [string]$HermesHome = "",          # Hermes 数据目录，留空自动检测
    [string]$RuntimePath = "",         # runtime 可执行文件路径，留空自动检测
    [switch]$InstallStartup = $false,  # 安装为开机自启
    [switch]$Uninstall = $false        # 移除开机自启
)

# ─── 自动检测路径 ──────────────────────────────────────────────

if (-not $HermesHome) {
    $HermesHome = $env:HERMES_HOME
    if (-not $HermesHome) { $HermesHome = "D:\Hermes Agent CN Desktop\data\hermes-home" }
}

if (-not $RuntimePath) {
    $possiblePaths = @(
        "$PSScriptRoot\hermes-agent-cn-runtime-win32-x64.exe",
        "D:\Hermes Agent CN Desktop\data\versions\0.18.2-cn.2\hermes-agent-cn-runtime-win32-x64.exe",
        "D:\Hermes Agent CN Desktop\data\versions\0.18.2-cn.2\hermes-agent-cn-desktop.exe"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) { $RuntimePath = $p; break }
    }
}

$GatewayLog = Join-Path $HermesHome "logs\gateway.log"
$ErrorLog = Join-Path $HermesHome "logs\errors.log"
$AgentLog = Join-Path $HermesHome "logs\agent.log"

# ─── 安装/卸载开机自启 ─────────────────────────────────────

if ($InstallStartup) {
    $shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) "HermesFeishuWatchdog.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-NoProfile -WindowStyle Hidden -File `"$PSCommandPath`""
    $shortcut.Description = "Hermes 飞书连接守护"
    $shortcut.Save()
    Write-Output "✅ 已安装开机自启: $shortcutPath"
    return
}

if ($Uninstall) {
    $shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) "HermesFeishuWatchdog.lnk"
    if (Test-Path $shortcutPath) { Remove-Item $shortcutPath -Force; Write-Output "✅ 已移除开机自启" }
    else { Write-Output "ℹ️ 未安装开机自启" }
    return
}

# ─── 核心逻辑 ────────────────────────────────────────────────

Write-Output "================================================"
Write-Output " Hermes 飞书连接看门狗"
Write-Output " 检查间隔: ${CheckInterval}s"
Write-Output " Hermes Home: $HermesHome"
Write-Output " Runtime: $RuntimePath"
Write-Output " 日志: $GatewayLog"
Write-Output "================================================"

function Test-GatewayRunning {
    # 方法1：检查进程
    $processRunning = (Get-Process -Name "hermes-agent-cn-runtime-win32-x64" -ErrorAction SilentlyContinue).Count -gt 0
    
    # 方法2：检查 gateway 日志是否在持续更新
    $logFresh = $false
    if (Test-Path $GatewayLog) {
        $lastWrite = (Get-Item $GatewayLog).LastWriteTime
        $logFresh = ((Get-Date) - $lastWrite).TotalMinutes -lt 10
    }
    
    # 方法3：检查 Feishu 端口（WebSocket 不需要固定端口，但 gateway 启动后有健康检查）
    $feishuConnected = $false
    if (Test-Path $GatewayLog) {
        $recentLog = Get-Content $GatewayLog -Tail 20 -ErrorAction SilentlyContinue
        $feishuConnected = ($recentLog -match "connected to wss://msg-frontier.feishu.cn").Count -gt 0
        # 如果日志太旧，连接可能已经断了
        if ($logFresh -and -not $feishuConnected) {
            # 检查是否有历史连接记录
            $everConnected = (Get-Content $GatewayLog -ErrorAction SilentlyContinue | Select-String "connected to wss://msg-frontier.feishu.cn").Count -gt 0
            if ($everConnected) {
                # 曾经连上过但日志太久没更新，可能进程还活着但连接断了
                $feishuConnected = $logFresh  # 如果日志更新说明进程在运行
            }
        }
    }

    # 方法4：检查 agent.log 是否有最近的 Feishu 消息处理记录
    $recentFeishuActivity = $false
    if (Test-Path $AgentLog) {
        $recentAgent = Get-Content $AgentLog -Tail 30 -ErrorAction SilentlyContinue
        $recentFeishuActivity = ($recentAgent -match "feishu.*Received").Count -gt 0
    }

    return @{
        ProcessRunning = $processRunning
        LogFresh = $logFresh
        FeishuConnected = $feishuConnected
        FeishuActivity = $recentFeishuActivity
        AllOk = $processRunning -and ($feishuConnected -or $logFresh)
    }
}

function Restart-Gateway {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] ⚠ 检测到飞书断连，正在恢复..."
    
    # 先尝试优雅关闭旧进程
    Get-Process -Name "hermes-agent-cn-runtime-win32-x64" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Output "  停止旧进程 PID=$($_.Id)"
        $_.CloseMainWindow()
        Start-Sleep -Seconds 2
        if (-not $_.HasExited) { $_.Kill() }
    }
    
    Start-Sleep -Seconds 3
    
    # 启动 Gateway
    if (Test-Path $RuntimePath) {
        Write-Output "  启动 Gateway: $RuntimePath"
        Start-Process -FilePath $RuntimePath -ArgumentList "gateway","run" -WindowStyle Hidden
        Start-Sleep -Seconds 10
        
        # 验证是否启动成功
        $status = Test-GatewayRunning
        if ($status.AllOk) {
            Write-Output "  ✅ Gateway 启动成功"
            # 记录恢复日志
            $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 看门狗自动恢复: Gateway 重启成功"
            $logEntry | Out-File -FilePath (Join-Path $HermesHome "logs\watchdog.log") -Append
        } else {
            Write-Output "  ❌ Gateway 启动可能失败，状态: $($status | ConvertTo-Json -Compress)"
        }
    } else {
        Write-Output "  ❌ 找不到 Runtime: $RuntimePath"
    }
}

# ─── 主循环 ──────────────────────────────────────────────────

$restartCount = 0
$lastRestartTime = Get-Date

while ($true) {
    $status = Test-GatewayRunning
    
    # 记录当前状态（每小时一次）
    if (((Get-Date).Minute -eq 0 -and (Get-Date).Second -lt 30)) {
        $logEntry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 状态: 进程=$($status.ProcessRunning) 日志=$($status.LogFresh) 飞书=$($status.FeishuConnected) 活动=$($status.FeishuActivity)"
        $logEntry | Out-File -FilePath (Join-Path $HermesHome "logs\watchdog.log") -Append
    }
    
    if (-not $status.AllOk) {
        $now = Get-Date
        # 防止频繁重启（至少间隔 5 分钟）
        if (($now - $lastRestartTime).TotalMinutes -ge 5) {
            $restartCount++
            Restart-Gateway
            $lastRestartTime = $now
            
            if ($restartCount -ge 5) {
                Write-Output "[$(Get-Date -Format 'HH:mm:ss')] ❌ 已尝试重启 $restartCount 次，请人工检查"
            }
        } else {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] ⚠ 上次重启不足5分钟，跳过"
        }
    }
    
    Start-Sleep -Seconds $CheckInterval
}
