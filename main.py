#!/usr/bin/env python3
"""
Guardian Bot - Professional Telegram Group Protection Bot
Supports Arabic & English | Built for Railway deployment
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ChatMemberHandler, CallbackQueryHandler, filters
)

from handlers.commands import register_commands
from handlers.messages import (
    message_handler, new_member_handler, callback_handler
)
from utils.database import init_db

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GuardianBot")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.critical("❌ BOT_TOKEN not set in environment variables!")
        return

    init_db()
    logger.info("✅ Database initialized")

    app = Application.builder().token(token).build()
    register_commands(app)

    app.add_handler(ChatMemberHandler(new_member_handler, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))

    logger.info("🛡️  Guardian Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
