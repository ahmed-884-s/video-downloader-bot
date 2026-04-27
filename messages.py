"""Message event handlers - protection logic"""

import asyncio
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

from utils.database import (
    get_settings, get_lang, update_setting,
    check_filter, get_note,
    check_blacklist, is_locked,
    track_flood, reset_flood,
    is_gbanned, gban_user
)
from utils.helpers import (
    is_admin, is_owner, mention, contains_link, contains_telegram_link
)
from locales.strings import get as _

# ── Pending captchas: {(chat_id, user_id): {"msg_id": int, "answer": int}} ──
PENDING_CAPTCHA: dict = {}


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central message processor"""
    msg  = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not user or not chat or chat.type == "private":
        return
    if user.is_bot:
        return

    lang     = get_lang(chat.id)
    settings = get_settings(chat.id)

    # ── GBan check ──────────────────────────────────────────────────────────
    reason = is_gbanned(user.id)
    if reason:
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await msg.reply_text(_("gbanned_entry", lang, user=mention(user)), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
        return

    # Skip admins for most checks
    user_is_admin = await is_admin(chat, user.id, context)

    # ── Note retrieval via #name ─────────────────────────────────────────────
    if msg.text and msg.text.startswith("#"):
        note_name = msg.text[1:].split()[0].lower()
        content = get_note(chat.id, note_name)
        if content:
            await msg.reply_text(content, parse_mode=ParseMode.MARKDOWN)
            return

    # ── Filter check ─────────────────────────────────────────────────────────
    if msg.text:
        response = check_filter(chat.id, msg.text)
        if response:
            await msg.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    if user_is_admin:
        return

    # ── Blacklist ────────────────────────────────────────────────────────────
    if msg.text:
        found = check_blacklist(chat.id, msg.text)
        if found:
            try:
                await msg.delete()
                notice = await context.bot.send_message(
                    chat.id,
                    f"🚫 {mention(user)}: " + (f"تم حذف رسالتك (كلمة محظورة: `{found}`)" if lang=="ar" else f"Your message was deleted (blacklisted word: `{found}`)"),
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(5)
                try: await notice.delete()
                except: pass
            except Exception:
                pass
            return

    # ── Lock checks ──────────────────────────────────────────────────────────
    deleted = await _check_locks(msg, chat, user, lang, context)
    if deleted:
        return

    # ── Anti-link ────────────────────────────────────────────────────────────
    if settings.get("antilink") and msg.text:
        if contains_telegram_link(msg.text):
            try:
                await msg.delete()
                notice = await context.bot.send_message(
                    chat.id,
                    _("antilink_triggered", lang, user=mention(user)),
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(5)
                try: await notice.delete()
                except: pass
            except Exception:
                pass
            return

    # ── Anti-flood ───────────────────────────────────────────────────────────
    if settings.get("antiflood"):
        limit = settings.get("flood_limit", 5)
        count = track_flood(chat.id, user.id)
        if count >= limit:
            reset_flood(chat.id, user.id)
            try:
                await context.bot.restrict_chat_member(
                    chat.id, user.id,
                    ChatPermissions(can_send_messages=False),
                )
                notice = await context.bot.send_message(
                    chat.id,
                    _("antiflood_triggered", lang, user=mention(user), count=count),
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(10)
                try: await notice.delete()
                except: pass
                # Auto-unmute after 60s
                await asyncio.sleep(50)
                await context.bot.restrict_chat_member(
                    chat.id, user.id,
                    ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                    can_send_other_messages=True, can_add_web_page_previews=True)
                )
            except Exception:
                pass


async def _check_locks(msg, chat, user, lang, context) -> bool:
    """Check message against group locks. Returns True if deleted."""
    if not msg:
        return False

    lock_map = {
        "text":     lambda m: bool(m.text) and not m.entities,
        "photo":    lambda m: bool(m.photo),
        "video":    lambda m: bool(m.video),
        "audio":    lambda m: bool(m.audio),
        "voice":    lambda m: bool(m.voice),
        "document": lambda m: bool(m.document),
        "sticker":  lambda m: bool(m.sticker),
        "gif":      lambda m: bool(m.animation),
        "forward":  lambda m: bool(m.forward_date),
        "game":     lambda m: bool(m.game),
    }

    for ltype, checker in lock_map.items():
        if is_locked(chat.id, ltype) and checker(msg):
            try:
                await msg.delete()
                notice = await context.bot.send_message(
                    chat.id,
                    _("lock_deleted", lang, lock_type=ltype),
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(3)
                try: await notice.delete()
                except: pass
                return True
            except Exception:
                pass
    return False


# ── New member handler ────────────────────────────────────────────────────────

async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return
    chat     = result.chat
    new_mem  = result.new_chat_member
    old_mem  = result.old_chat_member

    if not (old_mem.status in ("left", "kicked") and new_mem.status == "member"):
        # Handle leave
        if old_mem.status == "member" and new_mem.status in ("left", "kicked"):
            await _handle_leave(chat, new_mem.user, context)
        return

    user     = new_mem.user
    lang     = get_lang(chat.id)
    settings = get_settings(chat.id)

    # ── GBan check on join ───────────────────────────────────────────────────
    reason = is_gbanned(user.id)
    if reason:
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.send_message(
                chat.id,
                _("gbanned_entry", lang, user=mention(user)),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
        return

    # ── Captcha ──────────────────────────────────────────────────────────────
    if settings.get("captcha"):
        await _send_captcha(chat, user, lang, context)
        return

    # ── Welcome ──────────────────────────────────────────────────────────────
    if settings.get("welcome"):
        await _send_welcome(chat, user, lang, settings, context)


async def _handle_leave(chat, user, context):
    lang     = get_lang(chat.id)
    settings = get_settings(chat.id)
    if not settings.get("farewell"):
        return
    farewell_msg = settings.get("farewell_msg") or _("default_farewell", lang)
    text = farewell_msg.replace("{user}", mention(user)).replace("{chat}", chat.title or "")
    try:
        await context.bot.send_message(chat.id, text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass


async def _send_welcome(chat, user, lang, settings, context):
    welcome_msg = settings.get("welcome_msg") or _("default_welcome", lang)
    text = welcome_msg.replace("{user}", mention(user)).replace("{chat}", chat.title or "")
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📋 " + ("القوانين" if lang=="ar" else "Rules"),
            callback_data=f"rules:{chat.id}"
        )
    ]])
    try:
        await context.bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass


async def _send_captcha(chat, user, lang, context):
    """Send math captcha to new member"""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    answer = a + b
    # Generate wrong answers
    wrong = set()
    while len(wrong) < 3:
        w = random.randint(2, 18)
        if w != answer:
            wrong.add(w)

    options = list(wrong) + [answer]
    random.shuffle(options)

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(str(opt), callback_data=f"captcha:{user.id}:{opt}:{answer}")
        for opt in options
    ]])

    # Restrict until verified
    try:
        await context.bot.restrict_chat_member(
            chat.id, user.id,
            ChatPermissions(can_send_messages=False)
        )
    except Exception:
        pass

    timeout = 60
    text = _("captcha_msg", lang, user=mention(user), timeout=timeout)
    try:
        sent = await context.bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        PENDING_CAPTCHA[(chat.id, user.id)] = {
            "msg_id": sent.message_id,
            "answer": answer,
            "timeout": timeout
        }
        # Schedule timeout
        asyncio.create_task(_captcha_timeout(chat, user, lang, sent.message_id, timeout, context))
    except Exception:
        pass


async def _captcha_timeout(chat, user, lang, msg_id, timeout, context):
    await asyncio.sleep(timeout)
    key = (chat.id, user.id)
    if key in PENDING_CAPTCHA:
        del PENDING_CAPTCHA[key]
        try:
            await context.bot.delete_message(chat.id, msg_id)
        except Exception:
            pass
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.send_message(
                chat.id,
                _("captcha_failed", lang, user=mention(user)),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass


# ── Callback handler ──────────────────────────────────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data  = query.data
    chat  = query.message.chat
    user  = query.from_user
    lang  = get_lang(chat.id) if chat.type != "private" else "ar"

    # ── Captcha answer ───────────────────────────────────────────────────────
    if data.startswith("captcha:"):
        _, uid, chosen, correct = data.split(":")
        uid = int(uid)
        if user.id != uid:
            await query.answer("❌ " + ("هذا ليس لك!" if lang=="ar" else "Not for you!"), show_alert=True)
            return
        key = (chat.id, uid)
        if key not in PENDING_CAPTCHA:
            return
        if int(chosen) == int(correct):
            del PENDING_CAPTCHA[key]
            try:
                await context.bot.restrict_chat_member(
                    chat.id, uid,
                    ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                    can_send_other_messages=True, can_add_web_page_previews=True)
                )
                await query.edit_message_text(
                    _("captcha_passed", lang, user=mention(user)),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass
        else:
            await query.answer(_("captcha_wrong", lang), show_alert=True)
        return

    # ── Only admins can use the rest ─────────────────────────────────────────
    if not await is_admin(chat, user.id, context):
        await query.answer("❌ " + ("ليس لديك صلاحية" if lang=="ar" else "No permission"), show_alert=True)
        return

    # ── Settings toggle ──────────────────────────────────────────────────────
    if data.startswith("toggle:"):
        key = data.split(":")[1]
        from utils.database import get_settings as gs
        settings = gs(chat.id)
        new_val = 0 if settings.get(key, 0) else 1
        update_setting(chat.id, key, new_val)
        settings = gs(chat.id)
        from utils.helpers import settings_keyboard
        kb = settings_keyboard(settings, lang)
        try:
            await query.edit_message_reply_markup(reply_markup=kb)
        except Exception:
            pass
        return

    # ── Language change ──────────────────────────────────────────────────────
    if data.startswith("lang:"):
        new_lang = data.split(":")[1]
        update_setting(chat.id, "lang", new_lang)
        from utils.database import get_settings as gs
        settings = gs(chat.id)
        from utils.helpers import settings_keyboard
        kb = settings_keyboard(settings, new_lang)
        label = "تم تغيير اللغة إلى العربية ✅" if new_lang=="ar" else "Language changed to English ✅"
        try:
            await query.edit_message_text(label, reply_markup=kb)
        except Exception:
            pass
        return

    # ── Rules inline ─────────────────────────────────────────────────────────
    if data.startswith("rules:"):
        cid = int(data.split(":")[1])
        from utils.database import get_settings as gs
        s = gs(cid)
        rules = s.get("rules", "")
        text = rules if rules else _("no_rules", lang)
        await query.answer(text[:200], show_alert=True)
        return

    # ── Close settings ────────────────────────────────────────────────────────
    if data == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── PM Language ──────────────────────────────────────────────────────────
    if data.startswith("lang_pm:"):
        new_lang = data.split(":")[1]
        from locales.strings import get as _s
        await query.edit_message_text(_s("start_pm", new_lang), parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ أضفني | Add me", url=f"https://t.me/{context.bot.username}?startgroup=true")
            ],[
                InlineKeyboardButton("🇸🇦 عربي", callback_data="lang_pm:ar"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_pm:en"),
            ]])
        )
        return
