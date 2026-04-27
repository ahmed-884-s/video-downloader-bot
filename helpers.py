"""Utility helpers"""

import re
import os
from datetime import timedelta
from telegram import Update, Chat, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
URL_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|@\w+\.(com|net|org|io|me|ru|ua|tk))",
    re.IGNORECASE
)
TELEGRAM_LINK = re.compile(r"(t\.me/|telegram\.me/|@\w+)", re.IGNORECASE)


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def is_admin(chat: Chat, user_id: int, context) -> bool:
    if is_owner(user_id):
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


def parse_time(time_str: str) -> int | None:
    """Parse '10m', '2h', '1d' → seconds"""
    m = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    return val * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def format_duration(seconds: int) -> str:
    td = timedelta(seconds=seconds)
    parts = []
    if td.days:
        parts.append(f"{td.days}d")
    h, r = divmod(td.seconds, 3600)
    m, s = divmod(r, 60)
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts) or "0s"


def mention(user: User) -> str:
    name = user.full_name or str(user.id)
    return f"[{name}](tg://user?id={user.id})"


def contains_link(text: str) -> bool:
    return bool(URL_PATTERN.search(text))


def contains_telegram_link(text: str) -> bool:
    return bool(TELEGRAM_LINK.search(text))


async def resolve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get target user from reply or args"""
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None
    if context.args:
        target = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
        try:
            uid = int(target.lstrip("@"))
            user = await context.bot.get_chat(uid)
            return user, reason
        except ValueError:
            try:
                user = await context.bot.get_chat(target)
                return user, reason
            except Exception:
                return None, None
        except Exception:
            return None, None
    return None, None


def settings_keyboard(settings: dict, lang: str) -> InlineKeyboardMarkup:
    def btn(label_ar, label_en, key, val):
        icon = "✅" if val else "❌"
        label = f"{icon} {'تفعيل' if lang=='ar' else 'Enable'}" if not val else f"{icon} {'إيقاف' if lang=='ar' else 'Disable'}"
        display = label_ar if lang == "ar" else label_en
        return InlineKeyboardButton(f"{display}: {label}", callback_data=f"toggle:{key}")

    keyboard = [
        [btn("مكافحة السبام", "Anti-Spam",   "antispam",   settings["antispam"])],
        [btn("مكافحة الروابط","Anti-Link",   "antilink",   settings["antilink"])],
        [btn("مكافحة الفلود", "Anti-Flood",  "antiflood",  settings["antiflood"])],
        [btn("كابتشا",        "Captcha",     "captcha",    settings["captcha"])],
        [btn("رسالة الترحيب", "Welcome Msg", "welcome",    settings["welcome"])],
        [btn("رسالة الوداع",  "Farewell Msg","farewell",   settings["farewell"])],
        [InlineKeyboardButton(
            f"🌐 {'العربية' if lang=='en' else 'English'}",
            callback_data=f"lang:{'en' if lang=='ar' else 'ar'}"
        )],
        [InlineKeyboardButton("❌ " + ("إغلاق" if lang=="ar" else "Close"), callback_data="close")],
    ]
    return InlineKeyboardMarkup(keyboard)
