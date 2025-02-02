import asyncio
import os
import time
import subprocess
from pyrogram import Client, filters
from bot import Bot
from config import OWNER_ID

async def download_m3u8(url, save_path):
    # yt-dlp command prioritizing MKV, then MP4
    command = [
        "yt-dlp",
        "-f", "bv*+ba/b",  # Best video + audio, fallback to best
        "--merge-output-format", "mkv,mp4",  # Prefer MKV, fallback to MP4
        "-o", save_path,  # Output file path
        url
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return False, stderr.decode()

    return True, None

@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_command(client, message):
    try:
        url = message.text.split(" ")[1]  # Extract URL
    except IndexError:
        return await message.reply("Usage: /dl <m3u8_url>")

    user_id = message.from_user.id
    save_path = f"{user_id}_video.mkv"

    progress_message = await message.reply(f"Downloading video from:\n`{url}`")

    success, error_msg = await download_m3u8(url, save_path)

    if not success:
        return await progress_message.edit(f"Download failed:\n```{error_msg}```")

    await progress_message.edit("Download complete! Uploading the video...")

    with open(save_path, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded video!")

    os.remove(save_path)
