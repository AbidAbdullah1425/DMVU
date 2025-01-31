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

# Upload the video and track progress
def upload_file(upload_url, file_path, client, message):
    file_size = os.path.getsize(file_path)
    uploaded_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    progress_interval = 0.1  # 10% progress interval

    with open(file_path, "rb") as file:
        # Uploading the file
        response = requests.post(upload_url, files={"file": file})
        if response.status_code != 200:
            return None, f"❌ Upload failed.\nError: {response.text}"

    # Simulate progress in percentage
    progress = 0
    while uploaded_bytes < file_size:
        uploaded_bytes += chunk_size
        progress = min((uploaded_bytes / file_size) * 100, 100)

        # Simulating a progress update
        if progress % progress_interval == 0:
            # Send progress as a log or message (optional logging)
            print(f"Upload Progress: {progress:.2f}%")

        # Avoid going over 100%
        if uploaded_bytes >= file_size:
            uploaded_bytes = file_size

    return upload_url, "✅ Upload complete!"

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

        # Step 2: Upload the file with progress tracking
        uploaded_url, error_message = upload_file(upload_link, video_file, client, message)
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
            video_embedded_link = f"```https://www.dailymotion.com/embed/video/{video_id}```"
            await client.send_message(OWNER_ID, f"🎬 **Embedded Video Link:**\n{video_embedded_link}")

            await message.reply(f"✅ Video uploaded successfully! 🎉\nWatch it here: https://www.dailymotion.com/video/{video_id}")
        else:
            await message.reply("⚠️ Some steps failed. Check PM for details.")

        os.remove(video_file)

    else:
        await message.reply("⚠️ Please send an MKV video file.")
