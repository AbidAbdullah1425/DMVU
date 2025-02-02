import os
import time
import asyncio
import yt_dlp
from pyrogram import Client, filters
from bot import Bot
from config import OWNER_ID

# Directory to store video files
VIDEO_FOLDER = "downloads"

# Function to download video using yt-dlp
async def download_m3u8_video(url, user_id):
    save_path = os.path.join(VIDEO_FOLDER, f"{user_id}_video")
    os.makedirs(save_path, exist_ok=True)
    
    # yt-dlp download options
    ydl_opts = {
        'format': 'best',  # best quality
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),  # Output file format
        'merge_output_format': 'mkv',  # Merge into MKV format
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferredformat': 'mkv',  # Convert to MKV
        }],
        'noplaylist': True,  # Avoid downloading playlist
        'quiet': False,
    }

    # Running yt-dlp to download the video
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        return save_path  # Return the download path
    except Exception as e:
        return None, f"Download failed: {str(e)}"

# Function to merge TS files if needed and handle download completion
async def merge_video(save_path, user_id):
    video_file = os.path.join(save_path, f"{user_id}_video.mkv")
    
    if not os.path.exists(video_file):
        return None, "Error: Video download failed."

    return video_file  # Return the merged file path

# Command handler for the '/dl' command
@Bot.on_message(filters.command("dl") & filters.user(OWNER_ID))
async def handle_dl_command(client, message):
    try:
        url = message.text.split(" ")[1]  # Extract the URL from the command
    except IndexError:
        return await message.reply("Usage: /dl <m3u8_url>")
    
    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name

    # Send initial message indicating the download is starting
    progress_message = await message.reply(f"Starting download for {url}...")

    # Download video using yt-dlp
    download_path, error = await download_m3u8_video(url, user_id)

    if download_path is None:
        # If download fails, send error message
        await progress_message.edit(f"Download failed: {error}")
        return

    # Once download completes, update the message and start the upload
    await progress_message.edit("Download complete! Now uploading the video...")

    # Merge the video files if necessary (for .ts segments)
    video_file = await merge_video(download_path, user_id)

    if video_file is None:
        await progress_message.edit("Error during video merging!")
        return

    # Send the video file to the user
    with open(video_file, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded video!")

    # Clean up by removing the downloaded files
    os.remove(video_file)

    # Remove the folder after upload
    os.rmdir(download_path)
