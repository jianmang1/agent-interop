# poll-notebook.ps1 - 笔记本端轮询脚本
# 监听 results/ 目录，工位电脑的结果会在这里出现

$repoPath = "D:\agent互通"
$pollInterval = 10
$token = $env:GITHUB_TOKEN
if (-not $token) {
    $envContent = Get-Content "D:\Hermes Agent CN Desktop\data\hermes-home\.env" -ErrorAction SilentlyContinue
    foreach ($line in $envContent) {
        if ($line -match "^GITHUB_TOKEN=(.+)") { $token = $matches[1] }
    }
}

Write-Output "========================================"
Write-Output " 笔记本轮询脚本启动"
Write-Output " 监听: $repoPath\results\"
Write-Output " 间隔: ${pollInterval}s"
Write-Output " 时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "========================================"

while ($true) {
    $resultsDir = Join-Path $repoPath "results"
    if (Test-Path $resultsDir) {
        $newResults = Get-ChildItem -Path $resultsDir -Filter "result-*.json" | Where-Object { $_.Name -notlike "processed_*" }
        foreach ($result in $newResults) {
            try {
                $content = Get-Content $result.FullName -Raw | ConvertFrom-Json
                Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 收到新结果: $($result.Name)"
                Write-Output "  内容: $($content | ConvertTo-Json -Compress)"
                
                $processedName = "processed_$($result.Name)"
                Rename-Item -Path $result.FullName -NewName $processedName -Force
                Write-Output "  已标记 -> $processedName"
            } catch {
                Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 处理失败: $($result.Name) - $_"
            }
        }
    }
    Start-Sleep -Seconds $pollInterval
}
