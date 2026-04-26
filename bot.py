import os
import re
import asyncio
import tempfile
import logging
from pathlib import Path

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN     = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
COOKIES_PATH  = Path("/tmp/cookies.txt")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB Telegram limit

URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^\s]*)?')

SUPPORTED_SITES = (
    "YouTube • TikTok • Instagram • Facebook • Twitter/X\n"
    "Vimeo • Dailymotion • Reddit • Twitch • and 1,000+ more"
)

# ── Cookies setup ───────────────────────────────────────────────────────────
def setup_cookies():
    content = os.getenv("COOKIES_CONTENT", "").strip()
    if content:
        COOKIES_PATH.write_text(content)
        logger.info("✅ Cookies loaded from COOKIES_CONTENT env.")
    else:
        logger.warning("⚠️  No COOKIES_CONTENT — YouTube age-restricted/login videos may fail.")

# ── yt-dlp options ──────────────────────────────────────────────────────────
def get_ydl_opts(extra: dict = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # 2025/2026 best practice: impersonate a real browser to bypass bot checks
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        },
        # Retry on transient errors
        "retries": 5,
        "fragment_retries": 5,
        # Use the PO Token workaround (yt-dlp >=2024.11)
        "extractor_args": {
            "youtube": {
                # Tell yt-dlp to prefer the web client which is less rate-limited
                "player_client": ["web", "android"],
            }
        },
    }
    if COOKIES_PATH.exists():
        opts["cookiefile"] = str(COOKIES_PATH)
    if extra:
        opts.update(extra)
    return opts

# ── Helpers ─────────────────────────────────────────────────────────────────
def is_url(text: str) -> bool:
    return bool(URL_PATTERN.match(text.strip()))

def format_duration(seconds) -> str:
    if not seconds:
        return "Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def format_size(b) -> str:
    if not b:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GB"

def get_video_info(url: str) -> dict:
    with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
        return ydl.extract_info(url, download=False)

def build_format_list(formats: list) -> list:
    seen, result = set(), []
    for f in reversed(formats):
        if f.get("vcodec", "none") == "none" or not f.get("height"):
            continue
        h = f["height"]
        if h in seen:
            continue
        seen.add(h)
        size = f.get("filesize") or f.get("filesize_approx") or 0
        result.append({
            "format_id": f["format_id"],
            "label": f"{h}p  —  {format_size(size)}",
            "height": h,
        })
    return sorted(result, key=lambda x: x["height"], reverse=True)[:5]

# ── Commands ─────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 *Hello, {user}!*\n\n"
        "I'm a high-speed video downloader. Just send me any video link.\n\n"
        f"*Supported platforms:*\n{SUPPORTED_SITES}\n\n"
        "📎 Paste any video URL to get started.\n"
        "Type /help for more info.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use*\n\n"
        "1. Copy a video URL from any supported platform.\n"
        "2. Paste it here — I'll analyse it instantly.\n"
        "3. Choose quality or extract audio only.\n"
        "4. File sent directly to this chat.\n\n"
        "⚙️ *Commands*\n"
        "/start  — Welcome message\n"
        "/help   — This help page\n"
        "/status — Bot status & cookies\n\n"
        "⚠️ *Limits*\n"
        "• Max file size: 50 MB (Telegram limit)\n"
        "• Private/DRM videos cannot be downloaded",
        parse_mode=ParseMode.MARKDOWN,
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cookies_status = "✅ Loaded" if COOKIES_PATH.exists() else "❌ Not set"
    await update.message.reply_text(
        f"🤖 *Bot Status*\n\n"
        f"🍪 Cookies: {cookies_status}\n"
        f"📦 yt-dlp: `{yt_dlp.version.__version__}`\n"
        f"🟢 Status: Online",
        parse_mode=ParseMode.MARKDOWN,
    )

