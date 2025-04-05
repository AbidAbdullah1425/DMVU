# plugins/ytdlp.py
import youtube_dl
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from bot import Bot
import time
import os

# Command to handle /ytdl
@Bot.on_message(filters.command(["ytdl"]))
async def ytdl(client, message):
    url = message.text.split(" ", 1)[1]
    ydl_opts = {
        'format': 'best',
        'noplaylist': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', None)
        
        buttons = []
        for fmt in formats:
            if fmt.get('height') and fmt.get('width'):
                button_text = f"{fmt['height']}p"
                button_data = f"ytdl_{fmt['format_id']}_{url}"
                buttons.append([InlineKeyboardButton(button_text, callback_data=button_data)])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply("Choose the resolution:", reply_markup=reply_markup)

# Callback handler for resolution selection
@Bot.on_callback_query(filters.regex(r"^ytdl_"))
async def callback_query(client, callback_query):
    data = callback_query.data.split("_")
    format_id = data[1]
    url = data[2]

    ydl_opts = {
        'format': format_id,
        'progress_hooks': [lambda d: download_progress_hook(d, callback_query)],
        'noplaylist': True,
        'outtmpl': '%(title)s.%(ext)s'
    }

    await callback_query.message.edit_text("Downloading...")
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    
    video_path = ydl.prepare_filename(info_dict)
    await callback_query.message.edit_text("Uploading...")
    await client.send_video(callback_query.message.chat.id, video=video_path, progress=upload_progress_hook, progress_args=(callback_query.message,))
    os.remove(video_path)

last_download_update_time = 0

def download_progress_hook(d, callback_query):
    global last_download_update_time
    if d['status'] == 'downloading':
        downloaded = d['downloaded_bytes']
        total = d['total_bytes']
        percentage = downloaded / total * 100
        current_time = time.time()
        if current_time - last_download_update_time >= 3:
            last_download_update_time = current_time
            asyncio.create_task(update_progress_bar(callback_query, percentage, "Downloading"))

async def update_progress_bar(callback_query, percentage, stage):
    progress_bar = f"[{'=' * int(percentage // 10)}{' ' * (10 - int(percentage // 10))}] {percentage:.2f}%"
    await callback_query.message.edit_text(f"{stage}...\n{progress_bar}")

last_upload_update_time = 0

def upload_progress_hook(current, total, message):
    global last_upload_update_time
    percentage = current * 100 / total
    current_time = time.time()
    if current_time - last_upload_update_time >= 3:
        last_upload_update_time = current_time
        asyncio.create_task(update_progress_bar(message, percentage, "Uploading"))