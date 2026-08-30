# WorkBuddy：免费额度用完后接公司网关

面向：已经在用腾讯 WorkBuddy 桌面客户端的同事  
更新日期：2026-08-30

WorkBuddy 自带额度用完后，不要去买零散第三方中转。把自定义模型指到 **公司网关** `llm.imstem.org`，用入职邮件里的个人 **AGENT** 密钥。用量记在你的工号上。

官网（国内）：[https://www.workbuddy.cn](https://www.workbuddy.cn)  
官方文档：[https://www.workbuddy.cn/docs/workbuddy/Overview](https://www.workbuddy.cn/docs/workbuddy/Overview)

自定义模型弹窗 **只接受 OpenAI 兼容协议**。公司网关就是这种协议。

---

## 1. 你要准备什么

| 项 | 填什么 |
|---|---|
| 接口地址 | `https://llm.imstem.org/v1/chat/completions` |
| API Key | 入职邮件里的 **AGENT** 密钥（不是网页登录密码，也不是阿里云/小米官方 Key） |
| 模型名称 | 公司网关模型 ID，见下表 |

WorkBuddy 的「接口地址」要写到 **完整的 chat completions 路径**。只填 `https://llm.imstem.org` 或 `https://llm.imstem.org/v1` 往往会请求失败（腾讯云 TokenHub、多家接入文档都是这样写的）。

公司允许的模型名（一字不差）：

`qwen3.8-flash` · `qwen3.8-27b` · `qwen3.8-max` · `kimi-k3` · `deepseek-v4-flash-0731` · `deepseek-v4-pro-0813` · `mimo-v2.5` · `mimo-v2.5-pro`

日常先用 `qwen3.8-flash`。不要填 `deepseek-chat`、`gpt-4o`、`gpt-5` 这类官方原名，公司密钥不允许。

---

## 2. 方法一：界面设置（推荐）

不同版本入口略有差别，下面两条都能进「添加模型」。

**入口 A（腾讯云文档）：** 左下角账户 → **设置** → 左侧 **模型** → **添加模型**。  
**入口 B：** 新建任务里的大模型切换 → **配置自定义模型**。  
**入口 C：** 右上角 **设置** 图标 → **API 配置 / 模型设置 / 选择模型**。

然后：

1. 提供商选 **自定义 / Custom**（弹窗会写「仅支持 OpenAI 兼容协议 API」）。
2. 依次填写：

| 字段 | 填什么 |
|---|---|
| 接口地址（URL） | `https://llm.imstem.org/v1/chat/completions` |
| API Key | 你的 **AGENT** 密钥 |
| 模型名称（Model ID） | 例如 `qwen3.8-flash` |

3. 高级项如有「工具调用」，建议勾上（WorkBuddy 要调工具）。图片 / 推理按模型能力勾，没有就留空。
4. 有 **测试连接** 就点一下，通过后再 **保存**。没有测试按钮就直接保存。
5. 回到任务界面，在模型选择器的 **自定义** 分组里选刚加的模型，再开工。每个模型要单独加一条（Flash、Max、MiMo Pro 各保存一次）。

保存后若列表里看不到：确认已经勾选/启用该模型，不要还停在 WorkBuddy 自带免费模型上（自带模型会继续扣它自己的积分）。

---

## 3. 方法二：本机 `models.json`（批量时用）

界面不好用、或要一次加多个模型时，改配置文件。先打开一次 WorkBuddy，让它生成目录。

- Windows：`C:\Users\<你的用户名>\.workbuddy\models.json`
- macOS / Linux：`~/.workbuddy/models.json`

UTF-8 无 BOM。示例（密钥自己替换）：

```json
{
  "models": [
    {
      "id": "qwen3.8-flash",
      "name": "ImStem Flash",
      "vendor": "OpenAI",
      "url": "https://llm.imstem.org/v1/chat/completions",
      "apiKey": "sk-你的AGENT密钥",
      "supportsToolCall": true
    },
    {
      "id": "mimo-v2.5-pro",
      "name": "ImStem MiMo Pro",
      "vendor": "OpenAI",
      "url": "https://llm.imstem.org/v1/chat/completions",
      "apiKey": "sk-你的AGENT密钥",
      "supportsToolCall": true
    }
  ],
  "availableModels": ["qwen3.8-flash", "mimo-v2.5-pro"]
}
```

保存后重启 WorkBuddy，在自定义模型里选。

---

## 4. 测通了再干活

保存后新建一个任务，模型选 `qwen3.8-flash`，发一句「用一句话介绍间充质干细胞」。能回就说明走的是公司网关。

失败时按这个顺序查：

1. 接口地址是否写到 `/v1/chat/completions`
2. 密钥是不是 AGENT（以 `sk-` 开头）
3. 模型名是否在上面那张表里
4. 是否仍停在 WorkBuddy 自带模型（那样还会扣免费额度）

---

## 5. 费用与安全

- 自定义模型 **不再扣 WorkBuddy 免费额度**，改为扣公司网关上你的 AGENT 额度。
- 不要把阿里云 / 小米官方 Key 填进 WorkBuddy。
- 不要让它对含患者标识、密码、未脱敏病历的文件夹动手。
- 模型输出是草稿，不能直接当法规或医学终稿。

更完整的选模型说明见 [MODEL_COST_ZH.md](MODEL_COST_ZH.md)。个人 API 总说明见 [USER_GUIDE_ZH.md](USER_GUIDE_ZH.md)。
