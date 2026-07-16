# feishu-watchdog.ps1 — 飞书连接看门狗（双端合并版）
# 笔记本 + 工位电脑 经验整合
# 功能：监控飞书连接状态，断开时自动重启
# 用法：powershell -NoProfile -File feishu-watchdog.ps1
# 推荐：放入开机自启或计划任务

param(
    [int]$CheckInterval = 15,        # 检查间隔（秒）
    [string]$LogPath = "",           # 日志路径
    [int]$MaxRestartAttempts = 5,    # 最大连续重启次数
    [int]$RestartCooldown = 30       # 重启冷却（秒）
)

# ===== 配置区域 =====
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) {
    $possiblePaths = @(
        "D:\Hermes Agent CN Desktop\data\hermes-home",
        "C:\Users\10531\.hermes",
        "$env:USERPROFILE\.hermes"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path "$p\config.yaml") { $HermesHome = $p; break }
    }
}
if (-not $HermesHome) { Write-Host "❌ 找不到 HERMES_HOME"; exit 1 }

$GatewayLog = "$HermesHome\logs\gateway.log"
$AgentLog = "$HermesHome\logs\agent.log"
$WatchdogLog = "$HermesHome\logs\watchdog.log"

# gateway_state.json 可能的位置
$statePaths = @(
    "$HermesHome\..\..\data\gateway-runtime\gateway_state.json",
    "$HermesHome\gateway_state.json",
    "$env:HERMES_APP_DIR\data\gateway-runtime\gateway_state.json"
)

if (-not $LogPath) { $LogPath = $WatchdogLog }

