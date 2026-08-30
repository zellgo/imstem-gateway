# 入职邮件模板（大模型账号）

发给每位员工一封。密钥来自 `secret/outbox/roster.csv` 与对应 `MED00X.md`。  
**不要把本模板填好后的真实密钥提交到 git。** 填好的信在 `secret/outbox/emails/`。

涂美慧（MED004）的邮箱在花名册中为拼音推断，发送前请口头确认。

---

## 主题

```
【ImStem】大模型账号已开通（网页登录 + API）— 请先看试用与选模型说明
```

---

## 正文（复制后替换 {{占位符}}）

```
{{姓名}} 您好：

公司已开通统一大模型入口，用于方案写作、监查记录、会议纪要、翻译和编程助手。
这不是个人 ChatGPT 账号，密钥和用量记在您的工号上。

━━━━━━━━━━━━━━━━
一、费用（必读）
━━━━━━━━━━━━━━━━

当前公司使用的是阿里云百炼「通义千问」免费试用额度。

• 试用期内，优先用千问（尤其是 qwen3.8-flash），尽量把免费额度用在正经工作上。
• 免费额度用尽后，将按阿里云官方 Token 单价从公司账户扣费，并记到您的密钥。
• Kimi、DeepSeek、小米 MiMo 不在千问免费额度内，调用即可能产生费用。
• 日常请默认 qwen3.8-flash。写不好再换 qwen3.8-27b，难题再用 qwen3.8-max。
• 不要把 kimi-k3 当聊天默认模型，它是目前最贵的一档。

完整选模型与单价：请向管理员索取《模型费用与岗位推荐》，或看入职附件。

━━━━━━━━━━━━━━━━
二、网页对话（每天用这个）
━━━━━━━━━━━━━━━━

地址：https://chat.imstem.org
登录邮箱：{{登录邮箱}}
密码：{{网页密码}}

登录后左上角选择模型。推荐先选：qwen3.8-flash

大批本地文件、自己建知识库：不要往云端传。用本机 Open WebUI Desktop
  下载：https://github.com/open-webui/desktop
  说明：https://llm.imstem.org/guides/local-openwebui

━━━━━━━━━━━━━━━━
三、编程 / Agent API（Codex、Claude Code、Python）
━━━━━━━━━━━━━━━━

仅在公司网关有效，不是阿里云或小米官方 Key。

Base URL（OpenAI / Codex / Python，必须带 /v1）：
https://llm.imstem.org/v1

Agent API Key：
{{AGENT密钥}}

推荐模型：
• 日常：qwen3.8-flash
• 写代码：mimo-v2.5-pro
• 很难的医学文本：qwen3.8-max

请在工具里写上上面的模型名。若软件仍发送 gpt-4o / gpt-5 / claude-sonnet-4-5，
网关会转到最贵的 kimi-k3，费用仍算您的。

Windows 上 ChatGPT / Codex / Claude Code：请用 CC Switch 切到公司密钥
  下载：https://ccswitch.io/zh/
  地址栏叫 API Request URL（不是 Base URL）
    Codex：https://llm.imstem.org/v1
    Claude Code：https://llm.imstem.org（不要加 /v1）
  默认模型：点输入框右边下载按钮拉取列表，选好后 Save
  说明：https://llm.imstem.org/guide  与  https://llm.imstem.org/guides/user

Claude Code 注意：Base URL 不要加 /v1
  ANTHROPIC_BASE_URL=https://llm.imstem.org
  ANTHROPIC_API_KEY=（同一把 AGENT 密钥）
  ANTHROPIC_MODEL=qwen3.8-flash

━━━━━━━━━━━━━━━━
四、安全
━━━━━━━━━━━━━━━━

• 不要把密钥发给同事或发到微信群
• 不要上传可识别患者信息、身份证号、未脱敏病历、密码
• 模型输出是草稿，不能直接当法规/医学终稿

总入口：https://llm.imstem.org
API 说明：https://llm.imstem.org/guide

登录或密钥失败请回复本邮件。
```

---

## 发送清单

| 工号 | 姓名 | 岗位 | 邮箱 | 备注 |
|---|---|---|---|---|
| MED001 | 王丁坤 | 医学经理 | dingkunwang@imstem.com.cn | |
| MED002 | 李子木 | CRA | zimuli@imstem.com.cn | |
| MED003 | 刘士麟 | 项目经理 | shilinliu@imstem.com.cn | |
| MED004 | 涂美慧 | CRA | meihuitu@imstem.com.cn | 邮箱待确认 |
| MED005 | 王斯 | CRA | siwang@imstem.com.cn | |
| MED006 | 于丽伟 | 项目经理 | liweiyu@imstem.com.cn | |
| MED007 | 祁星 | CTA | xingqi@imstem.com.cn | |
