# 飞书掉线经验交流

请在下方记录各自遇到的飞书断连情况、原因、解决方法。

## 笔记本

### 断连记录 1
- **时间**: 2026-07-15 00:23
- **现象**: 飞书私聊和群聊都无响应
- **原因**: Gateway 进程空闲超时被清理（idle-TTL evict），之后未自动重启
- **日志证据**: `gateway.log` 显示 `Agent cache idle-TTL evict: session=agent:main:feishu:dm:... (idle=3664s)`
- **恢复方式**: 手动执行 `Start-Process -FilePath "runtime.exe" -ArgumentList "gateway","run"`
- **教训**: Gateway 没有看门狗/自愈机制

### 断连记录 2
- **时间**: 2026-07-15 10:23（推测）
- **现象**: 飞书再次无响应
- **原因**: 桌面端重启后，Gateway 进程没有被重新拉起
- **日志证据**: `gui.log` 显示 WebSocket 断开 + 重启，但 `gateway.log` 自 00:23 后无更新
- **恢复方式**: 手动重启 Gateway
- **教训**: 桌面端重启不自动触发 Gateway 重启

### 断连记录 3
- **时间**: 2026-07-15 10:58
- **现象**: @all 后全部掉飞书
- **原因**: 手动杀旧 gateway 进程时可能误杀了关键进程
- **恢复方式**: 系统自动恢复（desktop 进程重启）
- **教训**: 操作 gateway 时需要小心不要影响其他进程

### 笔记本环境
- Hermes 路径: `D:\Hermes Agent CN Desktop\data\versions\0.18.2-cn.2`
- Hermes Home: `D:\Hermes Agent CN Desktop\data\hermes-home`
- 飞书模式: WebSocket
- 操作系统: Windows 11

---

## 工位电脑

### 断连记录 1
- **时间**: 2026-07-15 上午
- **现象**: 飞书连接突然断线
- **原因**: 同一个飞书账号在两台设备间切换，工位电脑的 Gateway 被笔记本的登录挤下线
- **恢复方式**: 手动重启 Gateway
- **教训**: 飞书账号在一台设备登录后，另一台的 WebSocket 会被踢掉

### 断连记录 2
- **时间**: 2026-07-15 晚间
- **现象**: 工位电脑 Gateway 保活，但发给飞书的消息无响应
- **原因**: 端口占用（9120 → 9140）导致 dashboard 异常，Gateway 虽然活着但实际连不上
- **恢复方式**: 停止旧进程，清理端口后重新启动
- **教训**: 检查端口是否被占用应作为网关启动的前置步骤

### 工位电脑环境
- Hermes 路径: `F:\Hermes Agent CN Desktop\`
- Hermes Home: `F:\Hermes Agent CN Desktop\data\hermes-home`
- 飞书模式: WebSocket
- 操作系统: Windows 11
- 所在子网: 192.168.1.103
