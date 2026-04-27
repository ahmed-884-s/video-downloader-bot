"""All command handlers"""

import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, Application
from telegram.constants import ParseMode, ChatMemberStatus

from utils.database import (
    get_settings, update_setting, get_lang,
    add_warn, remove_warn, get_warns, clear_warns,
    add_filter, remove_filter, get_filters,
    save_note, delete_note, get_note, get_notes,
    add_blacklist, remove_blacklist, get_blacklist,
    add_lock, remove_lock, get_locks,
    gban_user, ungban_user, is_gbanned, get_gbans
)
from utils.helpers import (
    is_owner, is_admin, parse_time, format_duration,
    mention, resolve_user, settings_keyboard
)
from locales.strings import get as _

OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# ── Decorators ─────────────────────────────────────────────────────────────

def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        user = update.effective_user
        if chat.type == "private":
            await update.message.reply_text("⚠️ هذا الأمر للمجموعات فقط | This command is for groups only.")
            return
        lang = get_lang(chat.id)
        if not await is_admin(chat, user.id, context):
            await update.message.reply_text(_(  "no_permission", lang), parse_mode=ParseMode.MARKDOWN)
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper


def owner_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not is_owner(user.id):
            await update.message.reply_text("❌ Owner only command.")
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper

# ── /start ──────────────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ أضفني للمجموعة | Add me", url=f"https://t.me/{context.bot.username}?startgroup=true")
        ],[
            InlineKeyboardButton("🌐 عربي", callback_data="lang_pm:ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_pm:en"),
        ]])
        await update.message.reply_text(_("start_pm", "ar"), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        lang = get_lang(chat.id)
        await update.message.reply_text(
            "🛡️ Guardian Bot " + ("جاهز للحماية!" if lang=="ar" else "is ready to protect!"),
            parse_mode=ParseMode.MARKDOWN
        )

# ── /help ───────────────────────────────────────────────────────────────────

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id) if chat.type != "private" else "ar"
    await update.message.reply_text(_("help_text", lang), parse_mode=ParseMode.MARKDOWN)

# ── /lang ───────────────────────────────────────────────────────────────────

@admin_required
async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang:ar"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="lang:en"),
    ]])
    await update.message.reply_text(
        f"🌐 {'اختر لغة البوت' if lang=='ar' else 'Choose bot language'}:",
        reply_markup=kb
    )

# ── /settings ───────────────────────────────────────────────────────────────

@admin_required
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    settings = get_settings(chat.id)
    lang = settings.get("lang", "ar")
    kb = settings_keyboard(settings, lang)
    await update.message.reply_text(_("settings_panel", lang), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ── /warn ───────────────────────────────────────────────────────────────────

@admin_required
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, reason = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang), parse_mode=ParseMode.MARKDOWN)
        return
    if await is_admin(chat, target.id, context):
        await update.message.reply_text(_("cant_action_admin", lang), parse_mode=ParseMode.MARKDOWN)
        return
    reason = reason or ("بدون سبب" if lang == "ar" else "No reason")
    settings = get_settings(chat.id)
    max_warns = settings.get("warn_limit", 3)
    count = add_warn(chat.id, target.id, reason)
    if count >= max_warns:
        action = settings.get("warn_action", "ban")
        try:
            if action == "ban":
                await context.bot.ban_chat_member(chat.id, target.id)
            elif action == "mute":
                from telegram import ChatPermissions
                await context.bot.restrict_chat_member(chat.id, target.id, ChatPermissions(can_send_messages=False))
        except Exception:
            pass
        clear_warns(chat.id, target.id)
        await update.message.reply_text(
            _("warn_banned", lang, user=mention(target), max=max_warns),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            _("warned", lang, user=mention(target), reason=reason, count=count, max=max_warns),
            parse_mode=ParseMode.MARKDOWN
        )

