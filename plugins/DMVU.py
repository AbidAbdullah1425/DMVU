from pyrogram import Client, filters
import yt_dlp
import os
import time

# Define the download function for M3U8 links
async def download_m3u8(url, save_path):
    ydl_opts = {
        'outtmpl': save_path,  # Set the output template
        'quiet': False,         # For progress messages
        'noplaylist': True,     # Ensure only the video is downloaded
        'format': 'best',       # Automatically choose the best available format
        'merge_output_format': 'mkv',  # Set the final output format (change to mp4 if needed)
        'postprocessors': [],   # Remove ffmpeg post-processing
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])  # Download the video

    return save_path

# Command handler for the '/dl' command
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

    # Simulate the download process (actual download will happen here)
    await download_m3u8(url, save_path)

    # Once download completes, update the message and start the upload.
    await progress_message.edit(f"Download complete! Now uploading the video...")

    # Send the video file as a document.
    with open(save_path, "rb") as file:
        await message.reply_document(file, caption="Here is your downloaded video!")

    # Remove the temporary file after sending.
    os.remove(save_path)