# ===== 工具函数 =====
function Write-Log {
    param([string]$Msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Msg"
    Write-Host $line
    try { Add-Content -Path $LogPath -Value $line -ErrorAction SilentlyContinue } catch {}
}

function Get-HermesProcesses {
    $result = @{desktop=$null; runtime=@()}
    $result.desktop = Get-Process -Name "hermes-agent-cn-desktop" -ErrorAction SilentlyContinue | Select-Object -First 1
    $result.runtime = Get-Process -Name "hermes-agent-cn-runtime-win32-x64" -ErrorAction SilentlyContinue
    return $result
}

function Test-FeishuConnected {
    # 方法1：检查 gateway_state.json
    foreach ($sp in $statePaths) {
        if (Test-Path $sp) {
            try {
                $state = Get-Content $sp -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
                if ($state.platforms.feishu.state -eq "connected") { return $true }
            } catch {}
        }
    }
    # 方法2：检查 gateway 日志是否有最近连接记录
    if (Test-Path $GatewayLog) {
        $lastLines = Get-Content $GatewayLog -Tail 20 -ErrorAction SilentlyContinue
        # 查找最近的成功连接记录
        $connected = $lastLines | Select-String -Pattern "connected to wss://msg-frontier.feishu.cn"
        if ($connected) {
            # 检查连接后是否有断开
            $disconnected = $lastLines | Select-String -Pattern "disconnect|connection.*close|reconnect.*fail"
            if (-not $disconnected) { return $true }
            # 连接在断开的后面？说明已重连成功
            $connTime = ($connected | Select-Object -Last 1).Line
            $discTime = ($disconnected | Select-Object -Last 1).Line
            if (-not $discTime) { return $true }
        }
        # 方法3：检查 agent.log 是否有最近的飞书消息活动
        if (Test-Path $AgentLog) {
            $recent = Get-Content $AgentLog -Tail 10 -ErrorAction SilentlyContinue
            if ($recent -match "feishu.*Received|feishu.*Sending") { return $true }
        }
    }
    return $false
}

function Restart-Gateway {
    Write-Log "⚠ 正在重启飞书网关..."
    $procs = Get-HermesProcesses
    
    # 先杀 runtime 进程（gateway），这会触发桌面应用自动重启
    foreach ($p in $procs.runtime) {
        try {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Write-Log "  ✓ 已终止 runtime PID=$($p.Id)"
        } catch {}
    }
    
    Start-Sleep -Seconds 3
    
    # 如果桌面应用也不在了，启动它
    $procs = Get-HermesProcesses
    if (-not $procs.desktop) {
        $desktopPaths = @(
            "D:\Hermes Agent CN Desktop\data\versions\0.18.2-cn.2\hermes-agent-cn-desktop.exe",
            "$env:LOCALAPPDATA\Programs\hermes-agent\hermes-agent-cn-desktop.exe",
            "C:\Program Files\hermes-agent\hermes-agent-cn-desktop.exe"
        )
        foreach ($dp in $desktopPaths) {
            if (Test-Path $dp) {
                try {
                    Start-Process -FilePath $dp -WindowStyle Normal
                    Write-Log "  🚀 已启动桌面应用: $dp"
                    break
                } catch {}
            }
        }
    } else {
        # 桌面应用在运行但 gateway 不在，直接启动 gateway
        $runtimePaths = @(
            "D:\Hermes Agent CN Desktop\data\versions\0.18.2-cn.2\hermes-agent-cn-runtime-win32-x64.exe",
            "$PSScriptRoot\hermes-agent-cn-runtime-win32-x64.exe"
        )
        foreach ($rp in $runtimePaths) {
            if (Test-Path $rp) {
                try {
                    Start-Process -FilePath $rp -ArgumentList "gateway","run" -WindowStyle Hidden
                    Write-Log "  🚀 已启动 Gateway: $rp"
                    break
                } catch {}
            }
        }
    }
    
    Start-Sleep -Seconds 5
    
    # 最终检查
    $procs = Get-HermesProcesses
    if ($procs.desktop -or $procs.runtime) {
        Write-Log "  ✅ 网关已重启"
        return $true
    } else {
        Write-Log "  ❌ 网关启动失败"
        return $false
    }
}

# ===== 主循环 =====
Write-Log "============================================"
Write-Log " Hermes 飞书网关守护脚本（双端合并版）"
Write-Log " HERMES_HOME: $HermesHome"
Write-Log " 检查间隔: ${CheckInterval}s | 最大重启: ${MaxRestartAttempts}次"
Write-Log "============================================"

$restartCount = 0
$lastRestartTime = 0

while ($true) {
    $now = Get-Date
    $proc = Get-HermesProcesses
    $feishuOk = Test-FeishuConnected
    
    $hasDesktop = [bool]$proc.desktop
    $hasRuntime = $proc.runtime.Count -gt 0
    
    if (-not $hasDesktop -and -not $hasRuntime) {
        Write-Log "⛔ Hermes 进程全部消失，准备重启"
        if ($restartCount -lt $MaxRestartAttempts) {
            $ok = Restart-Gateway
            if ($ok) { $restartCount = 0 } else { $restartCount++ }
            $lastRestartTime = (Get-Date).UnixTimeSeconds
        } else {
            Write-Log "❌ 连续重启 $MaxRestartAttempts 次失败，退出守护"
            exit 1
        }
    } elseif ($hasRuntime -and -not $feishuOk) {
        $timeSinceRestart = $now.UnixTimeSeconds - $lastRestartTime
        if ($timeSinceRestart -gt $RestartCooldown) {
            Write-Log "⛔ 飞书连接异常（有进程但未连接），准备重启网关"
            if ($restartCount -lt $MaxRestartAttempts) {
                $ok = Restart-Gateway
                if ($ok) { $restartCount = 0 } else { $restartCount++ }
                $lastRestartTime = (Get-Date).UnixTimeSeconds
            } else {
                Write-Log "❌ 连续重启 $MaxRestartAttempts 次失败，退出守护"
                exit 1
            }
        }
    } elseif ($hasRuntime -and $feishuOk) {
        if ($restartCount -ne 0) {
            $restartCount = 0
            Write-Log "✅ 连接已恢复，重启计数归零"
        }
    }
    
    Start-Sleep -Seconds $CheckInterval
}
