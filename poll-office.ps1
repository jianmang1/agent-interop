# poll-office.ps1 - 工位电脑端轮询脚本
# 监听 requests/ 目录，笔记本发来的请求在这里出现
# 启动方式：powershell -NoProfile -File E:\agent互通\poll-office.ps1

param(
    [string]$RepoPath = "E:\agent互通",
    [int]$PollInterval = 10
)

$hermesHome = $env:HERMES_HOME
if (-not $hermesHome) { $hermesHome = 'F:\Hermes Agent CN Desktop\data\hermes-home' }

# 读取 GitHub Token
$token = $env:GITHUB_TOKEN
if (-not $token) {
    $envFile = Join-Path $hermesHome ".env"
    if (Test-Path $envFile) {
        foreach ($line in (Get-Content $envFile -ErrorAction SilentlyContinue)) {
            if ($line -match "^GITHUB_TOKEN=(.+)" -or $line -match "^GITHUB_TOKEN=(.+)") {
                $token = $matches[1]; break
            }
        }
    }
}

if (-not $token) {
    Write-Host "❌ 找不到 GITHUB_TOKEN，请在 .env 中设置" -ForegroundColor Red
    exit 1
}

# 请求类型处理映射
$requestHandlers = @{
    "screenshot"  = { param($req) Take-Screenshot $req }
    "command"     = { param($req) Run-Command $req }
    "file"        = { param($req) Get-File $req }
    "status"      = { param($req) Get-Status $req }
}

function Take-Screenshot {
    param($req)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $screenshotPath = Join-Path $RepoPath "desktop_$timestamp.png"
    
    Add-Type -AssemblyName System.Windows.Forms
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bitmap.Save($screenshotPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    return @{
        type = "screenshot"
        status = "completed"
        result_file = "desktop_$timestamp.png"
        description = "工位电脑桌面截图"
    }
}

function Run-Command {
    param($req)
    $cmd = $req.command
    $output = Invoke-Expression $cmd 2>&1 | Out-String
    return @{
        type = "command"
        status = "completed"
        output = $output
        description = "命令执行结果"
    }
}

function Get-File {
    param($req)
    $filePath = $req.file_path
    if (Test-Path $filePath) {
        return @{
            type = "file"
            status = "completed"
            file = $filePath
            description = "文件已准备"
        }
    } else {
        return @{
            type = "file"
            status = "failed"
            error = "文件不存在: $filePath"
        }
    }
}

function Get-Status {
    param($req)
    return @{
        type = "status"
        status = "completed"
        hostname = $env:COMPUTERNAME
        time = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -First 1).IPAddress
        hermes_process = [bool](Get-Process -Name "hermes-agent-cn-*" -ErrorAction SilentlyContinue)
    }
}

Write-Output "========================================"
Write-Output " 工位电脑轮询脚本启动"
Write-Output " 监听: $RepoPath\requests\"
Write-Output " git pull 间隔: ${PollInterval}s"
Write-Output " 时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "========================================"

# 本地处理追踪文件，避免重复处理
$trackerFile = Join-Path $RepoPath ".processed_tracker.json"
$processedIds = @{}
if (Test-Path $trackerFile) {
    try { $processedIds = Get-Content $trackerFile -Raw | ConvertFrom-Json -AsHashtable } catch {}
}

while ($true) {
    try {
        # 方法1：通过 git pull 拉取最新
        Push-Location $RepoPath
        $pullResult = git pull 2>&1 | Out-String
        Pop-Location

        $requestsDir = Join-Path $RepoPath "requests"
        if (Test-Path $requestsDir) {
            $newRequests = Get-ChildItem -Path $requestsDir -Filter "request-*.json" | Where-Object { 
                $_.Name -notlike "processed_request-*" -and -not $processedIds.ContainsKey($_.Name)
            }
            
            foreach ($reqFile in $newRequests) {
                try {
                    $request = Get-Content $reqFile.FullName -Raw | ConvertFrom-Json
                    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 收到新请求: $($reqFile.Name)"
                    Write-Output "  类型: $($request.type) | 消息: $($request.msg)"
                    
                    # 处理请求
                    $handler = $requestHandlers[$request.type]
                    if ($handler) {
                        $result = & $handler $request
                    } else {
                        $result = @{
                            type = $request.type
                            status = "failed"
                            error = "不支持的请求类型: $($request.type)"
                        }
                    }
                    
                    # 处理 reply_to
                    if ($request.reply_to) {
                        $resultPath = Join-Path $RepoPath $request.reply_to
                    } else {
                        $timestamp = (Get-Date -Format 'yyyyMMddHHmmss')
                        $random = -join ((65..90) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
                        $resultPath = Join-Path $RepoPath "results\result-$timestamp-$random.json"
                    }
                    
                    # 写结果文件
                    $result | ConvertTo-Json | Set-Content $resultPath -Encoding UTF8
                    Write-Output "  结果已写入: $resultPath"
                    
                    # 标记请求为已处理
                    $processedName = "processed_$($reqFile.Name)"
                    Rename-Item -Path $reqFile.FullName -NewName $processedName -Force
                    $processedIds[$reqFile.Name] = $true
                    
                    # git add / commit / push
                    Push-Location $RepoPath
                    git add -A 2>&1 | Out-String
                    git commit -m "工位电脑: 处理 $($reqFile.Name)" 2>&1 | Out-String
                    git push 2>&1 | Out-String
                    Pop-Location
                    
                    Write-Output "  ✅ 已提交并推送结果"
                    
                } catch {
                    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 处理失败: $($reqFile.Name) - $_"
                }
            }
        }
        
        # 保存追踪文件
        $processedIds | ConvertTo-Json | Set-Content $trackerFile -Encoding UTF8
        
    } catch {
        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 轮询异常: $_"
    }
    
    Start-Sleep -Seconds $PollInterval
}
