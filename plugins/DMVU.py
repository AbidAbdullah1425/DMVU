import requests
import os
import gc
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

# Check if the access token is expired
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

# Upload video in chunks to reduce RAM usage
def upload_video_in_chunks(file_path, upload_url):
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(5 * 1024 * 1024), b""):  # 5MB chunks
            response = requests.post(upload_url, files={"file": chunk})
            if response.status_code != 200:
                return None, response.text
    return upload_url, None

@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(client, message):
    await message.reply("✅ Bot is working! Send an MKV video to upload.")

@Bot.on_message(filters.user(OWNER_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        video_file = await message.download()
        file_name = os.path.basename(video_file)
        title = file_name.split('.')[0]
        description = f"Battle Through The Heavens episode {title}." if "EP" in title else "Battle Through The Heavens episode."

        await message.reply("🔄 Uploading your video to Dailymotion...")

        access_token = get_access_token()
        if not access_token:
            await message.reply("❌ Failed to authenticate with Dailymotion. Check API credentials.")
            return

        # Step 1: Get an upload URL from Dailymotion
        headers = {"Authorization": f"Bearer {access_token}"}
        upload_url_response = requests.get("https://api.dailymotion.com/file/upload", headers=headers)
        if upload_url_response.status_code != 200:
            await message.reply(f"❌ Failed to get upload URL.\nError: {upload_url_response.text}")
            return

        upload_link = upload_url_response.json()["upload_url"]

        # Step 2: Upload the file in chunks (LOW RAM USAGE)
        uploaded_url, error = upload_video_in_chunks(video_file, upload_link)
        os.remove(video_file)  # DELETE FILE IMMEDIATELY AFTER UPLOAD
        gc.collect()  # FREE MEMORY

        if error:
            await message.reply(f"❌ Error uploading video.\nError: {error}")
            return

        # Step 3: Create video entry on Dailymotion
        video_metadata = {
            "title": title,
            "description": description,
            "url": uploaded_url,
            "published": "true",
            "is_created_for_kids": "false",
            "channel": "tv"
        }

        create_response = requests.post("https://api.dailymotion.com/me/videos", headers=headers, data=video_metadata)
        if create_response.status_code == 200:
            video_id = create_response.json().get("id")
            video_link = f"https://www.dailymotion.com/video/{video_id}"

            await client.send_message(OWNER_ID, f"✅ Video uploaded successfully! 🎉\n\nWatch here: `{video_link}`")
            await message.reply(f"✅ Video uploaded successfully!\nWatch it here: {video_link}")
        else:
            await message.reply(f"❌ Failed to create video entry.\nError: {create_response.text}")
