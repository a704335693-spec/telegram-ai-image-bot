#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram AI 文生图机器人
基于 Pollinations.ai 免费 API，无需 API Key，完全免费。
支持本地长轮询模式 和 云端 Webhook 模式（Render.com 等）。
"""

import os
import io
import asyncio
import logging
from urllib.parse import quote

import aiohttp
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ============ 配置 ============
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    print("错误：请设置 TELEGRAM_BOT_TOKEN 环境变量")
    print("获取方式：在 Telegram 中联系 @BotFather 创建机器人并获取 Token")
    exit(1)

# 代理设置（本地运行时中国大陆访问 Telegram API 必需，云端部署留空）
PROXY_URL = os.getenv("PROXY_URL", "").strip()

# Webhook 模式配置（云端部署时设置）
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
PORT = int(os.getenv("PORT", "10000"))  # Render 默认端口

# 可用模型
AVAILABLE_MODELS = {
    "flux": "Flux（高质量，推荐）",
    "turbo": "Turbo（快速生成）",
    "sana": "Sana",
}

# 可用尺寸
AVAILABLE_SIZES = {
    "1024x1024": "正方形 1024×1024",
    "1280x720": "横版 1280×720",
    "720x1280": "竖版 720×1280",
    "1920x1080": "全高清横版 1920×1080",
    "512x512": "快速 512×512",
}

# API 地址
POLLINATIONS_API = "https://image.pollinations.ai/prompt"

# 日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============ 用户状态管理 ============
class UserSettings:
    """管理每个用户的生成设置"""

    def __init__(self):
        self.model = "flux"
        self.size = "1024x1024"
        self.enhance = False

    def get_width_height(self):
        w, h = self.size.split("x")
        return int(w), int(h)


user_settings = {}


def get_user_settings(user_id: int) -> UserSettings:
    if user_id not in user_settings:
        user_settings[user_id] = UserSettings()
    return user_settings[user_id]


# ============ 核心功能 ============
async def generate_image(prompt: str, settings: UserSettings) -> bytes:
    """调用 Pollinations.ai 生成图片"""
    width, height = settings.get_width_height()
    encoded_prompt = quote(prompt)

    url = (
        f"{POLLINATIONS_API}/{encoded_prompt}"
        f"?model={settings.model}"
        f"&width={width}"
        f"&height={height}"
        f"&nologo=true"
        f"&enhance={'true' if settings.enhance else 'false'}"
        f"&referrer=telegram-ai-image-bot"
    )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; TelegramAIBot/1.0)"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=300)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"API 返回错误 {resp.status}: {error_text[:200]}")
            return await resp.read()


# ============ Telegram 处理函数 ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 命令"""
    user = update.effective_user
    welcome = (
        f"你好，{user.first_name}！我是 AI 文生图机器人。\n\n"
        f"我基于 Pollinations.ai 免费 API 驱动，完全免费，无需付费。\n\n"
        f"使用方法：\n"
        f"直接发送文字描述，我就会为你生成图片。\n\n"
        f"示例：\n"
        f"一只戴着墨镜的猫咪坐在赛博朋克城市的屋顶\n"
        f"水彩风格的山间日出风景\n\n"
        f"其他命令：\n"
        f"/model - 切换 AI 模型\n"
        f"/size - 切换图片尺寸\n"
        f"/enhance - 开关提示词增强\n"
        f"/settings - 查看当前设置\n"
        f"/help - 显示帮助信息"
    )
    await update.message.reply_text(welcome)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 命令"""
    help_text = (
        "AI 文生图机器人帮助\n\n"
        "基本用法：\n"
        "直接发送文字描述即可生成图片。\n\n"
        "提示词技巧：\n"
        "• 描述越详细，效果越好\n"
        "• 可以指定风格：水彩、油画、赛博朋克、像素风等\n"
        "• 可以指定主体、场景、光线、构图等\n\n"
        "命令列表：\n"
        "/start - 开始使用\n"
        "/model - 切换 AI 模型\n"
        "/size - 切换图片尺寸\n"
        "/enhance - 开关提示词增强\n"
        "/settings - 查看当前设置\n"
        "/help - 显示此帮助\n\n"
        "费用说明：\n"
        "本机器人完全免费，基于 Pollinations.ai 开源免费 API。\n"
        "匿名用户约每 15 秒可生成一张图。"
    )
    await update.message.reply_text(help_text)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /model - 显示模型选择按钮 """
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    keyboard = []
    for model_id, model_name in AVAILABLE_MODELS.items():
        current = " ✅" if model_id == settings.model else ""
        keyboard.append([InlineKeyboardButton(f"{model_name}{current}", callback_data=f"model:{model_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("选择 AI 模型：", reply_markup=reply_markup)


async def size_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /size - 显示尺寸选择按钮 """
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    keyboard = []
    for size_id, size_name in AVAILABLE_SIZES.items():
        current = " ✅" if size_id == settings.size else ""
        keyboard.append([InlineKeyboardButton(f"{size_name}{current}", callback_data=f"size:{size_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("选择图片尺寸：", reply_markup=reply_markup)


async def enhance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /enhance - 切换提示词增强 """
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    settings.enhance = not settings.enhance
    status = "已开启" if settings.enhance else "已关闭"
    await update.message.reply_text(f"提示词增强 {status}。\n开启后 AI 会自动优化你的描述以获得更好效果。")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /settings - 查看当前设置 """
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    model_name = AVAILABLE_MODELS.get(settings.model, settings.model)
    size_name = AVAILABLE_SIZES.get(settings.size, settings.size)
    enhance_status = "开启" if settings.enhance else "关闭"

    text = (
        "当前设置\n\n"
        f"模型：{model_name}\n"
        f"尺寸：{size_name}\n"
        f"提示词增强：{enhance_status}\n\n"
        "使用 /model 切换模型\n"
        "使用 /size 切换尺寸\n"
        "使用 /enhance 开关增强"
    )
    await update.message.reply_text(text)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理内联按钮回调"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    data = query.data
    if data.startswith("model:"):
        model_id = data.split(":", 1)[1]
        if model_id in AVAILABLE_MODELS:
            settings.model = model_id
            await query.edit_message_text(f"已切换模型为：{AVAILABLE_MODELS[model_id]}")
    elif data.startswith("size:"):
        size_id = data.split(":", 1)[1]
        if size_id in AVAILABLE_SIZES:
            settings.size = size_id
            await query.edit_message_text(f"已切换尺寸为：{AVAILABLE_SIZES[size_id]}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户发送的文字，生成图片"""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    prompt = update.message.text.strip()

    if not prompt:
        return

    # 发送"正在生成"提示，让用户知道机器人在正常工作
    status_msg = await update.message.reply_text(
        f"正在生成图片，请稍候...\n\n"
        f"提示词：{prompt}\n"
        f"模型：{AVAILABLE_MODELS.get(settings.model, settings.model)}\n"
        f"尺寸：{AVAILABLE_SIZES.get(settings.size, settings.size)}"
    )

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        image_data = await generate_image(prompt, settings)

        photo = io.BytesIO(image_data)
        photo.name = "generated.jpg"

        caption = (
            f"生成完成！\n\n"
            f"提示词：{prompt}\n"
            f"模型：{settings.model}\n"
            f"尺寸：{settings.size}"
        )

        await update.message.reply_photo(photo=photo, caption=caption)
        await status_msg.delete()

    except asyncio.TimeoutError:
        await status_msg.edit_text("生成超时，请稍后重试。可能是服务器繁忙，建议尝试切换模型或减小尺寸。")
    except Exception as e:
        logger.error(f"生成图片失败: {e}")
        await status_msg.edit_text(f"生成失败：{str(e)[:200]}\n\n请稍后重试，或尝试切换模型。")


# ============ 创建 Application（模块级别，gunicorn 可引用） ============
def create_application():
    """创建并配置 Telegram Application"""
    request_kwargs = {}
    if PROXY_URL:
        request_kwargs["proxy"] = PROXY_URL
        request_kwargs["httpx_kwargs"] = {"verify": False}

    request = HTTPXRequest(**request_kwargs)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("size", size_command))
    app.add_handler(CommandHandler("enhance", enhance_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


# 全局 Application 实例
application = create_application()
_app_initialized = False


async def _process_update_async(update):
    """异步处理更新，包含延迟初始化"""
    global _app_initialized
    if not _app_initialized:
        try:
            await application.initialize()
            _app_initialized = True
            logger.info("Application 初始化成功")
        except Exception as e:
            logger.error(f"Application 初始化失败: {e}")
            raise
    await application.process_update(update)


# ============ Flask Web 应用（模块级别，gunicorn 用 bot:flask_app 引用） ============
flask_app = Flask(__name__)


@flask_app.route("/", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "bot": "running"})


@flask_app.route("/test", methods=["GET"])
def test_connection():
    """测试 Railway 服务器到 Telegram API 的连接"""
    import urllib.request
    import json as json_lib
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json_lib.loads(resp.read())
        return jsonify({"telegram_api": "ok", "bot_name": data["result"]["first_name"]})
    except Exception as e:
        return jsonify({"telegram_api": "error", "error": str(e)[:200]}), 500


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    """接收 Telegram Webhook 更新"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(_process_update_async(update))
    except Exception as e:
        logger.error(f"处理 webhook 更新失败: {e}")
    # 始终返回 200，避免 Telegram 重复推送
    return jsonify({"status": "ok"})


def setup_webhook():
    """设置 Telegram Webhook（云端部署时调用）"""
    if not WEBHOOK_URL:
        return

    import urllib.request
    import json as json_lib

    webhook_url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
    set_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"

    try:
        if PROXY_URL:
            proxy_handler = urllib.request.ProxyHandler({"http": PROXY_URL, "https": PROXY_URL})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

        req = urllib.request.Request(set_url)
        resp = urllib.request.urlopen(req, timeout=30)
        result = json_lib.loads(resp.read())
        if result.get("ok"):
            logger.info(f"Webhook 设置成功: {webhook_url}")
            print(f"Webhook 设置成功: {webhook_url}")
        else:
            logger.error(f"Webhook 设置失败: {result}")
    except Exception as e:
        logger.error(f"设置 Webhook 时出错: {e}")


# 云端部署时，模块加载即设置 Webhook
if WEBHOOK_URL:
    setup_webhook()
    print("=" * 50)
    print("Telegram AI 文生图机器人 - Webhook 模式")
    print(f"Webhook URL: {WEBHOOK_URL.rstrip('/')}/webhook")
    print("基于 Pollinations.ai 免费 API，完全免费")
    print("=" * 50)


# ============ 主入口（本地运行用） ============
if __name__ == "__main__":
    if WEBHOOK_URL:
        # Webhook 模式：用 Flask 开发服务器启动（生产用 gunicorn）
        print(f"监听端口: {PORT}")
        flask_app.run(host="0.0.0.0", port=PORT)
    else:
        # 长轮询模式（本地开发/测试用）
        print("=" * 50)
        print("Telegram AI 文生图机器人 - 长轮询模式")
        print(f"模型：{', '.join(AVAILABLE_MODELS.keys())}")
        print("基于 Pollinations.ai 免费 API，完全免费")
        print("=" * 50)
        if PROXY_URL:
            print(f"使用代理: {PROXY_URL}")
        print("机器人已启动，按 Ctrl+C 停止")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
