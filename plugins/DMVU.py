from pyrogram import Client, filters
import os
import time
import asyncio
from bot import Bot
from config import OWNER_ID

# Asynchronous function to simulate m3u8 download and update progress.
# This function writes dummy data so that the file size is nonzero.
async def download_m3u8(url, save_path):
    total_size = 300 * 1024 * 1024  # Simulated file size: 300 MB
    downloaded_size = 0
    start_time = time.time()
    chunk_size = 25 * 1024 * 1024  # 25 MB per iteration

    with open(save_path, "wb") as f:
        while downloaded_size < total_size:
            await asyncio.sleep(1)  # Simulate asynchronous download delay
            # Write dummy data for simulation
            f.write(b"\0" * chunk_size)
            f.flush()  # Ensure data is written to disk
            downloaded_size += chunk_size

            elapsed_time = time.time() - start_time
            speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
            progress = int(downloaded_size / total_size * 20)
            percent = int(downloaded_size / total_size * 100)

            # Yield a dictionary containing progress details
            yield {
                "progress": progress,
                "percent": percent,
                "downloaded": downloaded_size,
                "total": total_size,
                "speed": speed,
                "elapsed_time": elapsed_time,
                "file_path": save_path
            }

# Asynchronous function to simulate file upload and update progress.
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

            # Create and update the progress message for upload
            progress_text = f"""
video
┃ [{'■' * progress}{'□' * (20 - progress)}] {percent}%
┠ Processed: {uploaded_size / (1024 * 1024):.1f}MB of {total_size / (1024 * 1024):.1f}MB
┠ Status: Upload | ETA: -
┠ Speed: {speed / (1024 * 1024):.1f}MB/s | Elapsed: {elapsed_time / 60:.1f}m
┠ User: {user_name} | ID: {user_id}
┖ /cancel_{user_id}
"""
            await message.edit(progress_text)
            await asyncio.sleep(0.1)  # Brief pause for smooth editing

    return uploaded_size  # Return the total uploaded size

# Command handler for the '/dl' command.
@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_command(client, message):
    try:
        url = message.text.split(" ")[1]  # Extract the URL from the command
    except IndexError:
        return await message.reply("Usage: /dl <m3u8_url>")

    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name

    # Send initial message indicating the download is starting.
    progress_message = await message.reply(f"Starting download for {url}...")

    # Define the save path for the downloaded file.
    save_path = f"{user_id}_video.mkv"

    # Simulate the download process with live progress updates.
    async for progress in download_m3u8(url, save_path):
        progress_text = f"""
video
┃ [{'■' * progress['progress']}{'□' * (20 - progress['progress'])}] {progress['percent']}%
┠ Processed: {progress['downloaded'] / (1024 * 1024):.1f}MB of {progress['total'] / (1024 * 1024):.1f}MB
┠ Status: Download | ETA: -
┠ Speed: {progress['speed'] / (1024 * 1024):.1f}MB/s | Elapsed: {progress['elapsed_time'] / 60:.1f}m
┠ User: {user_name} | ID: {user_id}
┖ /cancel_{user_id}
"""
        await progress_message.edit(progress_text)

    # Once download completes, update the message and start the upload.
    await progress_message.edit("Download complete! Now uploading the video...")

    # Simulate the upload process with live progress updates.
    await upload_file(client, progress_message, save_path, user_id, user_name)

    # After upload completes, update the message and send the file as a document.
    await progress_message.edit("Upload complete! Sending the file...")

    with open(save_path, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded and uploaded video!")

    # Remove the temporary file after sending.
    os.remove(save_path)