# ── URL handler ──────────────────────────────────────────────────────────────
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_url(url):
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid URL.\n"
            "Please send a direct link starting with `https://`.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    status = await update.message.reply_text("🔍 Analysing URL, please wait…")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, get_video_info, url)

        title      = info.get("title", "Untitled Video")
        duration   = info.get("duration", 0)
        uploader   = info.get("uploader") or info.get("channel") or "Unknown"
        view_count = info.get("view_count")
        formats    = info.get("formats", [])

        video_formats = build_format_list(formats)
        has_audio = any(
            f.get("vcodec") == "none" and f.get("acodec") not in (None, "none")
            for f in formats
        )

        if not video_formats and not has_audio:
            await status.edit_text(
                "❌ No downloadable formats found.\n"
                "The video may be private, region-locked, or from an unsupported source."
            )
            return

        context.user_data.update({"url": url, "title": title})

        short_title = title[:60] + "…" if len(title) > 60 else title
        views_str   = f"{view_count:,}" if view_count else "N/A"
        dur_str     = format_duration(duration)

        buttons = [
            [InlineKeyboardButton(f"🎬  {fmt['label']}", callback_data=f"dl_video_{fmt['format_id']}")]
            for fmt in video_formats
        ]
        buttons.append([InlineKeyboardButton("🎵  Audio only  (MP3 192kbps)", callback_data="dl_audio")])
        buttons.append([InlineKeyboardButton("✖  Cancel", callback_data="cancel")])

        await status.edit_text(
            f"✅ *Video found*\n\n"
            f"📹 *{short_title}*\n"
            f"👤 {uploader}\n"
            f"⏱ Duration: `{dur_str}`\n"
            f"👁 Views: `{views_str}`\n\n"
            f"Select quality to download:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if "private" in err:
            msg = "🔒 This video is private and cannot be accessed."
        elif "not available" in err or "unavailable" in err:
            msg = "🌍 This video is not available in your region or has been removed."
        elif "unsupported url" in err:
            msg = "❌ This platform is not supported."
        elif "sign in" in err or "login" in err or "confirm" in err:
            msg = (
                "🔐 *YouTube requires authentication.*\n\n"
                "Set the `COOKIES_CONTENT` env variable with valid YouTube cookies.\n"
                "Type /status to check."
            )
        elif "429" in err or "too many" in err:
            msg = (
                "⏱ *Rate limited by YouTube.*\n\n"
                "Please wait a few minutes and try again.\n"
                "Adding YouTube cookies can help — see /status."
            )
        else:
            msg = f"❌ Download failed.\n\n`{str(e)[:250]}`"
        await status.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.exception("Unexpected error in handle_url")
        await status.edit_text(
            f"⚠️ Unexpected error. Please try again.\n\n`{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
        )

# ── Download & send ──────────────────────────────────────────────────────────
async def download_and_send(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    url: str,
    title: str,
    format_id: str = None,
    audio_only: bool = False,
):
    query = update.callback_query
    await query.edit_message_text("⬇️ Downloading… this may take a moment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_tmpl = str(Path(tmpdir) / "%(title)s.%(ext)s")

        if audio_only:
            extra = {
                "format": "bestaudio/best",
                "outtmpl": output_tmpl,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            extra = {
                "format": (
                    f"{format_id}+bestaudio[ext=m4a]/bestaudio/best"
                    if format_id else
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                ),
                "outtmpl": output_tmpl,
                "merge_output_format": "mp4",
            }

        ydl_opts = get_ydl_opts(extra)

        try:
            def do_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            await asyncio.get_event_loop().run_in_executor(None, do_download)

            files = list(Path(tmpdir).glob("*"))
            if not files:
                await query.edit_message_text("❌ Download failed — no output file produced.")
                return

            file_path = files[0]
            file_size = file_path.stat().st_size

            if file_size > MAX_FILE_SIZE:
                await query.edit_message_text(
                    "⚠️ *File too large*\n\n"
                    f"The file is `{format_size(file_size)}`, exceeding Telegram's 50 MB limit.\n"
                    "Please choose a lower quality and try again.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            await query.edit_message_text("📤 Uploading to Telegram…")

            short_title = title[:100] if title else "Video"
            caption = f"📹 *{short_title}*"

            with open(file_path, "rb") as f:
                if audio_only:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=f,
                        title=short_title,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                else:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=f,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        supports_streaming=True,
                    )

            await query.edit_message_text(
                f"✅ *Done!* Your {'audio' if audio_only else 'video'} has been sent.",
                parse_mode=ParseMode.MARKDOWN,
            )

        except yt_dlp.utils.DownloadError as e:
            err = str(e).lower()
            if "429" in err or "too many" in err:
                msg = "⏱ Rate limited. Please wait a few minutes and try again."
            else:
                msg = f"❌ Download error.\n\n`{str(e)[:200]}`"
            await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.exception("Error in download_and_send")
            await query.edit_message_text(
                f"❌ Error.\n\n`{str(e)[:200]}`",
                parse_mode=ParseMode.MARKDOWN,
            )

# ── Callback router ──────────────────────────────────────────────────────────
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data  = query.data
    url   = context.user_data.get("url")
    title = context.user_data.get("title", "Video")

    if data == "cancel":
        await query.edit_message_text("✖ Cancelled.")
        return
    if not url:
        await query.edit_message_text("⚠️ Session expired. Please send the URL again.")
        return
    if data == "dl_audio":
        await download_and_send(update, context, url, title, audio_only=True)
    elif data.startswith("dl_video_"):
        await download_and_send(update, context, url, title, format_id=data[len("dl_video_"):])

# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    setup_cookies()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("Bot is running…")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
