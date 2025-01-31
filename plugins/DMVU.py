import requests
import os
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
    else:
        print(f"Failed to refresh token: {response.text}")  # Log the error
        return None


# Function to check if the access token is expired
def is_access_token_expired():
    url = "https://api.dailymotion.com/me"
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN', ACCESS_TOKEN)}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 401:  # 401 means token expired
        print("Access token expired.")
        return True
    elif response.status_code != 200:
        print(f"Error checking token: {response.text}")  # Log unexpected errors
        return True
    return False


# Get a valid access token (refresh if needed)
def get_access_token():
    if is_access_token_expired():
        new_token = refresh_access_token()
        if not new_token:
            print("⚠️ Failed to refresh access token. Check refresh token.")
            return None
        return new_token
    return os.getenv("ACCESS_TOKEN", ACCESS_TOKEN)


# Start command to check if the bot is responsive
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

        await message.reply("🔄 Uploading your video to Dailymotion...")

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

        # Step 2: Upload the file
        with open(video_file, "rb") as file:
            files = {"file": file}
            upload_video_response = requests.post(upload_link, files=files)

        if upload_video_response.status_code == 200:
            video_id = upload_video_response.json().get("id")
            await message.reply(f"✅ Video uploaded! ID: {video_id}\nNow, send tags separated by commas.")

            # Step 3: Wait for user to send tags
            @Bot.on_message(filters.user(OWNER_ID) & filters.text)
            async def handle_tags(client, tag_message):
                tags = tag_message.text.split(",")

                # Update video metadata
                metadata_url = f"https://api.dailymotion.com/video/{video_id}"
                metadata_params = {
                    "title": title,
                    "description": title,
                    "tags": ",".join(tags)
                }
                metadata_response = requests.post(metadata_url, headers=headers, data=metadata_params)

                if metadata_response.status_code == 200:
                    await tag_message.reply(f"🎉 Video is ready: https://www.dailymotion.com/video/{video_id}")
                else:
                    await tag_message.reply(f"❌ Failed to update video metadata.\nError: {metadata_response.text}")

                os.remove(video_file)  # Cleanup
                Bot.remove_handler(handle_tags)  # Stop listening for tags after processing

        else:
            await message.reply(f"❌ Error uploading the video.\nError: {upload_video_response.text}")
            os.remove(video_file)

    else:
        await message.reply("⚠️ Please send an MKV video file.")
