---
name: cross-bot-interop
description: 涓や釜椋炰功鏈哄櫒浜猴紙宸ヤ綅鐢佃剳 & 绗旇鏈級鍦ㄤ笉鍚屽瓙缃戜笅鐨勪簰閫氭柟妗堝畬鏁磋褰?platforms: [windows]
---

# 璺ㄦ満鍣ㄤ汉浜掗€氭柟妗?鈥?瀹屾暣瀹炵幇璁板綍

## 闂鎻忚堪

涓や釜椋炰功鏈哄櫒浜猴紙宸ヤ綅鐢佃剳 = Hermes Agent锛岀瑪璁版湰 = 鍙︿竴涓涔︽櫤鑳戒綋锛夐渶瑕佷簰鐩镐紶閫掓暟鎹紙鎴浘銆佷换鍔¤姹傘€佺粨鏋滅瓑锛夛紝浣嗛潰涓翠互涓嬮檺鍒讹細

| 闄愬埗 | 璇存槑 |
|------|------|
| 馃寪 **涓嶅悓瀛愮綉** | 宸ヤ綅鐢佃剳 `192.168.1.x`锛岀瑪璁版湰 `192.168.3.x`锛屾棤娉曠洿鎺ョ綉缁滈€氫俊 |
| 馃 **椋炰功涓嶈浆鍙戞満鍣ㄤ汉@娑堟伅** | 椋炰功骞冲彴涓嶄細鎶婃満鍣ㄤ汉A @鏈哄櫒浜築 鐨勪簨浠舵帹閫佺粰鏈哄櫒浜築 |
| 馃攲 **鏃犲叕缃慖P** | 涓ゅ彴鏈哄櫒閮藉湪鍐呯綉锛屾棤娉曠洿鎺ユ毚闇叉湇鍔?|

## 鎺㈢储杩囩殑鏂规

### 鉂?鏂规1锛氶涔?API 杞锛堟湭瀹屽叏鎵撻€氾級
- 闇€瑕侀涔﹀簲鐢ㄦ潈闄?`im:message.group_msg`
- 鏉冮檺闇€瑕佸湪椋炰功寮€鍙戣€呭悗鍙版坊鍔犮€佸彂甯冩柊鐗堟湰銆佺鐞嗗憳瀹℃壒
- 鏈€缁堟病鏈夎蛋閫氳繖鏉¤矾寰?
### 鉂?鏂规2锛歐ebhook 鐩磋繛锛堜笉鍚屽瓙缃戜笉閫氾級
- 宸ヤ綅鐢佃剳閰嶇疆浜?Hermes Webhook锛堢鍙?8644锛?- 绗旇鏈篃閰嶇疆浜?Webhook锛堢鍙?8644锛?- 浣嗙敱浜?`192.168.1.x` 鍜?`192.168.3.x` 鍦ㄤ笉鍚屽瓙缃戯紝TCP 杩炴帴瓒呮椂
- Webhook 閰嶇疆璁板綍锛?  - 宸ヤ綅鐢佃剳: `http://192.168.1.103:8644/webhooks/notebook-bridge`
  - 瀵嗛挜: `RJiOxwixczhO1WMCAjPneghPeueFZ-CeEWg5Iq9s6Ak`
  - 绛惧悕鏂瑰紡: HMAC-SHA256 V2锛坄X-Webhook-Signature-V2` + `X-Webhook-Timestamp`锛?
### 鉁?鏂规3锛欸itHub 浠撳簱闃熷垪锛堟渶缁堥噰鐢級
- 鍒╃敤涓ゅ彴鏈哄櫒閮借兘璁块棶浜掕仈缃?- 浣跨敤 GitHub 浠撳簱浣滀负娑堟伅闃熷垪

## 鏈€缁堟柟妗堬細GitHub 浠撳簱闃熷垪

### 浠撳簱缁撴瀯

```
jianmang1/agent-interop/
鈹溾攢鈹€ requests/          # 绗旇鏈?鈫?宸ヤ綅鐢佃剳 鐨勮姹傞槦鍒?鈹?  鈹溾攢鈹€ README.md
鈹?  鈹斺攢鈹€ request-{timestamp}-{rand}.json
鈹溾攢鈹€ results/           # 宸ヤ綅鐢佃剳 鈫?绗旇鏈?鐨勭粨鏋滈槦鍒?鈹?  鈹溾攢鈹€ README.md
鈹?  鈹斺攢鈹€ result-{timestamp}-{rand}.json
鈹斺攢鈹€ site_r/            # GEE Python 閬ユ劅鐗╁€欏垎鏋愪唬鐮?    鈹斺攢鈹€ ...
```

### 閫氫俊鍗忚

#### 璇锋眰鏍煎紡锛堢瑪璁版湰鈫掑伐浣嶇數鑴戯級

鏂囦欢璺緞: `requests/request-{timestamp}-{rand4}.json`

```json
{
  "type": "screenshot",
  "msg": "璇锋埅涓€寮犳闈㈡埅鍥?,
  "timestamp": "2026-07-15 11:52:44",
  "reply_to": "results/result-{timestamp}-{rand4}.json"
}
```

#### 缁撴灉鏍煎紡锛堝伐浣嶇數鑴戔啋绗旇鏈級

鏂囦欢璺緞: `results/result-{timestamp}-{rand4}.json`

```json
{
  "type": "screenshot",
  "status": "done",
  "path": "E:\\agent浜掗€歕\screenshot.png",
  "note": "鎴浘宸蹭繚瀛?,
  "processed_at": 1784087564
}
```

### 璁よ瘉鏂瑰紡

- Token 绫诲瀷: GitHub Classic PAT锛坄ghp_` 寮€澶达級
- 鏉冮檺鑼冨洿: `repo`锛堝畬鏁寸鏈変粨搴撴帶鍒讹級
- Token 鍊? 瑙?memory 鎴?.env

