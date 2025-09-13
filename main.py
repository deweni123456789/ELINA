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

# -------------------- Download Helper --------------------
async def download_media(url: str):
    ydl_opts = {
        "format": "best",
        "outtmpl": f"/tmp/%(title)s.%(ext)s",  # Railway uses ephemeral /tmp folder
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
    return info

# -------------------- Message Handler --------------------
@bot.on_message(filters.text & ~filters.edited)
async def auto_download(client: Client, message: Message):
    urls = URL_REGEX.findall(message.text)
    if not urls:
        return
    status_msg = await message.reply_text("🔄 Downloading media...")
    for url in urls:
        try:
            info = await download_media(url)
            file_path = f"/tmp/{info['title']}.{info.get('ext','mp4')}"
            caption = f"**Title:** {info.get('title','N/A')}\n" \
                      f"**Uploader:** {info.get('uploader','N/A')}\n" \
                      f"**Duration:** {info.get('duration','N/A')} seconds\n" \
                      f"**View Count:** {info.get('view_count','N/A')}"

            # Detect type: video or other
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
            os.remove(file_path)  # Clean up
        except Exception as e:
            await message.reply_text(f"❌ Failed to download:\n{e}")
    await status_msg.delete()

# -------------------- Run Bot --------------------
if __name__ == "__main__":
    print("Bot is running on Railway...")
    bot.run()
