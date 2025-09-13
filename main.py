import os
import re
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN

# -------------------- Client Setup --------------------
bot = Client(
    "EliZaBethBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------- Inline Buttons --------------------
BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("Developer", url="https://t.me/deweni2"),
     InlineKeyboardButton("Support Group", url="https://t.me/slmusicmania")]
])

# -------------------- URL Detection --------------------
URL_REGEX = re.compile(r"(https?://[^\s]+)")

# -------------------- Sanitize Filename --------------------
def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)

# -------------------- Download Helper --------------------
async def download_media(url: str):
    ydl_opts = {
        "format": "best",
        "outtmpl": f"/tmp/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True
    }
    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(
            None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)
        )
        if info is None:
            return None, None
        title = sanitize_filename(info.get('title', 'file'))
        ext = info.get('ext', 'mp4')
        file_path = f"/tmp/{title}.{ext}"
        return info, file_path
    except Exception:
        return None, None

# -------------------- Message Handler --------------------
@bot.on_message(filters.text & ~filters.edited)
async def auto_download(client: Client, message: Message):
    urls = URL_REGEX.findall(message.text)
    if not urls:
        return
    status_msg = await message.reply_text("🔄 Downloading media...")
    for url in urls:
        info, file_path = await download_media(url)
        if not info or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            await message.reply_text(f"❌ Failed to download or empty file:\n{url}")
            continue

        caption = f"**Title:** {info.get('title','N/A')}\n" \
                  f"**Uploader:** {info.get('uploader','N/A')}\n" \
                  f"**Duration:** {info.get('duration','N/A')} sec\n" \
                  f"**View Count:** {info.get('view_count','N/A')}"
        try:
            if info.get('ext') in ["mp4", "mkv", "webm"]:
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_path,
                    caption=caption,
                    reply_markup=BUTTONS
                )
            else:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    caption=caption,
                    reply_markup=BUTTONS
                )
        except Exception as e:
            await message.reply_text(f"❌ Failed to send file:\n{e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    await status_msg.delete()

# -------------------- Run Bot --------------------
if __name__ == "__main__":
    print("Bot is running on Railway...")
    bot.run()