### 鎿嶄綔娴佺▼

```
绗旇鏈?                                    宸ヤ綅鐢佃剳
  鈹?                                         鈹?  鈹溾攢 鍐?requests/request-xxx.json 鈹€鈹€鈹€鈹€鈹€鈹€鈫?   鈹?  鈹?                                         鈹溾攢 杞鍙戠幇鏂拌姹?  鈹?                                         鈹溾攢 鎵ц浠诲姟锛堟埅鍥剧瓑锛?  鈹?                                         鈹溾攢 鍐?results/result-xxx.json
  鈹?                                         鈹?  鈹溾攢 杞鍙戠幇鏂扮粨鏋?鈫愨攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€    鈹?  鈹?                                         鈹?  鈹斺攢 璇诲彇缁撴灉鏂囦欢锛屽畬鎴愰棴鐜?                 鈹?```

### 杞鑴氭湰

宸ヤ綅鐢佃剳宸叉湁杞鑴氭湰: `poll-github-queue.ps1`
- 閫氳繃 GitHub REST API 杞 `requests/` 鐩綍
- 鏈湴缁存姢 `.processed_tracker.json` 閬垮厤閲嶅澶勭悊
- 鍙戠幇鏂?`.json` 璇锋眰 鈫?涓嬭浇 鈫?澶勭悊 鈫?鍐欑粨鏋?
## 鐜閰嶇疆瑕佺偣

### 宸ヤ綅鐢佃剳
- **杩愯鐜**: Windows 10, Hermes Agent (妗岄潰鐗?
- **椋炰功閰嶇疆**: WebSocket 妯″紡锛宍FEISHU_ALLOW_BOTS=mentions`
- **Webhook**: 绔彛 8644锛屽凡鍒涘缓 `notebook-bridge` 璺敱锛堝鐢級
- **Git**: 宸插畨瑁咃紙`git version 2.55.0.windows.1`锛?- **GitHub CLI**: 宸插畨瑁咃紙`gh version 2.96.0`锛?- **Python**: 3.14.6

### 绗旇鏈?- 闇€閰嶇疆 GitHub PAT 璁块棶鍚屼竴浠撳簱
- 闇€瀹炵幇杞閫昏緫鎴?webhook 瑙﹀彂

## 缁忛獙鏁欒

1. **椋炰功骞冲彴闄愬埗**: 椋炰功涓嶄細灏嗘満鍣ㄤ汉涔嬮棿鐨?@娑堟伅杞彂缁欑洰鏍囨満鍣ㄤ汉銆傝繖鏄钩鍙拌璁★紝涓嶆槸閰嶇疆闂
2. **Fine-grained PAT vs Classic PAT**: Fine-grained PAT 鏉冮檺鍒嗛」缁嗕絾閰嶇疆澶嶆潅锛汣lassic PAT 鍕句笂 `repo` 涓€姝ュ埌浣嶆洿鐪佷簨
3. **Webhook HMAC 绛惧悕**: Hermes webhook 浣跨敤 HMAC-SHA256 V2锛岄渶瑕?`X-Webhook-Signature-V2` + `X-Webhook-Timestamp` 澶达紝绛惧悕瀛楃涓叉牸寮忎负 `{timestamp}.{json_body}`
4. **GitHub API 闄愬埗**: 鐢?API 閫愭枃浠朵笂浼犲ぇ閲忓皬鏂囦欢鏁堢巼浣庯紱鎵归噺鎻愪氦鐢?git tree 鏂瑰紡鏇撮珮鏁?5. **璺ㄥ瓙缃戦€氫俊**: 鏈€绠€鏂规鏄繛鍚屼竴涓?WiFi锛涘鏋滀笉琛屽氨鐢ㄤ簰鑱旂綉鍙闂殑涓粙锛堝 GitHub锛?