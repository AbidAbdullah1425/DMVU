import requests
import os
import gc
from bot import Bot
from config import OWNER_ID, CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN
from pyrogram import filters

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

def get_access_token():
    return os.getenv("ACCESS_TOKEN", ACCESS_TOKEN) or refresh_access_token()

def upload_video_direct(file_path, upload_url, headers):
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(upload_url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json().get("url")  # Return the video URL
        return None, response.text  # Return error message

@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(client, message):
    await message.reply("✅ Bot is working! Send an MKV video to upload.")

@Bot.on_message(filters.user(OWNER_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        temp_video = await message.download()
        title = os.path.basename(temp_video).split('.')[0]
        description = f"Battle Through The Heavens episode {title}." if "EP" in title else "Battle Through The Heavens episode."

        await message.reply("🔄 Uploading your video to Dailymotion...")

        access_token = get_access_token()
        if not access_token:
            await message.reply("❌ Failed to authenticate with Dailymotion. Check API credentials.")
            return

        headers = {"Authorization": f"Bearer {access_token}"}
        upload_url_response = requests.get("https://api.dailymotion.com/file/upload", headers=headers)
        if upload_url_response.status_code != 200:
            await message.reply(f"❌ Failed to get upload URL.\nError: {upload_url_response.text}")
            return

        upload_link = upload_url_response.json()["upload_url"]

        uploaded_url, error = upload_video_direct(temp_video, upload_link, headers)

        os.remove(temp_video)
        gc.collect()

        if error:
            await message.reply(f"❌ Error uploading video.\nError: {error}")
            return

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
