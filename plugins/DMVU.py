from pyrogram import Client, filters
import os
import time
import asyncio
import subprocess
from bot import Bot
from config import OWNER_ID

# Function to download M3U8 with yt-dlp
async def download_m3u8(url, save_path, progress_message):
    process = await asyncio.create_subprocess_exec(
        "yt-dlp", "-f", "bestvideo+bestaudio", "--merge-output-format", "mkv",
        "-o", save_path, url,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    start_time = time.time()
    while process.returncode is None:  # While process is running
        await asyncio.sleep(5)  # Update progress every 5 seconds
        
        if os.path.exists(save_path):
            downloaded_size = os.path.getsize(save_path)
            elapsed_time = time.time() - start_time
            speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
            progress_text = f"""
video
┃ [{downloaded_size // (1024 * 1024)}MB] Downloading...
┠ Speed: {speed / (1024 * 1024):.1f}MB/s | Elapsed: {elapsed_time / 60:.1f}m
┠ Status: Downloading | ETA: -
┠ User: {progress_message.chat.username} | ID: {progress_message.chat.id}
┖ /cancel_{progress_message.chat.id}
"""
            await progress_message.edit(progress_text)

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise Exception(f"Download failed: {error_msg}")

    return save_path

# Upload function
async def upload_file(client, message, file_path, user_id, user_name):
    total_size = os.path.getsize(file_path)
    uploaded_size = 0
    start_time = time.time()

    with open(file_path, "rb") as file:
        while uploaded_size < total_size:
            chunk = file.read(1024 * 1024)  # Read 1 MB at a time
            if not chunk:
                break  # End of file reached
            uploaded_size += len(chunk)

            elapsed_time = time.time() - start_time
            speed = uploaded_size / elapsed_time if elapsed_time > 0 else 0
            progress = int(uploaded_size / total_size * 20)
            percent = int(uploaded_size / total_size * 100)

            # Update upload progress message
            progress_text = f"""
video
┃ [{'■' * progress}{'□' * (20 - progress)}] {percent}%
┠ Processed: {uploaded_size / (1024 * 1024):.1f}MB of {total_size / (1024 * 1024):.1f}MB
┠ Status: Uploading | ETA: -
┠ Speed: {speed / (1024 * 1024):.1f}MB/s | Elapsed: {elapsed_time / 60:.1f}m
┠ User: {user_name} | ID: {user_id}
┖ /cancel_{user_id}
"""
            await message.edit(progress_text)
            await asyncio.sleep(0.1)  # Brief pause for smooth editing

    return uploaded_size  # Return total uploaded size

# Command handler for '/dl'
@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_command(client, message):
    try:
        url = message.text.split(" ")[1]  # Extract URL
    except IndexError:
        return await message.reply("Usage: /dl <m3u8_url>")

    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name
    save_path = f"{user_id}_video.mkv"

    # Send initial download message
    progress_message = await message.reply(f"Starting download for {url}...")

    # Download video using yt-dlp
    try:
        await download_m3u8(url, save_path, progress_message)
    except Exception as e:
        return await progress_message.edit(f"Download failed: {e}")

    await progress_message.edit("Download complete! Now uploading the video...")

    # Upload file
    await upload_file(client, progress_message, save_path, user_id, user_name)

    # Send the file as document
    with open(save_path, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded and uploaded video!")

    os.remove(save_path)  # Delete file after sending
