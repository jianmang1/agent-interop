# 跨机器人互通方案 — 完整实现记录

## 参与者

| 角色 | 设备 | 网络 | 身份 |
|------|------|------|------|
| **工位电脑** | Windows, Hermes Agent 桌面版 | `192.168.1.103` | GitHub: jianmang1 |
| **笔记本** | Windows, Hermes Agent | `192.168.3.5` | GitHub: jianmang1 |

## 问题描述

两台计算机在不同子网（`192.168.1.x` vs `192.168.3.x`），无法直接 TCP 通信，需要跨设备传输文件（截图、任务请求、结果等）。

## 探索过的方案

### ❌ 方案1：飞书 API 轮询
- 需要飞书应用权限 `im:message.group_msg`
- 权限需要在飞书开发者后台添加、发布新版本、管理员审批
- 最终未走通此路线

### ❌ 方案2：Webhook 直连（不同子网不通）
- 工位电脑配置 Hermes Webhook（端口 8644）
- 笔记本也配置 Webhook（端口 8644）
- 但 `192.168.1.x` 和 `192.168.3.x` 在不同子网，TCP 连接超时
- 工位电脑 Webhook: `http://192.168.1.103:8644/webhooks/notebook-bridge`
- 签名方式: HMAC-SHA256 V2（`X-Webhook-Signature-V2` + `X-Webhook-Timestamp`）

### ❌ 方案3：飞书群聊 @对方
- 同一个飞书群，一方发消息另一方通过飞书客户端查看
- 问题：飞书不将机器人之间的 @消息转发给目标机器人
- 单向手动下载可用，但无法实现自动化互通

### ✅ 方案4：GitHub 仓库队列（最终方案）
- 利用两台机器都能访问互联网
- 使用 GitHub 仓库作为异步消息队列

## 最终方案：GitHub 仓库队列

### 仓库信息

- **URL**: https://github.com/jianmang1/agent-interop
- **笔记本本地**: `D:\agent互通\`
- **工位电脑本地**: `E:\agent互通\`

### 目录结构

```
agent-interop/
├── requests/                          # 请求队列
│   ├── README.md
│   ├── request-{ts}-{rand}.json       # 请求文件
│   └── processed_request-*            # 已处理请求
├── results/                           # 结果队列
│   ├── README.md
│   ├── result-{ts}-{rand}.json        # 结果文件
│   └── processed_result-*             # 已处理结果
├── docs/
│   └── cross-bot-interop-skill.md     # 工位电脑的 skill 文档
├── poll-notebook.ps1                  # 笔记本端轮询脚本
├── site_r/                            # GEE 遥感物候分析代码
├── 互通实现.md                          # 笔记本侧实现文档
└── README.md
```

### 通信协议

#### 请求格式（笔记本 → 工位电脑）

`requests/request-{timestamp}-{random4}.json`:

```json
{
  "type": "screenshot",
  "msg": "请截一张桌面截图",
  "timestamp": "2026-07-15 11:52:44",
  "reply_to": "results/result-{timestamp}-{random4}.json"
}
```

#### 结果格式（工位电脑 → 笔记本）

`results/result-{timestamp}-{random4}.json`:

```json
{
  "type": "screenshot",
  "status": "completed",
  "result_file": "desktop_screenshot.png",
  "timestamp": "2026-07-15 11:52:44",
  "description": "工位电脑桌面截图"
}
```

### 工作流程

```
笔记本                             工位电脑
  │                                    │
  ├─ 写 requests/request-xxx.json      │
  ├─ git add/commit/push ─────────────→│
  │                                    ├─ 轮询发现新请求
  │                                    ├─ 执行任务（截图等）
  │                                    ├─ 写 results/result-xxx.json
  │                                    ├─ git add/commit/push
  ├─ 轮询发现新结果 ←─────────────────┤
  ├─ 读取结果文件                      │
  ├─ 标记 processed_ ────────────────→│
  │                                    │
  ▼                                    ▼
 完成闭环                          完成闭环
```

### 轮询方式

**笔记本端**: `D:\agent互通\poll-notebook.ps1`
- 监听 `results/` 目录
- 10 秒轮询间隔
- 处理后将文件重命名为 `processed_` 前缀
- 通过 `Start-Process` 后台启动

**工位电脑端**: `poll-github-queue.ps1`
- 通过 GitHub REST API 轮询 `requests/` 目录
- 本地维护 `.processed_tracker.json` 避免重复处理
- 发现新请求 → 下载 → 处理 → 写结果

### 认证方式

- **Token 类型**: GitHub Classic PAT（`ghp_` 开头）
- **权限范围**: `repo`（完整私有仓库控制）
- **存放位置**: `~/.hermes/.env` 中 `GITHUB_TOKEN` 变量
- **教训**: Fine-grained PAT 权限分项细但配置复杂；Classic PAT 勾上 `repo` 一步到位更省事

## 经验教训

1. **飞书平台限制**: 飞书不会将机器人之间的 @消息转发给目标机器人。这是平台设计，不是配置问题
2. **Fine-grained PAT vs Classic PAT**: Fine-grained PAT 权限分项细但配置复杂，Classic PAT 勾上 repo 一步到位
3. **Webhook HMAC 签名**: Hermes webhook 使用 HMAC-SHA256 V2，需要 `X-Webhook-Signature-V2` + `X-Webhook-Timestamp` 头，签名字符串格式为 `{timestamp}.{json_body}`
4. **GitHub API 限制**: 用 API 逐文件上传大量小文件效率低；批量提交用 git tree 方式更高效
5. **跨子网通信**: 最简单方案是连同一个 WiFi；如果不行就用互联网可访问的中介（如 GitHub）
6. **网络不稳定**: 笔记本的 `git push` HTTPS 偶尔被重置，但 GitHub REST API 可正常使用。API 上传是可靠后备方案

## 测试验证

2026-07-15 成功完成首次端到端测试：

1. ✅ 笔记本 → `requests/` → GitHub → 工位电脑 pull
2. ✅ 工位电脑截图 → `results/` + 图片 → GitHub → 笔记本 pull
3. ✅ 笔记本确认 + 标记 `processed_` → GitHub → 工位电脑可见

## Hermes Skill

本协议已保存为 Hermes skill:

| 端 | Skill 名 | 位置 |
|----|----------|------|
| 笔记本 | `github-queue-interop` | Hermes skills 目录 |
| 工位电脑 | `cross-bot-interop` | GitHub 仓库 `docs/` 目录 |

在 Hermes 会话中加载:
```
/skill github-queue-interop
```


---

## 经验教训：飞书连接掉线

### 症状
* 飞书 gateway 突然停止响应
* 群消息无法发送或接收
* 连接后突然断线无重连

### 可能原因
| 原因 | 说明 |
|------|------|
| 端口冲突 | dashboard 端口被占用(9120-9140)导致异常 |
| 网络波动 | WebSocket 长连接因网络中断 |
| 进程崩溃 | Runtime 意外退出，桌面未自动重启 |

### 解决方案：feishu-watchdog.ps1
仓库 scripts/ 目录下的守护脚本：
1. 每15秒检查 Hermes 进程状态
2. 通过 gateway_state.json 判断飞书连接
3. 检测断连时自动重启网关
4. 最多连续重启5次防死循环
5. 重启冷却30秒

### 推荐使用
* 开机自启：放入 shell:startup 文件夹
* 计划任务（更稳定）：系统启动时运行 powershell -NoProfile -File scripts/feishu-watchdog.ps1
