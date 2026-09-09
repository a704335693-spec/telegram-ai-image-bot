# Telegram AI 文生图机器人

基于 **Pollinations.ai** 免费 API 的 Telegram 文生图机器人，**完全免费，无需 API Key，无需付费**。

## 特点

- 🆓 **100% 免费**：基于 Pollinations.ai 开源免费 API，无需注册、无需 API Key
- 🎨 **多模型支持**：Flux（高质量）、Turbo（快速）、Sana
- 📐 **多种尺寸**：正方形、横版、竖版、全高清等
- ✨ **提示词增强**：可开启 AI 自动优化提示词
- ⚡ **异步处理**：生成时不阻塞，支持多用户同时使用
- 🔒 **隐私保护**：Pollinations.ai 不存储用户数据

## 费用说明

| 项目 | 费用 |
|------|------|
| Pollinations.ai API | 完全免费 |
| Telegram Bot API | 完全免费 |
| 运行本机器人 | 仅需你的电脑/服务器 |

匿名用户约每 15 秒可生成一张图；在 [auth.pollinations.ai](https://auth.pollinations.ai) 免费注册可提升至每 5 秒一张，并可去除水印。

## 快速开始

### 1. 创建 Telegram 机器人

1. 在 Telegram 中搜索 **@BotFather**
2. 发送 `/newbot`
3. 按提示设置机器人名称和用户名
4. 复制获取到的 **Bot Token**（格式类似 `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

### 2. 配置机器人

1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env`，将 `your_bot_token_here` 替换为你的 Bot Token

### 3. 启动机器人

**Windows 用户**：双击运行 `start.bat`

**手动启动**：
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动
python bot.py
```

### 4. 使用机器人

1. 在 Telegram 中搜索你的机器人用户名
2. 发送 `/start` 开始
3. 直接发送文字描述即可生成图片

## 命令列表

| 命令 | 功能 |
|------|------|
| `/start` | 开始使用，显示欢迎信息 |
| `/help` | 显示帮助信息 |
| `/model` | 切换 AI 模型（Flux/Turbo/Sana） |
| `/size` | 切换图片尺寸 |
| `/enhance` | 开关提示词增强（AI自动优化描述） |
| `/settings` | 查看当前设置 |

## 使用技巧

### 提示词建议

好的提示词包含以下要素：
- **主体**：什么人/物
- **场景**：在哪里
- **风格**：水彩、油画、赛博朋克、像素风、动漫等
- **光线**：日落、霓虹、柔光等
- **构图**：特写、全景、俯视等

**示例**：
```
一只戴着墨镜的猫咪坐在赛博朋克城市的屋顶，霓虹灯，雨夜，电影感构图
```

```
水彩风格的山间日出，薄雾，松树，温暖的金色阳光，宁静
```

### 模型选择

- **Flux**：默认模型，质量最高，适合大多数场景，生成稍慢
- **Turbo**：快速生成，适合快速预览或简单图片
- **Sana**：轻量模型，生成最快

## 技术细节

- **语言**：Python 3.10+
- **框架**：python-telegram-bot v20+（异步）
- **HTTP**：aiohttp
- **图片 API**：Pollinations.ai `https://image.pollinations.ai/prompt/{prompt}`

### API 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| prompt | 图片描述（必填） | - |
| model | AI 模型 | flux |
| width | 图片宽度 | 1024 |
| height | 图片高度 | 1024 |
| seed | 随机种子（固定可复现） | 随机 |
| nologo | 去除水印 | true |
| enhance | AI 增强提示词 | false |

## 常见问题

**Q: 生成图片很慢？**
A: 免费 API 有速率限制，匿名用户约 15 秒/张。可免费注册 Pollinations 提升到 5 秒/张。也可切换到 Turbo 或 Sana 模型加快速度。

**Q: 生成失败怎么办？**
A: 可能是服务器繁忙或网络问题。请稍后重试，或尝试切换模型、减小尺寸。

**Q: 可以在服务器上 24 小时运行吗？**
A: 可以。将项目部署到任何支持 Python 的服务器上，使用 `nohup python bot.py &` 或 systemd 服务后台运行即可。

**Q: 需要付费吗？**
A: 不需要。本机器人所有依赖的 API 都是免费的。Pollinations.ai 提供免费额度供个人使用。

## 许可证

MIT License

## 致谢

- [Pollinations.ai](https://pollinations.ai) - 提供免费的 AI 图像生成 API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot 框架
