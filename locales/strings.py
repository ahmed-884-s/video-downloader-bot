"""Bilingual strings - Arabic & English"""

STRINGS = {
    # ─── General ────────────────────────────────────────────────
    "start_pm": {
        "ar": (
            "👋 **أهلاً بك في Guardian Bot!**\n\n"
            "🛡️ أنا بوت حماية احترافي للمجموعات\n\n"
            "**مميزاتي:**\n"
            "• 🚫 حماية من السبام والفلود\n"
            "• 🔗 حظر الروابط والتطبيقات\n"
            "• ⚠️ نظام تحذيرات متكامل\n"
            "• 🤖 كابتشا للأعضاء الجدد\n"
            "• 🔒 قفل المجموعة\n"
            "• 👋 رسائل ترحيب/وداع\n"
            "• 📌 ملاحظات وفلاتر\n"
            "• 🌐 دعم العربي والإنجليزي\n\n"
            "أضفني لمجموعتك كمشرف وابدأ الحماية! ✅"
        ),
        "en": (
            "👋 **Welcome to Guardian Bot!**\n\n"
            "🛡️ I'm a professional group protection bot\n\n"
            "**Features:**\n"
            "• 🚫 Anti-spam & Anti-flood\n"
            "• 🔗 Anti-link & Anti-bot\n"
            "• ⚠️ Full warning system\n"
            "• 🤖 Captcha for new members\n"
            "• 🔒 Group locking\n"
            "• 👋 Welcome/farewell messages\n"
            "• 📌 Notes & Filters\n"
            "• 🌐 Arabic & English support\n\n"
            "Add me to your group as admin and start protecting! ✅"
        ),
    },
    "no_permission": {
        "ar": "❌ ليس لديك صلاحية لاستخدام هذا الأمر.",
        "en": "❌ You don't have permission to use this command.",
    },
    "bot_no_permission": {
        "ar": "❌ ليس لدي الصلاحيات الكافية لتنفيذ هذا الأمر.",
        "en": "❌ I don't have enough permissions to execute this command.",
    },
    "reply_to_user": {
        "ar": "❌ رد على رسالة مستخدم أو اذكر اليوزر.",
        "en": "❌ Reply to a user's message or mention a username.",
    },
    "cant_action_admin": {
        "ar": "❌ لا يمكنني تنفيذ هذا الإجراء على مشرف.",
        "en": "❌ I can't perform this action on an admin.",
    },
    "done": {
        "ar": "✅ تم.",
        "en": "✅ Done.",
    },
    # ─── Warn ────────────────────────────────────────────────────
    "warned": {
        "ar": "⚠️ **تحذير** للمستخدم {user}\n📝 السبب: {reason}\n🔢 التحذيرات: {count}/{max}",
        "en": "⚠️ **Warning** issued to {user}\n📝 Reason: {reason}\n🔢 Warns: {count}/{max}",
    },
    "warn_banned": {
        "ar": "🚫 تم حظر {user} بعد {max} تحذيرات.",
        "en": "🚫 {user} has been banned after {max} warnings.",
    },
    "unwarned": {
        "ar": "✅ تم إزالة آخر تحذير من {user}.",
        "en": "✅ Removed the last warning from {user}.",
    },
    "no_warns": {
        "ar": "ℹ️ {user} ليس لديه تحذيرات.",
        "en": "ℹ️ {user} has no warnings.",
    },
    "warns_list": {
        "ar": "📋 **تحذيرات** {user}:\n{list}\nالإجمالي: {count}/{max}",
        "en": "📋 **Warnings** for {user}:\n{list}\nTotal: {count}/{max}",
    },
    # ─── Ban/Mute/Kick ───────────────────────────────────────────
    "banned": {
        "ar": "🚫 تم حظر {user}\n📝 السبب: {reason}",
        "en": "🚫 {user} has been banned\n📝 Reason: {reason}",
    },
    "unbanned": {
        "ar": "✅ تم رفع الحظر عن {user}",
        "en": "✅ {user} has been unbanned",
    },
    "muted": {
        "ar": "🔇 تم كتم {user}\n⏱ المدة: {duration}\n📝 السبب: {reason}",
        "en": "🔇 {user} has been muted\n⏱ Duration: {duration}\n📝 Reason: {reason}",
    },
    "unmuted": {
        "ar": "🔊 تم رفع الكتم عن {user}",
        "en": "🔊 {user} has been unmuted",
    },
    "kicked": {
        "ar": "👢 تم طرد {user}\n📝 السبب: {reason}",
        "en": "👢 {user} has been kicked\n📝 Reason: {reason}",
    },
    # ─── Welcome ─────────────────────────────────────────────────
    "default_welcome": {
        "ar": "👋 أهلاً {user} في {chat}!\nيرجى قراءة القوانين واحترام الجميع. 🌟",
        "en": "👋 Welcome {user} to {chat}!\nPlease read the rules and respect everyone. 🌟",
    },
    "default_farewell": {
        "ar": "👋 وداعاً {user}، نتمنى لك التوفيق.",
        "en": "👋 Goodbye {user}, we wish you the best.",
    },
    "welcome_set": {
        "ar": "✅ تم تعيين رسالة الترحيب.",
        "en": "✅ Welcome message has been set.",
    },
    "farewell_set": {
        "ar": "✅ تم تعيين رسالة الوداع.",
        "en": "✅ Farewell message has been set.",
    },
    # ─── Captcha ─────────────────────────────────────────────────
    "captcha_msg": {
        "ar": (
            "👋 مرحباً {user}!\n\n"
            "⏱ لديك **{timeout} ثانية** لتأكيد أنك لست بوت.\n"
            "👇 اضغط الزر الصحيح:"
        ),
        "en": (
            "👋 Welcome {user}!\n\n"
            "⏱ You have **{timeout} seconds** to verify you're not a bot.\n"
            "👇 Press the correct button:"
        ),
    },
    "captcha_passed": {
        "ar": "✅ تم التحقق! أهلاً بك {user} 🎉",
        "en": "✅ Verified! Welcome {user} 🎉",
    },
    "captcha_failed": {
        "ar": "❌ فشل التحقق! تم طرد {user}.",
        "en": "❌ Verification failed! {user} has been kicked.",
    },
    "captcha_wrong": {
        "ar": "❌ إجابة خاطئة! حاول مرة أخرى.",
        "en": "❌ Wrong answer! Try again.",
    },
    # ─── AntiSpam/Link/Flood ──────────────────────────────────────
    "antilink_triggered": {
        "ar": "🔗 تم حذف رابط غير مسموح به من {user}.",
        "en": "🔗 Deleted an unauthorized link from {user}.",
    },
    "antiflood_triggered": {
        "ar": "🌊 تم كتم {user} بسبب الفلود ({count} رسائل).",
        "en": "🌊 {user} has been muted for flooding ({count} messages).",
    },
    "antispam_triggered": {
        "ar": "🚫 تم حذف رسالة سبام من {user}.",
        "en": "🚫 Deleted a spam message from {user}.",
    },
    # ─── Settings ────────────────────────────────────────────────
    "settings_panel": {
        "ar": "⚙️ **إعدادات المجموعة**\n\nاختر ما تريد تعديله:",
        "en": "⚙️ **Group Settings**\n\nChoose what to configure:",
    },
    "toggle_on":  {"ar": "✅ مفعّل",  "en": "✅ ON"},
    "toggle_off": {"ar": "❌ معطّل", "en": "❌ OFF"},
    # ─── Rules ───────────────────────────────────────────────────
    "no_rules": {
        "ar": "📋 لم يتم تعيين قوانين لهذه المجموعة بعد.",
        "en": "📋 No rules have been set for this group yet.",
    },
    "rules_set": {
        "ar": "✅ تم حفظ القوانين.",
        "en": "✅ Rules have been saved.",
    },
    # ─── Lock ────────────────────────────────────────────────────
    "locked": {
        "ar": "🔒 تم قفل **{lock_type}** في هذه المجموعة.",
        "en": "🔒 **{lock_type}** has been locked in this group.",
    },
    "unlocked": {
        "ar": "🔓 تم فتح **{lock_type}** في هذه المجموعة.",
        "en": "🔓 **{lock_type}** has been unlocked in this group.",
    },
    "lock_deleted": {
        "ar": "🔒 تم حذف الرسالة (مقفل: {lock_type}).",
        "en": "🔒 Message deleted (locked: {lock_type}).",
    },
    # ─── Filters/Notes ────────────────────────────────────────────
    "filter_added": {
        "ar": "✅ تمت إضافة الفلتر `{keyword}`",
        "en": "✅ Filter `{keyword}` has been added.",
    },
    "filter_removed": {
        "ar": "✅ تم حذف الفلتر `{keyword}`",
        "en": "✅ Filter `{keyword}` has been removed.",
    },
    "no_filters": {
        "ar": "📋 لا توجد فلاتر في هذه المجموعة.",
        "en": "📋 No filters in this group.",
    },
    "note_added": {
        "ar": "✅ تمت إضافة الملاحظة `{name}`",
        "en": "✅ Note `{name}` has been saved.",
    },
    "note_removed": {
        "ar": "✅ تم حذف الملاحظة `{name}`",
        "en": "✅ Note `{name}` has been deleted.",
    },
    "no_notes": {
        "ar": "📋 لا توجد ملاحظات في هذه المجموعة.",
        "en": "📋 No notes in this group.",
    },
    # ─── GBan ─────────────────────────────────────────────────────
    "gbanned": {
        "ar": "🌐 تم الحظر العالمي للمستخدم {user}\n📝 السبب: {reason}",
        "en": "🌐 {user} has been globally banned\n📝 Reason: {reason}",
    },
    "ungbanned": {
        "ar": "✅ تم رفع الحظر العالمي عن {user}",
        "en": "✅ {user}'s global ban has been lifted.",
    },
    "gbanned_entry": {
        "ar": "🚫 {user} محظور عالمياً ولا يمكنه الانضمام.",
        "en": "🚫 {user} is globally banned and cannot join.",
    },
    # ─── Help ─────────────────────────────────────────────────────
    "help_text": {
        "ar": (
            "🛡️ **Guardian Bot - قائمة الأوامر**\n\n"
            "**👑 إدارة الأعضاء:**\n"
            "`/ban` - حظر عضو\n"
            "`/unban` - رفع الحظر\n"
            "`/mute` - كتم عضو\n"
            "`/unmute` - رفع الكتم\n"
            "`/kick` - طرد عضو\n"
            "`/warn` - تحذير عضو\n"
            "`/unwarn` - إزالة تحذير\n"
            "`/warns` - عرض التحذيرات\n"
            "`/purge` - حذف رسائل\n"
            "`/promote` - ترقية لمشرف\n"
            "`/demote` - إلغاء إشراف\n\n"
            "**🛡️ الحماية:**\n"
            "`/antispam` - مكافحة السبام\n"
            "`/antilink` - مكافحة الروابط\n"
            "`/antiflood` - مكافحة الفلود\n"
            "`/captcha` - التحقق من الأعضاء\n"
            "`/lock` - قفل نوع رسائل\n"
            "`/unlock` - فتح القفل\n"
            "`/locks` - عرض الأقفال\n"
            "`/blacklist` - إضافة كلمة محظورة\n"
            "`/blacklists` - قائمة الكلمات المحظورة\n\n"
            "**📝 الفلاتر والملاحظات:**\n"
            "`/filter` - إضافة فلتر\n"
            "`/filters` - قائمة الفلاتر\n"
            "`/note` - حفظ ملاحظة\n"
            "`/notes` - قائمة الملاحظات\n"
            "`#اسم` - استدعاء ملاحظة\n\n"
            "**👋 الترحيب:**\n"
            "`/welcome` - تفعيل/إيقاف الترحيب\n"
            "`/setwelcome` - تعيين رسالة ترحيب\n"
            "`/farewell` - تفعيل/إيقاف الوداع\n"
            "`/setfarewell` - تعيين رسالة وداع\n\n"
            "**⚙️ إعدادات المجموعة:**\n"
            "`/settings` - لوحة الإعدادات\n"
            "`/rules` - عرض القوانين\n"
            "`/setrules` - تعيين القوانين\n"
            "`/adminlist` - قائمة المشرفين\n"
            "`/pin` - تثبيت رسالة\n"
            "`/unpin` - إلغاء تثبيت\n"
            "`/lang` - تغيير اللغة\n\n"
            "**ℹ️ معلومات:**\n"
            "`/id` - الحصول على الـ ID\n"
            "`/info` - معلومات عضو\n"
            "`/report` - إبلاغ عن مخالفة\n\n"
            "**🌐 الحظر العالمي (المطور فقط):**\n"
            "`/gban` - حظر عالمي\n"
            "`/ungban` - رفع الحظر العالمي\n"
            "`/gbans` - قائمة المحظورين عالمياً\n"
        ),
        "en": (
            "🛡️ **Guardian Bot - Command List**\n\n"
            "**👑 Member Management:**\n"
            "`/ban` - Ban a member\n"
            "`/unban` - Unban a member\n"
            "`/mute` - Mute a member\n"
            "`/unmute` - Unmute a member\n"
            "`/kick` - Kick a member\n"
            "`/warn` - Warn a member\n"
            "`/unwarn` - Remove a warning\n"
            "`/warns` - View warnings\n"
            "`/purge` - Delete messages\n"
            "`/promote` - Promote to admin\n"
            "`/demote` - Remove admin\n\n"
            "**🛡️ Protection:**\n"
            "`/antispam` - Toggle anti-spam\n"
            "`/antilink` - Toggle anti-link\n"
            "`/antiflood` - Toggle anti-flood\n"
            "`/captcha` - Toggle captcha\n"
            "`/lock` - Lock message type\n"
            "`/unlock` - Unlock message type\n"
            "`/locks` - View locks\n"
            "`/blacklist` - Add blacklisted word\n"
            "`/blacklists` - View blacklist\n\n"
            "**📝 Filters & Notes:**\n"
            "`/filter` - Add a filter\n"
            "`/filters` - List all filters\n"
            "`/note` - Save a note\n"
            "`/notes` - List all notes\n"
            "`#name` - Retrieve a note\n\n"
            "**👋 Welcome:**\n"
            "`/welcome` - Toggle welcome\n"
            "`/setwelcome` - Set welcome message\n"
            "`/farewell` - Toggle farewell\n"
            "`/setfarewell` - Set farewell message\n\n"
            "**⚙️ Group Settings:**\n"
            "`/settings` - Settings panel\n"
            "`/rules` - View rules\n"
            "`/setrules` - Set rules\n"
            "`/adminlist` - List admins\n"
            "`/pin` - Pin a message\n"
            "`/unpin` - Unpin a message\n"
            "`/lang` - Change language\n\n"
            "**ℹ️ Info:**\n"
            "`/id` - Get ID\n"
            "`/info` - User info\n"
            "`/report` - Report a violation\n\n"
            "**🌐 Global Bans (Dev only):**\n"
            "`/gban` - Global ban\n"
            "`/ungban` - Remove global ban\n"
            "`/gbans` - List globally banned\n"
        ),
    },
}


def get(key: str, lang: str = "ar", **kwargs) -> str:
    s = STRINGS.get(key, {})
    text = s.get(lang, s.get("ar", s.get("en", f"[{key}]")))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
