#!/usr/bin/env python3

from yt_dlp import YoutubeDL
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from asyncio import get_event_loop
import os
from bot import Bot

DOWNLOAD_DIR = './downloads/'

# Ensure the download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(link, output_path):
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'outtmpl': output_path,
        'merge_output_format': 'mkv'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])

@Bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply("Welcome! Send me the m3u8 link to download the video in MKV format at 720p resolution.")

@Bot.on_message(filters.private)
async def handle_m3u8_link(client, message):
    link = message.text
    if link.startswith("http"):
        output_path = f"{DOWNLOAD_DIR}%(title)s.%(ext)s"
        loop = get_event_loop()
        try:
            await loop.run_in_executor(None, download_video, link, output_path)
            await message.reply("Download started. You'll receive the video once it's done.")
        except Exception as e:
            await message.reply(f"Error downloading video: {e}")
    else:
        await message.reply("Please send a valid m3u8 link.")