@admin_required
async def unwarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    removed = remove_warn(chat.id, target.id)
    msg = _("unwarned", lang, user=mention(target)) if removed else _("no_warns", lang, user=mention(target))
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def warns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        target = update.effective_user
    warns = get_warns(chat.id, target.id)
    if not warns:
        await update.message.reply_text(_("no_warns", lang, user=mention(target)), parse_mode=ParseMode.MARKDOWN)
        return
    settings = get_settings(chat.id)
    items = "\n".join([f"  {i+1}. {w['reason']}" for i, w in enumerate(warns)])
    await update.message.reply_text(
        _("warns_list", lang, user=mention(target), list=items, count=len(warns), max=settings.get("warn_limit", 3)),
        parse_mode=ParseMode.MARKDOWN
    )

# ── /ban /unban ──────────────────────────────────────────────────────────────

@admin_required
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, reason = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    if await is_admin(chat, target.id, context):
        await update.message.reply_text(_("cant_action_admin", lang)); return
    reason = reason or ("بدون سبب" if lang == "ar" else "No reason")
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(_("banned", lang, user=mention(target), reason=reason), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(_("bot_no_permission", lang))

@admin_required
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    try:
        await context.bot.unban_chat_member(chat.id, target.id, only_if_banned=True)
        await update.message.reply_text(_("unbanned", lang, user=mention(target)), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

# ── /mute /unmute ────────────────────────────────────────────────────────────

@admin_required
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import ChatPermissions
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, reason = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    if await is_admin(chat, target.id, context):
        await update.message.reply_text(_("cant_action_admin", lang)); return

    duration_str = context.args[0] if context.args else None
    duration_secs = parse_time(duration_str) if duration_str else None
    reason = reason or ("بدون سبب" if lang == "ar" else "No reason")

    from datetime import datetime, timedelta, timezone
    until = datetime.now(timezone.utc) + timedelta(seconds=duration_secs) if duration_secs else None
    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            ChatPermissions(can_send_messages=False),
            until_date=until
        )
        dur_text = format_duration(duration_secs) if duration_secs else ("دائم" if lang=="ar" else "Permanent")
        await update.message.reply_text(
            _("muted", lang, user=mention(target), duration=dur_text, reason=reason),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

@admin_required
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import ChatPermissions
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(_("unmuted", lang, user=mention(target)), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

# ── /kick ────────────────────────────────────────────────────────────────────

@admin_required
async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, reason = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    if await is_admin(chat, target.id, context):
        await update.message.reply_text(_("cant_action_admin", lang)); return
    reason = reason or ("بدون سبب" if lang == "ar" else "No reason")
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await context.bot.unban_chat_member(chat.id, target.id)
        await update.message.reply_text(_("kicked", lang, user=mention(target), reason=reason), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

# ── /purge ───────────────────────────────────────────────────────────────────

@admin_required
async def purge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    if not msg.reply_to_message:
        await msg.reply_text("❌ رد على أول رسالة تريد حذفها | Reply to the first message to delete.")
        return
    start_id = msg.reply_to_message.message_id
    end_id   = msg.message_id
    deleted  = 0
    for mid in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(chat.id, mid)
            deleted += 1
        except Exception:
            pass
    notice = await msg.reply_text(f"🗑️ {'حُذفت' if lang=='ar' else 'Deleted'} {deleted} {'رسالة' if lang=='ar' else 'messages'}.")
    import asyncio; await asyncio.sleep(3)
    try: await notice.delete()
    except: pass

# ── /promote /demote ─────────────────────────────────────────────────────────

@admin_required
async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    try:
        await context.bot.promote_chat_member(
            chat.id, target.id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_manage_chat=True,
            can_invite_users=True
        )
        await update.message.reply_text(
            f"👑 {'تمت ترقية' if lang=='ar' else 'Promoted'} {mention(target)}!",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

@admin_required
async def demote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text(_("reply_to_user", lang)); return
    try:
        await context.bot.promote_chat_member(chat.id, target.id, can_manage_chat=False)
        await update.message.reply_text(
            f"🚫 {'تم إلغاء إشراف' if lang=='ar' else 'Demoted'} {mention(target)}.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

# ── Filters ──────────────────────────────────────────────────────────────────

@admin_required
async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    if len(context.args) < 2:
        await msg.reply_text("❌ الاستخدام: `/filter كلمة الرد`", parse_mode=ParseMode.MARKDOWN); return
    keyword  = context.args[0]
    response = " ".join(context.args[1:])
    add_filter(chat.id, keyword, response)
    await msg.reply_text(_("filter_added", lang, keyword=keyword), parse_mode=ParseMode.MARKDOWN)

@admin_required
async def unfilter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        await update.message.reply_text("❌ اذكر الكلمة | Specify the keyword"); return
    remove_filter(chat.id, context.args[0])
    await update.message.reply_text(_("filter_removed", lang, keyword=context.args[0]), parse_mode=ParseMode.MARKDOWN)

async def filters_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    f = get_filters(chat.id)
    if not f:
        await update.message.reply_text(_("no_filters", lang)); return
    lines = "\n".join([f"• `{x['keyword']}` → {x['response']}" for x in f])
    header = "📋 **الفلاتر الحالية:**\n" if lang=="ar" else "📋 **Current filters:**\n"
    await update.message.reply_text(header + lines, parse_mode=ParseMode.MARKDOWN)

# ── Notes ─────────────────────────────────────────────────────────────────────

@admin_required
async def note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if len(context.args) < 2:
        await update.message.reply_text("❌ الاستخدام: `/note اسم المحتوى`", parse_mode=ParseMode.MARKDOWN); return
    name    = context.args[0]
    content = " ".join(context.args[1:])
    save_note(chat.id, name, content)
    await update.message.reply_text(_("note_added", lang, name=name), parse_mode=ParseMode.MARKDOWN)

@admin_required
async def delnote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        await update.message.reply_text("❌ اذكر الاسم | Specify note name"); return
    delete_note(chat.id, context.args[0])
    await update.message.reply_text(_("note_removed", lang, name=context.args[0]), parse_mode=ParseMode.MARKDOWN)

async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    notes = get_notes(chat.id)
    if not notes:
        await update.message.reply_text(_("no_notes", lang)); return
    lines = "\n".join([f"• `#{n}`" for n in notes])
    header = "📋 **الملاحظات المحفوظة:**\n" if lang=="ar" else "📋 **Saved notes:**\n"
    await update.message.reply_text(header + lines, parse_mode=ParseMode.MARKDOWN)

# ── Blacklist ─────────────────────────────────────────────────────────────────

@admin_required
async def blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        await update.message.reply_text("❌ اذكر الكلمة | Specify a word"); return
    word = " ".join(context.args).lower()
    add_blacklist(chat.id, word)
    await update.message.reply_text(
        f"✅ تمت إضافة `{word}` للقائمة السوداء." if lang=="ar" else f"✅ `{word}` added to blacklist.",
        parse_mode=ParseMode.MARKDOWN
    )

@admin_required
async def unblacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        await update.message.reply_text("❌ اذكر الكلمة"); return
    word = " ".join(context.args).lower()
    remove_blacklist(chat.id, word)
    await update.message.reply_text(
        f"✅ تمت إزالة `{word}` من القائمة السوداء." if lang=="ar" else f"✅ `{word}` removed from blacklist.",
        parse_mode=ParseMode.MARKDOWN
    )

async def blacklists_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    words = get_blacklist(chat.id)
    if not words:
        await update.message.reply_text("📋 القائمة السوداء فارغة." if lang=="ar" else "📋 Blacklist is empty."); return
    lines = "\n".join([f"• `{w}`" for w in words])
    header = "📋 **الكلمات المحظورة:**\n" if lang=="ar" else "📋 **Blacklisted words:**\n"
    await update.message.reply_text(header + lines, parse_mode=ParseMode.MARKDOWN)

# ── Protection toggles ────────────────────────────────────────────────────────

async def _toggle_protection(update, context, key):
    chat = update.effective_chat
    if chat.type == "private":
        return
    lang = get_lang(chat.id)
    if not await is_admin(chat, update.effective_user.id, context):
        await update.message.reply_text(_("no_permission", lang)); return
    settings = get_settings(chat.id)
    new_val = 0 if settings.get(key, 0) else 1
    update_setting(chat.id, key, new_val)
    status = ("✅ مفعّل" if lang=="ar" else "✅ Enabled") if new_val else ("❌ معطّل" if lang=="ar" else "❌ Disabled")
    labels = {"antispam":"مكافحة السبام/Anti-Spam","antilink":"مكافحة الروابط/Anti-Link","antiflood":"مكافحة الفلود/Anti-Flood","captcha":"الكابتشا/Captcha"}
    await update.message.reply_text(f"🔧 {labels.get(key, key)}: {status}")

async def antispam_cmd(update, context): await _toggle_protection(update, context, "antispam")
async def antilink_cmd(update, context): await _toggle_protection(update, context, "antilink")
async def antiflood_cmd(update, context): await _toggle_protection(update, context, "antiflood")
async def captcha_cmd(update, context): await _toggle_protection(update, context, "captcha")

# ── Welcome/Farewell ──────────────────────────────────────────────────────────

async def _toggle_wf(update, context, key):
    chat = update.effective_chat
    if chat.type == "private": return
    lang = get_lang(chat.id)
    if not await is_admin(chat, update.effective_user.id, context):
        await update.message.reply_text(_("no_permission", lang)); return
    settings = get_settings(chat.id)
    new_val = 0 if settings.get(key, 1) else 1
    update_setting(chat.id, key, new_val)
    status = ("✅ مفعّل" if lang=="ar" else "✅ Enabled") if new_val else ("❌ معطّل" if lang=="ar" else "❌ Disabled")
    label = ("الترحيب" if key=="welcome" else "الوداع") if lang=="ar" else ("Welcome" if key=="welcome" else "Farewell")
    await update.message.reply_text(f"🔧 {label}: {status}")

async def welcome_cmd(update, context): await _toggle_wf(update, context, "welcome")
async def farewell_cmd(update, context): await _toggle_wf(update, context, "farewell")

@admin_required
async def setwelcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    text = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else None
    if msg.reply_to_message:
        text = msg.reply_to_message.text or text
    if not text:
        usage = "الاستخدام: /setwelcome نص الرسالة\nمتغيرات: {user} {chat}" if lang=="ar" else "Usage: /setwelcome message text\nVariables: {user} {chat}"
        await msg.reply_text(usage); return
    update_setting(chat.id, "welcome_msg", text)
    await msg.reply_text(_("welcome_set", lang))

@admin_required
async def setfarewell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    text = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else None
    if msg.reply_to_message:
        text = msg.reply_to_message.text or text
    if not text:
        await msg.reply_text("الاستخدام: /setfarewell نص\nمتغيرات: {user}" if lang=="ar" else "Usage: /setfarewell text\nVariables: {user}"); return
    update_setting(chat.id, "farewell_msg", text)
    await msg.reply_text(_("farewell_set", lang))

# ── Rules ─────────────────────────────────────────────────────────────────────

async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    settings = get_settings(chat.id)
    rules = settings.get("rules", "")
    if not rules:
        await update.message.reply_text(_("no_rules", lang)); return
    header = f"📋 **قوانين {chat.title}:**\n\n" if lang=="ar" else f"📋 **Rules of {chat.title}:**\n\n"
    await update.message.reply_text(header + rules, parse_mode=ParseMode.MARKDOWN)

@admin_required
async def setrules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    text = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else None
    if msg.reply_to_message:
        text = msg.reply_to_message.text or text
    if not text:
        await msg.reply_text("❌ أضف نص القوانين بعد الأمر | Add rules text after command"); return
    update_setting(chat.id, "rules", text)
    await msg.reply_text(_("rules_set", lang))

# ── Lock ──────────────────────────────────────────────────────────────────────

LOCK_TYPES = ["text", "media", "sticker", "gif", "url", "bots", "forward", "game", "photo", "video", "audio", "voice", "document"]

@admin_required
async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        types_str = ", ".join([f"`{t}`" for t in LOCK_TYPES])
        await update.message.reply_text(f"❌ الاستخدام: `/lock نوع`\nالأنواع: {types_str}", parse_mode=ParseMode.MARKDOWN); return
    ltype = context.args[0].lower()
    if ltype not in LOCK_TYPES:
        await update.message.reply_text(f"❌ نوع غير معروف | Unknown type: `{ltype}`", parse_mode=ParseMode.MARKDOWN); return
    add_lock(chat.id, ltype)
    await update.message.reply_text(_("locked", lang, lock_type=ltype), parse_mode=ParseMode.MARKDOWN)

@admin_required
async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if not context.args:
        await update.message.reply_text("❌ اذكر النوع | Specify type"); return
    ltype = context.args[0].lower()
    remove_lock(chat.id, ltype)
    await update.message.reply_text(_("unlocked", lang, lock_type=ltype), parse_mode=ParseMode.MARKDOWN)

async def locks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    locked = get_locks(chat.id)
    unlocked = [t for t in LOCK_TYPES if t not in locked]
    text = ("🔒 **الأقفال الحالية:**\n\n" if lang=="ar" else "🔒 **Current Locks:**\n\n")
    text += "\n".join([f"🔒 `{t}`" for t in locked]) or ("لا يوجد" if lang=="ar" else "None")
    text += "\n\n" + ("🔓 **مفتوح:**\n" if lang=="ar" else "🔓 **Unlocked:**\n")
    text += "\n".join([f"🔓 `{t}`" for t in unlocked])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ── adminlist ──────────────────────────────────────────────────────────────────

async def adminlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    if chat.type == "private":
        await update.message.reply_text("مجموعات فقط | Groups only"); return
    admins = await context.bot.get_chat_administrators(chat.id)
    lines = []
    for a in admins:
        role = ("👑 المالك" if lang=="ar" else "👑 Owner") if a.status == "creator" else ("🛡️ مشرف" if lang=="ar" else "🛡️ Admin")
        lines.append(f"{role}: [{a.user.full_name}](tg://user?id={a.user.id})")
    header = f"👥 **مشرفو {chat.title}:**\n\n" if lang=="ar" else f"👥 **Admins of {chat.title}:**\n\n"
    await update.message.reply_text(header + "\n".join(lines), parse_mode=ParseMode.MARKDOWN)

# ── /pin /unpin ───────────────────────────────────────────────────────────────

@admin_required
async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    if not msg.reply_to_message:
        await msg.reply_text("❌ رد على الرسالة التي تريد تثبيتها | Reply to the message to pin"); return
    try:
        await context.bot.pin_chat_message(chat.id, msg.reply_to_message.message_id)
        await msg.reply_text("📌 " + ("تم التثبيت!" if lang=="ar" else "Pinned!"))
    except Exception:
        await msg.reply_text(_("bot_no_permission", lang))

@admin_required
async def unpin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    try:
        await context.bot.unpin_chat_message(chat.id)
        await update.message.reply_text("📌 " + ("تم إلغاء التثبيت!" if lang=="ar" else "Unpinned!"))
    except Exception:
        await update.message.reply_text(_("bot_no_permission", lang))

# ── /id /info ─────────────────────────────────────────────────────────────────

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    text = f"👤 **User ID:** `{user.id}`\n"
    if chat.type != "private":
        text += f"💬 **Chat ID:** `{chat.id}`\n"
    if msg.reply_to_message:
        ru = msg.reply_to_message.from_user
        text += f"👤 **{ru.full_name}'s ID:** `{ru.id}`"
    await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id) if chat.type != "private" else "ar"
    msg  = update.effective_message
    target = msg.reply_to_message.from_user if msg.reply_to_message else update.effective_user
    gbanned_reason = is_gbanned(target.id)
    gban_status = f"\n🌐 **GBan:** {'نعم - ' if lang=='ar' else 'Yes - '}{gbanned_reason}" if gbanned_reason else ""
    text = (
        f"ℹ️ **معلومات المستخدم:**\n\n" if lang=="ar" else f"ℹ️ **User Info:**\n\n"
    )
    text += (
        f"👤 **الاسم:** {target.full_name}\n"
        f"🆔 **ID:** `{target.id}`\n"
        f"📛 **يوزر:** @{target.username or ('لا يوجد' if lang=='ar' else 'None')}\n"
        f"🤖 **بوت:** {'نعم' if target.is_bot else 'لا'}\n" if lang=="ar" else
        f"👤 **Name:** {target.full_name}\n"
        f"🆔 **ID:** `{target.id}`\n"
        f"📛 **Username:** @{target.username or 'None'}\n"
        f"🤖 **Bot:** {'Yes' if target.is_bot else 'No'}\n"
    )
    text += gban_status
    await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ── /report ───────────────────────────────────────────────────────────────────

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    lang = get_lang(chat.id)
    msg = update.effective_message
    if not msg.reply_to_message:
        await msg.reply_text("❌ رد على الرسالة المخالفة | Reply to the violating message"); return
    admins = await context.bot.get_chat_administrators(chat.id)
    mentions = " ".join([f"[{a.user.full_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot])
    reporter = mention(update.effective_user)
    text = (
        f"🚨 **إبلاغ!**\n{reporter} أبلغ عن رسالة.\n\n👮 المشرفون: {mentions}"
        if lang=="ar" else
        f"🚨 **Report!**\n{reporter} reported a message.\n\n👮 Admins: {mentions}"
    )
    await msg.reply_to_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ── GBan (owner only) ─────────────────────────────────────────────────────────

@owner_required
async def gban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target, reason = await resolve_user(update, context)
    if not target:
        await update.message.reply_text("❌ اذكر مستخدم | Specify a user"); return
    reason = reason or "No reason"
    gban_user(target.id, reason)
    await update.message.reply_text(_("gbanned", "ar", user=mention(target), reason=reason), parse_mode=ParseMode.MARKDOWN)

@owner_required
async def ungban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target, _ = await resolve_user(update, context)
    if not target:
        await update.message.reply_text("❌ اذكر مستخدم"); return
    ungban_user(target.id)
    await update.message.reply_text(_("ungbanned", "ar", user=mention(target)), parse_mode=ParseMode.MARKDOWN)

@owner_required
async def gbans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bans = get_gbans()
    if not bans:
        await update.message.reply_text("✅ لا يوجد محظورون عالمياً | No global bans."); return
    lines = [f"• `{b['user_id']}` - {b['reason']}" for b in bans[:20]]
    await update.message.reply_text(
        f"🌐 **قائمة الحظر العالمي ({len(bans)}):**\n" + "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN
    )

# ── Register all ──────────────────────────────────────────────────────────────

def register_commands(app: Application):
    cmds = [
        ("start", start_cmd), ("help", help_cmd), ("lang", lang_cmd), ("settings", settings_cmd),
        ("warn", warn_cmd), ("unwarn", unwarn_cmd), ("warns", warns_cmd),
        ("ban", ban_cmd), ("unban", unban_cmd),
        ("mute", mute_cmd), ("unmute", unmute_cmd),
        ("kick", kick_cmd), ("purge", purge_cmd),
        ("promote", promote_cmd), ("demote", demote_cmd),
        ("filter", filter_cmd), ("unfilter", unfilter_cmd), ("filters", filters_cmd),
        ("note", note_cmd), ("delnote", delnote_cmd), ("notes", notes_cmd),
        ("blacklist", blacklist_cmd), ("unblacklist", unblacklist_cmd), ("blacklists", blacklists_cmd),
        ("antispam", antispam_cmd), ("antilink", antilink_cmd), ("antiflood", antiflood_cmd), ("captcha", captcha_cmd),
        ("lock", lock_cmd), ("unlock", unlock_cmd), ("locks", locks_cmd),
        ("welcome", welcome_cmd), ("farewell", farewell_cmd),
        ("setwelcome", setwelcome_cmd), ("setfarewell", setfarewell_cmd),
        ("rules", rules_cmd), ("setrules", setrules_cmd),
        ("adminlist", adminlist_cmd),
        ("pin", pin_cmd), ("unpin", unpin_cmd),
        ("id", id_cmd), ("info", info_cmd), ("report", report_cmd),
        ("gban", gban_cmd), ("ungban", ungban_cmd), ("gbans", gbans_cmd),
    ]
    for name, handler in cmds:
        app.add_handler(CommandHandler(name, handler))
