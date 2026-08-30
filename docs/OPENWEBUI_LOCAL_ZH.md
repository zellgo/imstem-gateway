# 本地 Open WebUI：Desktop 与 Computer

面向：需要自己建知识库、处理大量本地文件的同事  
更新日期：2026-08-30

公司云端对话 [https://chat.imstem.org](https://chat.imstem.org) **可以继续用**（短消息、看一眼模型、不带大文件的日常问法）。  
处理 **大批本地文件、自己的知识库、本机文件夹 / 终端** 时，请用本机上的 **Open WebUI Desktop** 和 **Open WebUI Computer**。文件留在你电脑里，模型仍走公司网关。

云端界面按钮说明仍看 [OPENWEBUI_GUIDE_ZH.md](OPENWEBUI_GUIDE_ZH.md)。密钥与计费看 [USER_GUIDE_ZH.md](USER_GUIDE_ZH.md)。

---

## 1. 为什么要在自己电脑上跑

| | 公司云端 `chat.imstem.org` | 本机 Desktop / Computer |
|---|---|---|
| 适合 | 短对话、外出、不带大文件 | 方案 PDF、TMF、纪要、代码目录 |
| 文件在哪 | 先上传到公司服务器再处理 | **留在你硬盘**，本地建知识库 |
| 大文件 | 上传慢、排队、超时 | 本机读盘，快得多 |
| 账号 | 入职邮件里的 Open WebUI 账号 | **你自己在本机新建**的账号 |
| 模型费用 | 记在你的 CHAT 密钥上 | 同样记在你的网关密钥上（用的还是公司网关） |

这样做的优点：

- **文件不出电脑。** 知识库、PDF、文件夹不经过公司 Open WebUI 服务器。
- **建库快。** 本地磁盘索引，不把几十上百个文件先传到 `chat.imstem.org`。
- **自己管库。** 每个人一套知识库，不和同事抢云端空间。
- **模型仍是公司的。** 连 `https://llm.imstem.org/v1`，用入职邮件里的个人密钥，用量照常记账。
- **Computer 能碰本机目录和终端。** Desktop 负责对话和知识库；Computer 负责在你电脑上读文件、跑命令。

不要把阿里云 / 小米官方 Key 填进本地软件。只用公司发给你的虚拟密钥。

---

## 2. 你要准备什么

- Windows 10+ / macOS 12+ / 常见 Linux
- 入职邮件里的 **个人 API 密钥**（`CHAT` 或 `AGENT` 均可；日常对话用 **CHAT**）
- 公司网关：`https://llm.imstem.org/v1`（必须带 `/v1`）
- 不要用 Open WebUI 登录密码当 API Key

---

## 3. Open WebUI Desktop：安装并连公司网关

官方仓库与安装包：[https://github.com/open-webui/desktop](https://github.com/open-webui/desktop)

Windows 一般下 `open-webui-x64-setup.exe`。macOS Apple Silicon 下 `open-webui-arm64.dmg`。完整列表在仓库的 **Releases**。

只从 GitHub 官方 Releases 下载，不要用网盘或来路不明的安装包。该应用标注为早期版本，偶发异常可看仓库 Issues。

### 3.1 第一次打开

1. 安装并启动 **Open WebUI Desktop**。
2. **先在本机创建自己的账号**（邮箱 + 密码，这是你电脑上的本地账号，不是 `chat.imstem.org` 那套）。
3. 用刚建的本地账号登录。

### 3.2 把公司网关填进 Connections

登录后：

1. 点自己名字那个 **圆头像 / 名字圈**
2. **Settings / 设置**
3. **AI / Connections**（有的界面写成 **Connections**）
4. **Edit connections / 编辑连接**
5. 填：

| 项 | 填什么 |
|---|---|
| URL | `https://llm.imstem.org/v1`（必须带 `/v1`） |
| Auth | **Bearer** |
| API Key | 入职邮件里你自己的虚拟密钥 |

保存。左上角模型列表应出现 `qwen3.8-flash`、`glm-5.3-flash` 等公司模型。没有的话硬刷新或退出再开；仍没有，核对 URL 是否漏了 `/v1`、密钥是不是 CHAT/AGENT 那把。

默认模型建议 `qwen3.8-flash` 或 `glm-5.3-flash`（同级可换）。

### 3.3 在 Desktop 里建自己的知识库

文件在本地处理，步骤和云端类似：

1. **Workspace → Knowledge / 知识库**
2. 新建一个库（按项目起名，例如 `MED-某方案`）
3. 从本机文件夹添加 PDF / Word / 文本（不要传可识别患者信息、密码、未脱敏病历）
4. 聊天输入框打 `#` 引用该库

大批文件请在 Desktop 做，不要往 `chat.imstem.org` 上传。

---

## 4. Open WebUI Computer：本机文件夹与终端

[Open WebUI Computer](https://github.com/open-webui/computer)（命令一般是 `cptr`）把 **你这台电脑** 开在浏览器里：工作区里的文件、终端、git。它跑在你机器上，不把整盘项目先传到公司云。

官方说明：[https://docs.openwebui.com/getting-started/quick-start/connect-an-agent/cptr](https://docs.openwebui.com/getting-started/quick-start/connect-an-agent/cptr)

### 4.1 安装并启动

本机已有 Python 时：

```bash
pip install cptr
cptr run
```

或：

```bash
uvx cptr@latest run
```

默认打开 `http://localhost:8000`。第一次按提示建本地账号。

用 Docker（把当前目录挂进容器当工作区）：

```bash
docker run --rm -it \
  -p 8000:8000 \
  -v cptr-data:/data \
  -v "$PWD:/workspace" \
  -w /workspace \
  ghcr.io/open-webui/computer:latest
```

日志里会给出带一次性 token 的地址，用它创建管理员账号。`-v cptr-data:/data` 要保留，否则重启丢账号。

长期挂着可用官方 compose，把 `~/projects` 等目录挂进去，再在界面里加为 workspace。

### 4.2 让 Computer 使用公司模型

在 Computer 里：

1. **Settings → Admin → Connections**（或 **Settings → Connections**）
2. 添加连接，类型选 **OpenAI**（OpenAI 兼容，没有单独的「公司网关」项）
3. **Base URL**：`https://llm.imstem.org/v1`
4. **API Key**：你的个人虚拟密钥
5. Models 可留空，让它自动拉网关模型列表；然后把默认模型设成 `qwen3.8-flash` 或 `glm-5.3-flash`

不要填阿里云 / 小米官方地址。

### 4.3 接到 Desktop（可选，推荐）

Desktop 负责聊天界面，Computer 负责碰本机文件：

1. Computer：**Settings → Gateway**，建一把 Computer 自己的 Key（`sk-cptr-...`，只显示一次），记下 Base URL，一般是 `http://localhost:8000/v1`
2. 打开 **Open WebUI Desktop**
3. **Settings → Admin → Connections**（或 AI Connections）→ 添加
4. URL：`http://localhost:8000/v1`；API Key：刚才的 `sk-cptr-...`
5. 保存。模型列表里应出现 `cptr/工作区名`

选这个模型对话时，助手可以读该工作区里的文件、跑终端。工作仍走你在 Computer 里配的公司网关，费用记在你的密钥上。

若 Desktop 用 Docker 跑、Computer 在宿主机：把 `localhost` 换成 `host.docker.internal`。

### 4.4 日常怎么用 Computer

1. 在 Computer 里把项目目录加成 **workspace**
2. 需要改文件、列目录、跑脚本时，选 `cptr/该工作区`
3. 只要问答、引用知识库，用 Desktop 里的公司模型即可
4. 不要让它对含患者标识、密码、未脱敏病历的目录动手

更细的官方步骤见 [Connect Open WebUI Computer](https://docs.openwebui.com/getting-started/quick-start/connect-an-agent/cptr)。

---

## 5. 推荐分工

| 场景 | 用哪个 |
|---|---|
| 一两句翻译、改邮件、不带附件 | 公司云端 [chat.imstem.org](https://chat.imstem.org) 即可 |
| 一堆 PDF / 自己的知识库 | **Open WebUI Desktop** + 公司 `llm.imstem.org/v1` |
| 对着本机项目文件夹问、要终端 | **Open WebUI Computer**，模型仍走公司网关 |
| Codex / Claude Code | 不要用这套；见员工指南里的 AGENT 密钥和 CC Switch |

云端慢、上传大文件失败：改 Desktop / Computer，不是把文件再传一次到云端。

---

## 6. 安全（和云端同一套红线）

- 密钥只填你自己的，不要用同事的，不要发到微信
- 不要上传 / 挂载可识别患者信息、身份证、未脱敏病历、密码
- 模型输出是草稿，不能直接当法规或医学终稿
- Desktop 和 Computer 的本地账号密码自己保管；离职时删本机应用数据

---

## 7. 常见问题

**Desktop 里没有模型？** URL 必须是 `https://llm.imstem.org/v1`。Auth 必须是 Bearer。密钥用邮件里的 CHAT 或 AGENT，不是网页登录密码。

**能不能继续只用 chat.imstem.org？** 能。短对话没问题。大规模本地文件请改 Desktop / Computer。

**费用会不会算两份？** 不会。本地软件只是客户端，真正调用的还是公司网关，记在你的虚拟密钥上。

**Computer 和 Desktop 必须两个都装吗？** 只要知识库：装 Desktop 就够。要对着文件夹 / 终端干活再装 Computer。

**官方文档在哪？** Desktop：[github.com/open-webui/desktop](https://github.com/open-webui/desktop)。Computer：[github.com/open-webui/computer](https://github.com/open-webui/computer) 与 [docs.openwebui.com](https://docs.openwebui.com/getting-started/quick-start/connect-an-agent/cptr)。
