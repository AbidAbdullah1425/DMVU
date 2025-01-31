import requests
import os
import time
from bot import Bot
from config import OWNER_ID, CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN
from pyrogram import filters

# Function to refresh the access token
def refresh_access_token():
    url = "https://api.dailymotion.com/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        new_access_token = response.json().get('access_token')
        if new_access_token:
            os.environ["ACCESS_TOKEN"] = new_access_token
            return new_access_token
    print(f"Failed to refresh token: {response.text}")
    return None

# Function to check if the access token is expired
def is_access_token_expired():
    url = "https://api.dailymotion.com/me"
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', ACCESS_TOKEN)}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 401

# Get a valid access token
def get_access_token():
    if is_access_token_expired():
        return refresh_access_token() or None
    return os.getenv("ACCESS_TOKEN", ACCESS_TOKEN)

# Upload file with progress tracking
def upload_file_with_progress(upload_url, file_path, client, message):
    file_size = os.path.getsize(file_path)
    uploaded_bytes = 0
    chunk_size = 5 * 1024 * 1024  # 5 MB per chunk
    start_time = time.time()

    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            response = requests.post(upload_url, files={"file": chunk})
            if response.status_code != 200:
                return None, f"❌ Upload failed at {uploaded_bytes / (1024 * 1024):.2f} MB.\nError: {response.text}"

            uploaded_bytes += len(chunk)
            percent_done = (uploaded_bytes / file_size) * 100
            elapsed_time = time.time() - start_time
            speed = (uploaded_bytes / (1024 * 1024)) / elapsed_time  # MB/s
            
            progress_text = f"🚀 Uploading: {uploaded_bytes / (1024 * 1024):.2f}/{file_size / (1024 * 1024):.2f} MB ({percent_done:.2f}%) at {speed:.2f} MB/s"
            client.send_message(OWNER_ID, progress_text)

    return upload_url, None

# Start command
@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(client, message):
    await message.reply("✅ Bot is working! Send an MKV video to upload.")

# Handle MKV video uploads
@Bot.on_message(filters.user(OWNER_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        video_file = await message.download()
        file_name = os.path.basename(video_file)
        title = file_name.split('.')[0]
        description = f"Episode {title.split('EP')[-1]} of Battle Through The Heavens."

        await message.reply("🔄 Preparing to upload your video to Dailymotion...")

        access_token = get_access_token()
        if not access_token:
            await message.reply("❌ Failed to authenticate with Dailymotion. Check API credentials.")
            return

        # Step 1: Get an upload URL from Dailymotion
        upload_url = "https://api.dailymotion.com/file/upload"
        headers = {"Authorization": f"Bearer {access_token}"}

        upload_response = requests.get(upload_url, headers=headers)
        if upload_response.status_code != 200:
            await message.reply(f"❌ Failed to get upload URL from Dailymotion.\nError: {upload_response.text}")
            return

        upload_link = upload_response.json()["upload_url"]

        # Step 2: Upload the file in chunks with progress
        uploaded_url, error_message = upload_file_with_progress(upload_link, video_file, client, message)
        if error_message:
            await message.reply(error_message)
            os.remove(video_file)
            return

        # Step 3: Create video entry on Dailymotion
        create_video_url = "https://api.dailymotion.com/me/videos"
        tags = ["btth", "Battle Through The Heavens", "DonghuaWillow"]
        video_metadata = {
            "title": title,
            "description": description,
            "url": uploaded_url,
            "published": "true",
            "is_created_for_kids": "false",
            "category": "tv",
            "tags": ",".join(tags)
        }

        create_response = requests.post(create_video_url, headers=headers, data=video_metadata)

        status_report = []
        video_id = None

        if create_response.status_code == 200:
            response_json = create_response.json()
            video_id = response_json.get("id")

            status_report.append("✅ Video entry created" if video_id else "❌ Video entry creation failed")
            status_report.append("✅ Title set successfully" if response_json.get("title") == title else "❌ Title not set correctly")
            status_report.append("✅ Description added" if response_json.get("description") == description else "❌ Description failed")
            status_report.append("✅ Video is public" if response_json.get("published") == "true" else "❌ Video is not public")
            status_report.append("✅ Tags added successfully" if response_json.get("tags") == ",".join(tags) else "❌ Tags were not added correctly")
            status_report.append("✅ Category set to TV" if response_json.get("category") == "tv" else "❌ Category setting failed")

        else:
            status_report.append(f"❌ Video creation failed: {create_response.text}")

        # Send report to PM
        report_text = "\n".join(status_report)
        await client.send_message(OWNER_ID, f"📊 **Upload Status Report:**\n{report_text}")

        # If all tasks succeeded, send the embedded video link
        if all("✅" in line for line in status_report):
            video_embedded_link = f"https://www.dailymotion.com/embed/video/{video_id}"
            await client.send_message(OWNER_ID, f"🎬 **Embedded Video Link:**\n`{video_embedded_link}`")

            await message.reply(f"✅ Video uploaded successfully! 🎉\nWatch it here: https://www.dailymotion.com/video/{video_id}")
        else:
            await message.reply("⚠️ Some steps failed. Check PM for details.")

        os.remove(video_file)

    else:
        await message.reply("⚠️ Please send an MKV video file.")
