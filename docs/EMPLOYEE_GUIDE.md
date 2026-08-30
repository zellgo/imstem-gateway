# Employee guide — ImStem AI

完整中文指南：[USER_GUIDE_ZH.md](USER_GUIDE_ZH.md)  
Open WebUI 界面与知识库：[OPENWEBUI_GUIDE_ZH.md](OPENWEBUI_GUIDE_ZH.md)  
本地 Desktop / Computer：[OPENWEBUI_LOCAL_ZH.md](OPENWEBUI_LOCAL_ZH.md)  
WorkBuddy 接公司网关：[WORKBUDDY_ZH.md](WORKBUDDY_ZH.md)  
费用与岗位选模型：[MODEL_COST_ZH.md](MODEL_COST_ZH.md)  
入职邮件模板：[EMAIL_ONBOARDING_ZH.md](EMAIL_ONBOARDING_ZH.md)

入口：[https://llm.imstem.org](https://llm.imstem.org)

## 网页对话

1. 打开 [https://chat.imstem.org](https://chat.imstem.org)
2. 用管理员邮件里的 **邮箱 + 密码** 登录（不是工号）
3. 选模型：

| 模型 | 适合 |
|---|---|
| `qwen3.8-flash` | 快、便宜，草稿和翻译 |
| `qwen3.8-27b` | 日常写作、修改 |
| `qwen3.8-max` | 难文、长文档 |
| `kimi-k3` | Agent、代码（Codex 默认） |
| `deepseek-v4-flash-0731` | 低成本推理 |
| `deepseek-v4-pro-0813` | 更强 DeepSeek V4 |
| `mimo-v2.5` | 小米 MiMo 2.5 |
| `mimo-v2.5-pro` | 小米 MiMo 2.5 Pro |

不要粘贴阿里云或小米的官方 Key。你没有那些 Key。

## 个人 API（Codex、Claude Code、OpenCode、Python）

管理员会发给你一把 **AGENT** 虚拟密钥。它只在 `https://llm.imstem.org` 上有效。用量记在你的工号上。完整说明：[https://llm.imstem.org/guide](https://llm.imstem.org/guide)

Windows 上把 ChatGPT / Codex / Claude Code 切到公司网关：用 [CC Switch](https://ccswitch.io/zh/)（中文官方站）。地址栏叫 **API Request URL**（Codex 填 `https://llm.imstem.org/v1`，Claude Code 填 `https://llm.imstem.org` 不要加 `/v1`）+ AGENT 密钥。默认模型：点输入框右边下载按钮拉取列表，选好后 Save。Codex 每次切换后用任务管理器搜索 `chatgpt` 结束全部进程再打开。步骤见 [USER_GUIDE_ZH.md](USER_GUIDE_ZH.md) §5.2。

### Codex / OpenCode / OpenAI SDK

```bash
export OPENAI_BASE_URL=https://llm.imstem.org/v1
export OPENAI_API_KEY=sk-…你的 AGENT 密钥…
```

推荐 `kimi-k3` 或 `qwen3.8-max`。如果工具仍发送 `gpt-4o` / `gpt-5`，网关会转到 `kimi-k3`，费用仍是你的。

### Claude Code

```bash
export ANTHROPIC_BASE_URL=https://llm.imstem.org
export ANTHROPIC_API_KEY=sk-…你的 AGENT 密钥…
export ANTHROPIC_MODEL=kimi-k3
```

`ANTHROPIC_BASE_URL` **不要**加 `/v1`。拷贝示例见 [CODING_AGENTS.md](CODING_AGENTS.md)。

## 不要上传

| 类别 | 例子 | 规则 |
|---|---|---|
| 公开 | 论文、公开法规 | 可以 |
| 内部 | 草稿、非公开 PPT | 可以走这套系统 |
| 敏感 | 可识别患者信息、密码、API Key、未批准的法律文件 | **不要上传** |

临床内容先去标识再问模型。

## 出问题

找网关管理员。密钥失效通常是轮换或月度额度用完。
