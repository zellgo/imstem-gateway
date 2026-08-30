# ImStem 大模型使用指南（员工完整版）

面向：医学、临床监查、项目管理及后续入职同事  

更新日期：2026-08-30

---

## 1. 这套系统是什么

公司把通义千问、Kimi、DeepSeek、小米 MiMo 接到统一网关。你 **看不到、也不需要** 阿里云或小米的官方 Key。

你拿到的是两样东西：

| 用途                                   | 你怎么用                                                       | 费用记在谁身上             |
| ------------------------------------ | ---------------------------------------------------------- | ------------------- |
| 网页对话                                 | [https://chat.imstem.org](https://chat.imstem.org) 用邮箱密码登录 | 你的工号 `MED00X-CHAT`  |
| 编程 / Agent（Codex、Claude Code、Python） | 个人 **AGENT** 密钥 + 公司 Base URL                              | 你的工号 `MED00X-AGENT` |

两把密钥都是公司网关发的虚拟密钥，只能打 `https://llm.imstem.org`。转给同事、贴到公开网页或 ChatGPT 网站等于把额度送给别人。

---

## 2. 计费说明（请先读）

**当前阶段：公司正在使用阿里云百炼「通义千问」免费试用额度。**

- 试用期内，千问系列调用尽量走免费额度，账单上可能显示为 0 或接近 0。
- **免费额度用尽后，按阿里云官方 Token 单价从公司账户扣费**，同时记到你的虚拟密钥上。
- Kimi、DeepSeek 快照版、小米 MiMo **不在千问免费额度里**，从一开始就可能产生费用。
- 个人有月度上限。超额后密钥会失败，找管理员加额度，不要换同事的密钥继续用。

省钱原则：**日常默认 `qwen3.8-flash`。写不好再升级，不要一上来用 Max / Kimi。**  
详细单价与岗位推荐见 [MODEL_COST_ZH.md](MODEL_COST_ZH.md)。实时官方价（￥）：[https://llm.imstem.org/costs](https://llm.imstem.org/costs)。

---

## 3. 网页对话（Open WebUI）

1. 打开 [https://chat.imstem.org](https://chat.imstem.org)
2. 用入职邮件里的 **登录邮箱 + 密码**（不是工号，也不是阿里云账号）
3. 左上角选模型，发消息

界面按钮、文件夹、**知识库（Workspace → Knowledge）** 的逐步说明见 [OPENWEBUI_GUIDE_ZH.md](OPENWEBUI_GUIDE_ZH.md)。  
处理大批本地文件、自己建知识库：用本机 [Open WebUI Desktop / Computer](OPENWEBUI_LOCAL_ZH.md)，不要把大文件传到云端。

首次登录后建议：

- 把默认模型设成 `qwen3.8-flash`
- 不要在「连接 / Connections」里粘贴阿里云或小米官方 Key（公司已经配好）
- 硬刷新一次（Ctrl+Shift+R）如果看不到模型列表

---

## 4. 选哪个模型（日常口诀）

**能用 Flash 就不要用 Max；能用 Max 就不要用 Kimi。**

| 优先级               | 模型名（必须一字不差）                   | 适合做什么                           | 不适合                 |
| ----------------- | ----------------------------- | ------------------------------- | ------------------- |
| 1 默认              | `qwen3.8-flash`               | 翻译、润色、会议纪要、邮件、访视报告草稿、清单、把长文缩短   | 很难的法规对读、长程写代码       |
| 2 日常写作            | `qwen3.8-27b`                 | SOP / 方案章节、监查发现归纳、项目风险描述、PPT 大纲 | 把整本方案反复塞进去「再想一遍」    |
| 3 难题              | `qwen3.8-max`                 | 方案逻辑冲突、法规条款对照、复杂医学论证、审稿意见回复     | 日常聊天、批量翻译           |
| 4 便宜推理            | `deepseek-v4-flash-0731`      | 列表、分类、简单推理；可作 Flash 备选          | 要强中文公文腔时不如千问        |
| 5 强推理（仍比 Kimi 便宜） | `deepseek-v4-pro-0813`        | 数学/逻辑/代码推理，Flash 不够用时           | 工作日忙时单价翻倍，见费用表      |
| 6 代码 / Agent 首选   | `mimo-v2.5` / `mimo-v2.5-pro` | Codex、脚本、表格处理、多步工具调用            | 正式中文医学公文（优先千问）      |
| 7 最后手段            | `kimi-k3`                     | 别的模型都失败的长程 Agent、极难代码           | **禁止当默认聊天模型**（单价最高） |

岗位对照：

| 岗位   | 默认                         | 升级到 27b             | 才用 Max        | Agent / 代码                   |
| ---- | -------------------------- | ------------------- | ------------- | ---------------------------- |
| 医学经理 | Flash：邮件、摘要、中英翻译           | 方案/IB/CSR 章节、审稿意见草稿 | 关键法规对读、科学逻辑卡住 | `mimo-v2.5-pro`；Kimi 仅在连续失败后 |
| 项目经理 | Flash：纪要、邮件、进度话术           | 风险登记、供应商说明、里程碑冲突    | 复杂跨部门方案取舍     | 少用；脚本用 MiMo Pro              |
| CRA  | Flash：访视报告、query 清单、TMF 核对 | 方案偏离解释、发现分级         | 几乎不用          | 一般不需要；做表用 Flash 或 MiMo       |

---

## 5. 个人 API（Codex / Claude Code / Python）

邮件里的 **AGENT 密钥** 才用于 API。网页登录密码不能当 API Key。

### 5.1 OpenAI 兼容（Codex、OpenCode、Python）

Base URL **必须带** `/v1`：

```bash
export OPENAI_BASE_URL=https://llm.imstem.org/v1
export OPENAI_API_KEY=sk-你的AGENT密钥
```

推荐模型（省钱）：

```text
qwen3.8-flash          # 默认
mimo-v2.5-pro          # 写代码 / Agent
qwen3.8-max            # 很难的医学文本
```

**请在工具里显式指定模型。** 若 Codex / Claude 仍发送 `gpt-4o`、`gpt-5`、`claude-sonnet-4-5`，网关会转到最贵的 `kimi-k3`，费用仍记在你名下。

Codex 配置示例 `~/.codex/config.toml`：

```toml
model = "qwen3.8-flash"
model_provider = "imstem"

[model_providers.imstem]
name = "ImStem"
base_url = "https://llm.imstem.org/v1"
env_key = "OPENAI_API_KEY"
wire_api = "chat"
```

写代码时把 `model` 改成 `mimo-v2.5-pro`。

Python：

```python
from openai import OpenAI
client = OpenAI(base_url="https://llm.imstem.org/v1", api_key="sk-你的AGENT密钥")
print(client.chat.completions.create(
    model="qwen3.8-flash",
    messages=[{"role": "user", "content": "用三句话说明间充质干细胞"}],
).choices[0].message.content)
```

### 5.2 Windows：用 CC Switch 把 Codex / ChatGPT 桌面版切到公司密钥

直接改 `~/.codex/config.toml` 在 ChatGPT 桌面版上经常卡住（Windows 沙盒 / UAC 窗口过不去）。同事实测 **CC Switch** 可以一键把 Codex 切到公司网关，比手改配置稳。

官方下载（中文站）：[https://ccswitch.io/zh/](https://ccswitch.io/zh/)  
支持 Windows 10+、macOS、Linux。公司推荐从该站安装，不要用来路不明的安装包。CC Switch 具体可参照[官网使用指南](https://ccswitch.io/zh/)。

逐步操作：

1. 打开 CC Switch，选 **Codex** 或 **Claude Code** 面板（软件里地址栏叫 **API Request URL**，不是 Base URL）。
2. Codex：先切到 **OpenAI 官方**，启动一次 ChatGPT / Codex 桌面版并完成官方登录（有 ChatGPT 账号即可）。这样桌面版功能还能用。
3. Codex：打开 **设置 → 通用 → Codex 应用增强 → 切换第三方时保留官方登录**（建议打开）。
4. 添加自定义供应商（不要用阿里云/小米官方 Key）：

| 项 | 填什么 |
| --- | --- |
| 名称 | `ImStem` |
| API Request URL（Codex） | `https://llm.imstem.org/v1`（必须带 `/v1`） |
| API Request URL（Claude Code） | `https://llm.imstem.org`（**不要**加 `/v1`） |
| API Key | 入职邮件里的 **AGENT** 密钥 |
| 默认模型 | 先点模型输入框**右边的下载按钮**，拉取可用模型，再选你要用的（日常 `qwen3.8-flash`，写代码 `mimo-v2.5-pro`），点 **Save** |

5. 在 CC Switch 里把当前供应商切到 `ImStem`。
6. Codex 桌面版：**完全退出** ChatGPT / Codex，再打开。切供应商之后不要以为点一下桌面图标就生效。

公司允许的模型名（必须一字不差，不要填 `gpt-5.4` / `gpt-5.6-*`）：

`qwen3.8-flash` · `qwen3.8-27b` · `qwen3.8-max` · `kimi-k3` · `deepseek-v4-flash-0731` · `deepseek-v4-pro-0813` · `mimo-v2.5` · `mimo-v2.5-pro`

**已知问题（请照做，否则会以为「没切成功」）：**

- 默认模型不要空手填完就走。先点输入框右边**下载按钮**拉取网关模型列表，再点选，最后 **Save**。列表里没有的名字可以再手填上面的网关名。
- 每次切换供应商（公司网关 ⇄ OpenAI 官方），或刚换了模型名之后：打开 **任务管理器**，搜索 `chatgpt`，把列出的 **ChatGPT / Codex** 进程全部结束，再重新打开桌面版。只关窗口不够，托盘里残留进程会继续用旧配置。
- 若桌面版仍发送 `gpt-5.4` 等到公司网关，会返回 403（密钥不允许该模型）。回到 CC Switch 确认当前模型是上表里的名字。

切回 OpenAI 官方：在 CC Switch 选 OpenAI Official → 任务管理器结束全部 `chatgpt` 进程 → 再开桌面版。

### 5.3 Claude Code

`ANTHROPIC_BASE_URL` **不要**加 `/v1`（Claude Code 会自己加）：

```bash
export ANTHROPIC_BASE_URL=https://llm.imstem.org
export ANTHROPIC_API_KEY=sk-你的AGENT密钥
export ANTHROPIC_MODEL=qwen3.8-flash
```

---

## 6. 可以问 / 不可以问

| 类别        | 例子                                        | 规则                         |
| --------- | ----------------------------------------- | -------------------------- |
| 可以        | 已发表论文、公开法规、去标识后的方案草稿、内部 SOP 结构、会议纪要模板     | 走公司网关                      |
| 内部可用、仍需谨慎 | 未公开管线描述、供应商商务条款、未注册的试验设计                  | 可以问，不要外发密钥或把全文贴到外部 ChatGPT |
| **禁止**    | 可识别患者信息（姓名、住院号、身份证、影像号）、密码、同事密钥、未脱敏病历、银行卡 | **不要上传**                   |

临床内容：先去标识（去掉姓名/编号/日期组合），再问模型。模型输出不能替代医学、法规或统计签字。

---

## 7. 省钱操作习惯

1. 先 Flash，不满意再 27b，还不行再用 Max。
2. 不要把 100 页方案整份反复贴进 Max。先摘冲突章节，或让 Flash 做摘要再升级。
3. Agent 多轮会把历史对话反复计费。新任务开新会话。
4. 同一段制度/方案要反复问，尽量同一会话，让缓存命中（输入会便宜很多）。
5. 翻译、改错别字、改语气：只用 Flash。
6. 不要开着 Codex 挂机。空转也会打模型。
7. 工作日 9:00–12:00、14:00–18:00（北京时间）DeepSeek **快照版** 走忙时价，能用千问 Flash 就别用 DeepSeek Pro。

---

## 8. 常见问题

**登录后没有模型？** 退出再登录，或 Ctrl+Shift+R。仍没有，找管理员。

**密钥报 401 / 额度用完？** 月度预算用尽或密钥被轮换。找管理员，不要借用别人的 Key。

**网页能聊、API 不能用？** 网页用的是 CHAT 通道；API 必须用 AGENT 密钥，且 Base URL 按上面复制。

**ChatGPT 桌面版切不到公司模型？** 用 [CC Switch](https://ccswitch.io/zh/)（见 5.2）。手改 `config.toml` 在 Windows 桌面版上经常被沙盒窗口挡住。

**CC Switch 列表里没有 qwen / mimo？** 先点模型输入框右边的下载按钮拉取可用模型，选好后 Save。仍没有再手填网关模型名，并在每次切换后用任务管理器结束全部 `chatgpt` 进程。

**能不能自己加 GPT / Claude 官方 Key？** 不要往公司工具里贴个人官方 Key 来「绕过」记账。用 CC Switch 时，公司工作走 ImStem 供应商；个人 OpenAI 账号仅用于登录桌面版本身。

**输出能直接交 CDE / 伦理？** 不能。模型只出草稿，专业人员审核后才能对外。

---

## 9. 入口与帮助

| 页面 | 地址 |
|---|---|
| 总入口 | [https://llm.imstem.org](https://llm.imstem.org) |
| 网页对话 | [https://chat.imstem.org](https://chat.imstem.org) |
| API 说明 | [https://llm.imstem.org/guide](https://llm.imstem.org/guide) |
| CC Switch（切公司密钥） | [https://ccswitch.io/zh/](https://ccswitch.io/zh/) |
| 费用与选模型 | [模型单价与省钱](MODEL_COST_ZH.md) |
| 网页对话与知识库 | [Open WebUI 指南](OPENWEBUI_GUIDE_ZH.md) |
| 本地 Desktop / Computer | [本地 Open WebUI](OPENWEBUI_LOCAL_ZH.md) |

出问题找网关管理员。不要把密钥发到微信群。
