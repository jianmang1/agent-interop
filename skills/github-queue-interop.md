---
name: github-queue-interop
description: "笔记本 ⇄ 工位电脑 GitHub 队列互通协议。通过 GitHub 仓库作为异步消息队列实现跨子网文件交换"
version: 1.0.0
author: jianmang1
platforms: [windows]
metadata:
  hermes:
    tags: [interop, github-queue, cross-device, file-transfer, async]
---

# GitHub 队列互通协议

## 概述

通过 GitHub 仓库作为异步消息队列，实现两台在不同子网的机器（笔记本 192.168.3.x、工位电脑 192.168.1.x）之间的文件交换和任务调度。

## 仓库

- **URL**: https://github.com/jianmang1/agent-interop
- **笔记本本地**: `D:\agent互通\`
- **工位电脑本地**: `E:\agent互通\`

## 目录结构

```
agent-interop/
├── requests/                     # 请求队列
│   ├── request-{ts}-{rand}.json  # 请求文件（发起方写）
│   └── processed_request-*      # 已处理请求
├── results/                      # 结果队列
│   ├── result-{ts}-{rand}.json   # 结果文件（处理方写）
│   └── processed_result-*       # 已处理结果
├── poll-notebook.ps1             # 笔记本端轮询脚本
├── poll-office.ps1               # 工位电脑端轮询脚本
├── docs/                         # 文档
├── scripts/                      # 守护脚本
└── site_r/                       # GEE 遥感分析代码
```

## 使用方式

### 发起请求

在 `requests/` 目录创建 JSON 文件：

```json
{
  "type": "screenshot",
  "msg": "请截一张桌面截图",
  "reply_to": "results/result-{timestamp}-{random4}.json",
  "timestamp": "2026-07-15 11:52:44"
}
```

支持的请求类型：
- `screenshot` — 截桌面并返回图片
- `command` — 在对方机器执行命令
- `file` — 获取指定文件
- `status` — 查询对方机器状态

处理结果会写入 `results/` 目录，对方通过轮询拉取。

### 启动轮询

**笔记本端：**
```powershell
Start-Process powershell -ArgumentList "-NoProfile -File D:\agent互通\poll-notebook.ps1"
```

**工位电脑端：**
```powershell
Start-Process powershell -ArgumentList "-NoProfile -File E:\agent互通\poll-office.ps1"
```

### 认证

GitHub Classic PAT（`ghp_` 开头），存于 `~/.hermes/.env` 中 `GITHUB_TOKEN` 变量。

## 注意事项

- git push 偶尔会 HTTPS 重置，GitHub REST API 是可靠后备方案
- 飞书账号不能在两台设备同时保持飞书网关连接，会互相踢
- 建议配合 `scripts/feishu-watchdog.ps1` 保持飞书连接稳定
