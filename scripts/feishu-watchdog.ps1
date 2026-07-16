# feishu-watchdog.ps1 - 飞书网关守护脚本（工位电脑版）
# 功能：监控飞书连接状态，断开时自动重启
# 用法：powershell -NoProfile -File feishu-watchdog.ps1
# 推荐放在开机自启或计划任务中

param(
    [int]$CheckInterval = 15,        # 检查间隔（秒）
    [string]$LogPath = "",           # 日志路径，默认 $HERMES_HOME/logs/watchdog.log
    [int]$MaxRestartAttempts = 5,    # 最大连续重启次数（超过则退出）
    [int]$RestartCooldown = 30       # 重启冷却（秒）
)

# ===== 配置区域 =====
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) {
    # 尝试常见路径
    $possiblePaths = @(
        "F:\Hermes Agent CN Desktop\data\hermes-home",
        "C:\Users\Administrator\.hermes",
        "$env:USERPROFILE\.hermes"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path "$p\config.yaml") {
            $HermesHome = $p; break
        }
    }
}
if (-not $HermesHome) { Write-Host "❌ 找不到 HERMES_HOME"; exit 1 }

$GatewayLog = "$HermesHome\logs\gateway.log"
$GatewayState = "$HermesHome\..\..\data\gateway-runtime\gateway_state.json"

# 尝试解析 gateway_state.json 的实际路径
$statePaths = @(
    $GatewayState,
    "$HermesHome\gateway_state.json",
    "$env:HERMES_APP_DIR\data\gateway-runtime\gateway_state.json",
    "F:\Hermes Agent CN Desktop\data\gateway-runtime\gateway_state.json"
)

if (-not $LogPath) { $LogPath = "$HermesHome\logs\watchdog.log" }

# ===== 工具函数 =====
function Write-Log {
    param([string]$Msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Msg"
    Write-Host $line
    try {
        Add-Content -Path $LogPath -Value $line -ErrorAction SilentlyContinue
    } catch {}
}

function Get-HermesProcesses {
    $result = @{desktop=$null; runtime=@()}
    $result.desktop = Get-Process -Name "hermes-agent-cn-desktop" -ErrorAction SilentlyContinue | Select-Object -First 1
    $result.runtime = Get-Process -Name "hermes-agent-cn-runtime-win32-x64" -ErrorAction SilentlyContinue
    return $result
}

function Test-FeishuConnected {
    # 方法1：检查网关状态文件
    foreach ($sp in $statePaths) {
        if (Test-Path $sp) {
            try {
                $state = Get-Content $sp -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
                if ($state.platforms.feishu.state -eq "connected") { return $true }
            } catch {}
        }
    }
    # 方法2：检查网关日志最后几行是否有连接信息
    if (Test-Path $GatewayLog) {
        $lastLines = Get-Content $GatewayLog -Tail 10 -ErrorAction SilentlyContinue
        $lastFeishuLine = $lastLines | Select-String -Pattern "feishu connected|feishu.*Connected" -SimpleMatch | Select-Object -Last 1
        $lastErrorLine = $lastLines | Select-String -Pattern "disconnect|error|fail|close" -SimpleMatch | Select-Object -Last 1
        if ($lastFeishuLine -and $lastErrorLine) {
            # 比较时间：如果连接消息在错误消息之后说明已重连
            return $true
        }
        if ($lastFeishuLine) { return $true }
    }
    return $false
}

function Restart-Gateway {
    Write-Log "🔄 正在重启飞书网关..."
    $procs = Get-HermesProcesses
    
    # 先杀 runtime 进程（gateway），这会触发桌面应用自动重启它
    foreach ($p in $procs.runtime) {
        try {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Write-Log "  ✅ 已终止 runtime PID=$($p.Id)"
        } catch {}
    }
    
    Start-Sleep -Seconds 3
    
    # 如果桌面应用也不在了，启动它
    $desktopPath = "F:\Hermes Agent CN Desktop\hermes-agent-cn-desktop.exe"
    $altPaths = @(
        $desktopPath,
        "$env:LOCALAPPDATA\Programs\hermes-agent\hermes-agent-cn-desktop.exe",
        "C:\Program Files\hermes-agent\hermes-agent-cn-desktop.exe"
    )
    
    $procs2 = Get-HermesProcesses
    if (-not $procs2.desktop) {
        foreach ($dp in $altPaths) {
            if (Test-Path $dp) {
                try {
                    Start-Process -FilePath $dp -WindowStyle Normal
                    Write-Log "  🚀 已启动桌面应用: $dp"
                    break
                } catch {}
            }
        }
    }
    
    Start-Sleep -Seconds 5
    
    # 最终检查
    $procs3 = Get-HermesProcesses
    if ($procs3.desktop -or $procs3.runtime) {
        Write-Log "  ✅ 网关已重启"
        return $true
    } else {
        Write-Log "  ❌ 网关启动失败"
        return $false
    }
}

# ===== 主循环 =====
Write-Log "========================================"
Write-Log "🛻 飞书网关守护脚本启动"
Write-Log "📨 HERMES_HOME: $HermesHome"
Write-Log "⏱ 检查间隔: ${CheckInterval}s"
Write-Log "🔄 最大重启: ${MaxRestartAttempts}次"
Write-Log "========================================"

$restartCount = 0
$lastRestartTime = 0

while ($true) {
    $now = Get-Date
    $proc = Get-HermesProcesses
    $feishuOk = Test-FeishuConnected
    
    # 状态摘要
    $hasDesktop = [bool]$proc.desktop
    $hasRuntime = $proc.runtime.Count -gt 0
    
    if (-not $hasDesktop -and -not $hasRuntime) {
        Write-Log "⚠️  Hermes 进程全部消失，准备重启"
        if ($restartCount -lt $MaxRestartAttempts) {
            $ok = Restart-Gateway
            if ($ok) { $restartCount = 0 } else { $restartCount++ }
            $lastRestartTime = (Get-Date).UnixTimeSeconds
        } else {
            Write-Log "❌ 连续重启 $MaxRestartAttempts 次失败，退出守护"
            exit 1
        }
    } elseif ($hasRuntime -and -not $feishuOk) {
        # 有进程但飞书断连
        $timeSinceRestart = $now.UnixTimeSeconds - $lastRestartTime
        if ($timeSinceRestart -gt $RestartCooldown) {
            Write-Log "⚠️  飞书连接异常（有进程但未连接），准备重启网关"
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
        # 一切正常，重置计数
        if ($restartCount -ne 0) {
            $restartCount = 0
            Write-Log "✅ 连接已恢复，重启计数归零"
        }
    }
    
    Start-Sleep -Seconds $CheckInterval
}
