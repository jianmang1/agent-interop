# feishu-watchdog.ps1 - 椋炰功缃戝叧瀹堟姢鑴氭湰
# 鍔熻兘锛氱洃鎺ч涔﹁繛鎺ョ姸鎬侊紝鏂紑鏃惰嚜鍔ㄩ噸鍚?# 鐢ㄦ硶锛歱owershell -NoProfile -File feishu-watchdog.ps1
# 鎺ㄨ崘鏀惧湪寮€鏈鸿嚜鍚垨璁″垝浠诲姟涓?
param(
    [int]$CheckInterval = 15,        # 妫€鏌ラ棿闅旓紙绉掞級
    [string]$LogPath = "",           # 鏃ュ織璺緞锛岄粯璁?$HERMES_HOME/logs/watchdog.log
    [int]$MaxRestartAttempts = 5,    # 鏈€澶ц繛缁噸鍚鏁帮紙瓒呰繃鍒欓€€鍑猴級
    [int]$RestartCooldown = 30       # 閲嶅惎鍐峰嵈锛堢锛?)

# ===== 閰嶇疆鍖哄煙 =====
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) {
    # 灏濊瘯甯歌璺緞
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
if (-not $HermesHome) { Write-Host "鉂?鎵句笉鍒?HERMES_HOME"; exit 1 }

$GatewayLog = "$HermesHome\logs\gateway.log"
$GatewayState = "$HermesHome\..\..\data\gateway-runtime\gateway_state.json"

# 灏濊瘯瑙ｆ瀽 gateway_state.json 鐨勫疄闄呰矾寰?$statePaths = @(
    $GatewayState,
    "$HermesHome\gateway_state.json",
    "$env:HERMES_APP_DIR\data\gateway-runtime\gateway_state.json",
    "F:\Hermes Agent CN Desktop\data\gateway-runtime\gateway_state.json"
)

if (-not $LogPath) { $LogPath = "$HermesHome\logs\watchdog.log" }

# ===== 宸ュ叿鍑芥暟 =====
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
    # 鏂规硶1锛氭鏌ョ綉鍏崇姸鎬佹枃浠?    foreach ($sp in $statePaths) {
        if (Test-Path $sp) {
            try {
                $state = Get-Content $sp -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
                if ($state.platforms.feishu.state -eq "connected") { return $true }
            } catch {}
        }
    }
    # 鏂规硶2锛氭鏌ョ綉鍏虫棩蹇楁渶鍚庡嚑琛屾槸鍚︽湁杩炴帴淇℃伅
    if (Test-Path $GatewayLog) {
        $lastLines = Get-Content $GatewayLog -Tail 10 -ErrorAction SilentlyContinue
        $lastFeishuLine = $lastLines | Select-String -Pattern "feishu connected|feishu.*Connected" -SimpleMatch | Select-Object -Last 1
        $lastErrorLine = $lastLines | Select-String -Pattern "disconnect|error|fail|close" -SimpleMatch | Select-Object -Last 1
        if ($lastFeishuLine -and $lastErrorLine) {
            # 姣旇緝鏃堕棿锛氬鏋滆繛鎺ユ秷鎭湪閿欒娑堟伅涔嬪悗璇存槑宸查噸杩?            return $true
        }
        if ($lastFeishuLine) { return $true }
    }
    return $false
}

function Restart-Gateway {
    Write-Log "馃攧 姝ｅ湪閲嶅惎椋炰功缃戝叧..."
    $procs = Get-HermesProcesses
    
    # 鍏堟潃 runtime 杩涚▼锛坓ateway锛夛紝杩欎細瑙﹀彂妗岄潰搴旂敤鑷姩閲嶅惎瀹?    foreach ($p in $procs.runtime) {
        try {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            Write-Log "  鈿?宸茬粓姝?runtime PID=$($p.Id)"
        } catch {}
    }
    
    Start-Sleep -Seconds 3
    
    # 濡傛灉妗岄潰搴旂敤涔熶笉鍦ㄤ簡锛屽惎鍔ㄥ畠
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
                    Write-Log "  馃殌 宸插惎鍔ㄦ闈㈠簲鐢? $dp"
                    break
                } catch {}
            }
        }
    }
    
    Start-Sleep -Seconds 5
    
    # 鏈€缁堟鏌?    $procs3 = Get-HermesProcesses
    if ($procs3.desktop -or $procs3.runtime) {
        Write-Log "  鉁?缃戝叧宸查噸鍚?
        return $true
    } else {
        Write-Log "  鉂?缃戝叧鍚姩澶辫触"
        return $false
    }
}

# ===== 涓诲惊鐜?=====
Write-Log "========================================"
Write-Log "馃 椋炰功缃戝叧瀹堟姢鑴氭湰鍚姩"
Write-Log "馃搨 HERMES_HOME: $HermesHome"
Write-Log "鈴? 妫€鏌ラ棿闅? ${CheckInterval}s"
Write-Log "馃攧 鏈€澶ч噸鍚? ${MaxRestartAttempts}娆?
Write-Log "========================================"

$restartCount = 0
$lastRestartTime = 0

while ($true) {
    $now = Get-Date
    $proc = Get-HermesProcesses
    $feishuOk = Test-FeishuConnected
    
    # 鐘舵€佹憳瑕?    $hasDesktop = [bool]$proc.desktop
    $hasRuntime = $proc.runtime.Count -gt 0
    
    if (-not $hasDesktop -and -not $hasRuntime) {
        Write-Log "鈿狅笍  Hermes 杩涚▼鍏ㄩ儴娑堝け锛屽噯澶囬噸鍚?
        if ($restartCount -lt $MaxRestartAttempts) {
            $ok = Restart-Gateway
            if ($ok) { $restartCount = 0 } else { $restartCount++ }
            $lastRestartTime = (Get-Date).UnixTimeSeconds
        } else {
            Write-Log "鉂?杩炵画閲嶅惎 $MaxRestartAttempts 娆″け璐ワ紝閫€鍑哄畧鎶?
            exit 1
        }
    } elseif ($hasRuntime -and -not $feishuOk) {
        # 鏈夎繘绋嬩絾椋炰功鏂繛
        $timeSinceRestart = $now.UnixTimeSeconds - $lastRestartTime
        if ($timeSinceRestart -gt $RestartCooldown) {
            Write-Log "鈿狅笍  椋炰功杩炴帴寮傚父锛堟湁杩涚▼浣嗘湭杩炴帴锛夛紝鍑嗗閲嶅惎缃戝叧"
            if ($restartCount -lt $MaxRestartAttempts) {
                $ok = Restart-Gateway
                if ($ok) { $restartCount = 0 } else { $restartCount++ }
                $lastRestartTime = (Get-Date).UnixTimeSeconds
            } else {
                Write-Log "鉂?杩炵画閲嶅惎 $MaxRestartAttempts 娆″け璐ワ紝閫€鍑哄畧鎶?
                exit 1
            }
        }
    } elseif ($hasRuntime -and $feishuOk) {
        # 涓€鍒囨甯革紝閲嶇疆璁℃暟
        if ($restartCount -ne 0) {
            $restartCount = 0
            Write-Log "鉁?杩炴帴宸叉仮澶嶏紝閲嶅惎璁℃暟褰掗浂"
        }
    }
    
    Start-Sleep -Seconds $CheckInterval
}
