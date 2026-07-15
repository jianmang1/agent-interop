# agent-interop

笔记本 ⇄ 工位电脑 文件互通仓库

## 互通方式

通过 GitHub 仓库作为消息队列，实现两台不同子网机器的异步文件交换。

详见 [`互通实现.md`](互通实现.md)

## 目录结构

| 目录/文件 | 说明 |
|-----------|------|
| `requests/` | 请求队列（发请求方写文件到这里） |
| `results/` | 结果队列（处理方写结果到这里） |
| `poll-notebook.ps1` | 笔记本端轮询脚本 |
| `互通实现.md` | 完整实现文档 |
| `desktop_*.png` | 截图文件 |

## 快速使用

**笔记本：** `cd D:\agent互通 && git pull`

**工位电脑：** `cd E:\agent互通 && git pull`

### 发起请求

在 `requests/` 目录创建 JSON 文件：

```json
{
  "type": "screenshot",
  "msg": "请截桌面截图",
  "reply_to": "results/result-{timestamp}-{random}.json"
}
```

然后 `git add / commit / push`，对方轮询后会自动处理。

---

互通时间：2026-07-15
