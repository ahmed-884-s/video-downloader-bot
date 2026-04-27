# 🛡️ Guardian Bot

بوت حماية احترافي للمجموعات | Professional Telegram Group Protection Bot

## ✨ المميزات | Features

### 🛡️ الحماية | Protection
- **Anti-Spam** - مكافحة السبام
- **Anti-Link** - حذف روابط التيليجرام تلقائياً
- **Anti-Flood** - كتم من يرسل كثيراً
- **Captcha** - تحقق من الأعضاء الجدد (مسائل حسابية)
- **Blacklist** - كلمات محظورة
- **Locks** - قفل أنواع الرسائل (صور/فيديو/ستيكر...)
- **GBan** - حظر عالمي عبر كل المجموعات

### 👑 إدارة | Management
- Ban / Unban / Kick
- Mute / Unmute (مع مدة زمنية)
- Warn system (حظر تلقائي عند بلوغ الحد)
- Promote / Demote
- Purge messages
- Pin / Unpin

### 📝 محتوى | Content
- Filters (كلمة → رد تلقائي)
- Notes (ملاحظات تُستدعى بـ #اسم)
- Welcome / Farewell messages
- Rules

### ⚙️ إعدادات | Settings
- لوحة تحكم كاملة بالأزرار
- دعم العربي والإنجليزي

---

## 🚀 التشغيل على Railway

### 1. Fork/Upload المشروع على GitHub

### 2. إنشاء مشروع على Railway
- New Project → Deploy from GitHub
- اختر الـ repo

### 3. إضافة المتغيرات
في Railway → Variables:
```
BOT_TOKEN = توكن البوت من @BotFather
OWNER_ID  = ID الحساب الخاص بك (من @userinfobot)
```

### 4. تشغيل تلقائي ✅

---

## 📋 الأوامر | Commands

| الأمر | الوصف |
|-------|--------|
| `/start` | بدء البوت |
| `/help` | قائمة الأوامر |
| `/settings` | لوحة الإعدادات |
| `/lang` | تغيير اللغة |
| `/ban` | حظر عضو |
| `/unban` | رفع الحظر |
| `/mute [مدة]` | كتم (مثال: `/mute 10m`) |
| `/unmute` | رفع الكتم |
| `/kick` | طرد |
| `/warn [سبب]` | تحذير |
| `/unwarn` | إزالة تحذير |
| `/warns` | عرض التحذيرات |
| `/purge` | حذف رسائل |
| `/promote` | ترقية لمشرف |
| `/demote` | إلغاء إشراف |
| `/filter كلمة رد` | إضافة فلتر |
| `/unfilter كلمة` | حذف فلتر |
| `/filters` | عرض الفلاتر |
| `/note اسم نص` | حفظ ملاحظة |
| `/delnote اسم` | حذف ملاحظة |
| `/notes` | عرض الملاحظات |
| `#اسم` | استدعاء ملاحظة |
| `/blacklist كلمة` | إضافة للقائمة السوداء |
| `/unblacklist كلمة` | إزالة من القائمة السوداء |
| `/blacklists` | عرض القائمة السوداء |
| `/antispam` | تفعيل/إيقاف مكافحة السبام |
| `/antilink` | تفعيل/إيقاف مكافحة الروابط |
| `/antiflood` | تفعيل/إيقاف مكافحة الفلود |
| `/captcha` | تفعيل/إيقاف الكابتشا |
| `/lock نوع` | قفل نوع رسائل |
| `/unlock نوع` | فتح قفل |
| `/locks` | عرض الأقفال |
| `/welcome` | تفعيل/إيقاف الترحيب |
| `/setwelcome نص` | تعيين رسالة ترحيب |
| `/farewell` | تفعيل/إيقاف الوداع |
| `/setfarewell نص` | تعيين رسالة وداع |
| `/rules` | عرض القوانين |
| `/setrules نص` | تعيين القوانين |
| `/adminlist` | قائمة المشرفين |
| `/pin` | تثبيت رسالة |
| `/unpin` | إلغاء تثبيت |
| `/id` | الحصول على ID |
| `/info` | معلومات مستخدم |
| `/report` | إبلاغ عن مخالفة |
| `/gban` | حظر عالمي (المطور فقط) |
| `/ungban` | رفع الحظر العالمي |
| `/gbans` | قائمة المحظورين عالمياً |

### متغيرات الترحيب | Welcome Variables
- `{user}` - اسم العضو
- `{chat}` - اسم المجموعة

### أنواع القفل | Lock Types
`text`, `photo`, `video`, `audio`, `voice`, `document`, `sticker`, `gif`, `forward`, `game`, `url`

---

## 📁 هيكل المشروع | Project Structure

```
guardian_bot/
├── main.py              # نقطة البداية
├── requirements.txt
├── railway.json
├── Procfile
├── handlers/
│   ├── commands.py      # جميع الأوامر
│   └── messages.py      # معالجة الرسائل والأحداث
├── utils/
│   ├── database.py      # قاعدة البيانات SQLite
│   └── helpers.py       # دوال مساعدة
└── locales/
    └── strings.py       # النصوص ثنائية اللغة
```
