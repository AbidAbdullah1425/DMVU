from pyrogram import Client, filters
import os
import requests
import time
from bot import Bot
from config import OWNER_ID


# Function to simulate m3u8 download and update progress
def download_m3u8(url, save_path):
    total_size = 300 * 1024 * 1024  # Example file size (300MB)
    downloaded_size = 0
    speed = 0
    start_time = time.time()

    with open(save_path, "wb") as f:
        while downloaded_size < total_size:
            time.sleep(1)  # Simulate downloading for 1 second
            downloaded_size += 25 * 1024 * 1024  # Simulate downloading 25MB at a time
            
            elapsed_time = time.time() - start_time
            speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
            progress = int(downloaded_size / total_size * 20)
            percent = int(downloaded_size / total_size * 100)
            
            # Yield progress to update the message
            yield {
                "progress": progress,
                "percent": percent,
                "downloaded": downloaded_size,
                "total": total_size,
                "speed": speed,
                "elapsed_time": elapsed_time,
                "file_path": save_path
            }

# Function to simulate file upload and update progress
async def upload_file(client, message, file_path, user_id, user_name):
    total_size = os.path.getsize(file_path)
    uploaded_size = 0
    speed = 0
    start_time = time.time()
    
    # Open file and simulate upload in chunks
    with open(file_path, "rb") as file:
        while uploaded_size < total_size:
            chunk = file.read(1024 * 1024)  # Simulate uploading 1MB at a time
            uploaded_size += len(chunk)
            
            elapsed_time = time.time() - start_time
            speed = uploaded_size / elapsed_time if elapsed_time > 0 else 0
            progress = int(uploaded_size / total_size * 20)
            percent = int(uploaded_size / total_size * 100)
            
            # Update the progress message with upload status
            progress_text = f"""
            video
            ┃ [{'■' * progress}{'□' * (20 - progress)}] {percent}%
            ┠ Processed: {uploaded_size / (1024 * 1024):.1f}MB of {total_size / (1024 * 1024):.1f}MB
            ┠ Status: Upload | ETA: -
            ┠ Speed: {speed / (1024 * 1024):.1f}MB/s | Elapsed: {elapsed_time / 60:.1f}m
            ┠ User: {user_name} | ID: {user_id}
            ┖ /cancel_{user_id}

            ⌬ Bot Stats
            ┠ CPU: 0.1% | F: 18.79GB [92.4%]
            ┠ RAM: 43.6% | UPTIME: 13m42s
            ┖ DL: 0B/s | UL: 0B/s
            """
            await message.edit(progress_text)

    return uploaded_size  # Return the size of the uploaded file

# Command handler for '/dl' command
@Bot.on_message(filters.command("dl") && filters.user(OWNER_ID))
async def handle_dl_command(client, message):
    url = message.text.split(" ")[1]  # Extract the URL from the command
    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name

    # Send initial message with download status
    progress_message = await message.reply(f"Starting download for {url}...")

    # Define the save path for the downloaded file
    save_path = f"{user_id}_video.mkv"

    # Simulate download and send updates
    async for progress in download_m3u8(url, save_path):
        progress_text = f"""
        video
        ┃ [{'■' * progress['progress']}{'□' * (20 - progress['progress'])}] {progress['percent']}%
        ┠ Processed: {progress['downloaded'] / (1024 * 1024):.1f}MB of {progress['total'] / (1024 * 1024):.1f}MB
        ┠ Status: Download | ETA: -
        ┠ Speed: {progress['speed'] / (1024 * 1024):.1f}MB/s | Elapsed: {progress['elapsed_time'] / 60:.1f}m
        ┠ User: {user_name} | ID: {user_id}
        ┖ /cancel_{user_id}

        ⌬ Bot Stats
        ┠ CPU: 0.1% | F: 18.79GB [92.4%]
        ┠ RAM: 43.6% | UPTIME: 13m42s
        ┖ DL: 0B/s | UL: 0B/s
        """
        await progress_message.edit(progress_text)

    # Once the download completes, update message and start upload
    await progress_message.edit(f"Download complete! Now uploading the video...")

    # Upload video to user in document format
    uploaded_size = await upload_file(client, progress_message, save_path, user_id, user_name)
    
    # Once uploaded, notify user and clean up
    await progress_message.edit(f"Upload complete! Sending the file...")

    with open(save_path, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded and uploaded video!")

    # Clean up: remove the downloaded file after sending it
    os.remove(save_path)
