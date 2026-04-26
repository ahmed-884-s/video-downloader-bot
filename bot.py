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

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MAX_FILE_SIZE = 50 * 1024 * 1024

URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^\s]*)?')

SUPPORTED_SITES = (
    "YouTube • TikTok • Instagram • Facebook • Twitter/X\n"
    "Vimeo • Dailymotion • Reddit • Twitch • and 1,000+ more"
)

def is_url(text):
    return bool(URL_PATTERN.match(text.strip()))

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def format_size(bytes_):
    if not bytes_:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} GB"

def get_video_info(url):
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

def build_format_list(formats):
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

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 *Hello, {user}!*\n\n"
        "I'm a high-speed video downloader bot. Just send me a link and I'll "
        "fetch the video in your preferred quality — completely free.\n\n"
        f"*Supported platforms:*\n{SUPPORTED_SITES}\n\n"
        "📎 Paste any video URL to get started.\n"
        "Type /help for more information.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use*\n\n"
        "1. Copy a video URL from any supported platform.\n"
        "2. Paste it here — I'll analyse it instantly.\n"
        "3. Choose your preferred quality or extract audio only.\n"
        "4. Your file will be sent directly to this chat.\n\n"
        "⚙️ *Commands*\n"
        "/start — Welcome message\n"
        "/help  — This help page\n\n"
        "⚠️ *Limitations*\n"
        "• Maximum file size: 50 MB (Telegram limit)\n"
        "• Private or DRM-protected videos cannot be downloaded\n"
        "• Large files may take a moment — please be patient",
        parse_mode=ParseMode.MARKDOWN,
    )

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
        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, url)

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
                "❌ No downloadable formats were found for this URL.\n"
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
            f"Select a quality to download:",
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
            msg = "❌ This platform is not supported.\nTry a link from YouTube, TikTok, Instagram, or similar."
        elif "sign in" in err or "login" in err:
            msg = "🔐 This video requires a login and cannot be downloaded."
        else:
            msg = f"❌ Download failed.\n\n`{str(e)[:250]}`"
        await status.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.exception("Unexpected error in handle_url")
        await status.edit_text(
            f"⚠️ An unexpected error occurred. Please try again.\n\n`{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
        )

async def download_and_send(update, context, url, title, format_id=None, audio_only=False):
    query = update.callback_query
    await query.edit_message_text("⬇️ Downloading… this may take a moment.")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_tmpl = str(Path(tmpdir) / "%(title)s.%(ext)s")

        if audio_only:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            ydl_opts = {
                "format": f"{format_id}+bestaudio/best" if format_id else "bestvideo+bestaudio/best",
                "outtmpl": output_tmpl,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "merge_output_format": "mp4",
            }

        try:
            def do_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            await asyncio.get_event_loop().run_in_executor(None, do_download)

            files = list(Path(tmpdir).glob("*"))
            if not files:
                await query.edit_message_text("❌ Download failed — no output file was produced.")
                return

            file_path = files[0]
            file_size = file_path.stat().st_size

            if file_size > MAX_FILE_SIZE:
                await query.edit_message_text(
                    "⚠️ *File too large*\n\n"
                    f"The file is `{format_size(file_size)}`, which exceeds Telegram's 50 MB upload limit.\n"
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

        except Exception as e:
            logger.exception("Error during download_and_send")
            await query.edit_message_text(
                f"❌ An error occurred during download.\n\n`{str(e)[:200]}`",
                parse_mode=ParseMode.MARKDOWN,
            )

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
        fmt_id = data[len("dl_video_"):]
        await download_and_send(update, context, url, title, format_id=fmt_id)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
