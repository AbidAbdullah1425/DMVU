import requests
import os
from bot import Bot
from config import OWNER_ID, CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, LOGGER, LOG_FILE_NAME
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
    if response.status_code == 401:
        print("Access token expired.")
        return True
    elif response.status_code != 200:
        print(f"Error checking token: {response.text}")
        return True
    return False

# Get a valid access token
def get_access_token():
    if is_access_token_expired():
        new_token = refresh_access_token()
        if not new_token:
            print("⚠️ Failed to refresh access token. Check refresh token.")
            return None
        return new_token
    return os.getenv("ACCESS_TOKEN", ACCESS_TOKEN)

# Function to extract tags from filename
def extract_tags(filename):
    base_name = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_name)[0]

    # Extract season and episode
    parts = name_without_ext.replace('-', '').replace('@', '').split()
    tags = parts + ['btth', 'Battle Through The Heavens', 'DonghuaWillow']

    return tags

# Function to download file in chunks
def download_file_in_chunks(url, file_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):  # 8 KB chunks
                if chunk:
                    f.write(chunk)

# Start command
@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(client, message):
    await message.reply("✅ Bot is working! Send an MKV video to upload.")

# Handle MKV video uploads
@Bot.on_message(filters.user(OWNER_ID) & (filters.video | filters.document))
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        video_file = await message.download()

        # Instead of loading the full video into memory, save it in chunks to disk
        temp_video_path = "temp_video.mkv"  # Temp path for video download
        download_file_in_chunks(message.video.file_id, temp_video_path)
        
        file_name = os.path.basename(temp_video_path)
        title = file_name.split('.')[0]

        # Generate a dynamic description
        if "EP" in title:
            episode_number = title.split("EP")[-1]
            description = f"Episode {episode_number} of Battle Through The Heavens. Watch now!"
        else:
            description = "Battle Through The Heavens episode."

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
            os.remove(temp_video_path)
            return

        upload_link = upload_response.json()["upload_url"]

        # Step 2: Upload the file in chunks
        with open(temp_video_path, "rb") as file:
            files = {"file": file}
            upload_video_response = requests.post(upload_link, files=files)

        if upload_video_response.status_code == 200:
            video_data = upload_video_response.json()
            video_url = video_data.get("url")

            if not video_url:
                await message.reply(f"❌ Video upload failed.\nResponse: {video_data}")
                os.remove(temp_video_path)
                return

            # Step 3: Create video entry on Dailymotion
            create_video_url = "https://api.dailymotion.com/me/videos"
            tags = extract_tags(file_name)
            video_metadata = {
                "title": title,
                "description": description,
                "url": video_url,
                "published": "true",
                "is_created_for_kids": "false",
                "channel": "tv",  # Correct usage of media.category as per the API documentation
                "tags": ",".join(tags)
            }

            create_response = requests.post(create_video_url, headers=headers, data=video_metadata)

            if create_response.status_code == 200:
                video_id = create_response.json().get("id")
                video_embedded_link = f"https://www.dailymotion.com/embed/video/{video_id}"

                # Send embedded video link in code format to your private messages
                await client.send_message(
                    OWNER_ID, 
                    f"✅ Video uploaded successfully! 🎉\n\nHere is your embedded video link:\n`{video_embedded_link}`"
                )

                # Inform the user
                await message.reply(f"✅ Video uploaded successfully! 🎉\nWatch it here: https://www.dailymotion.com/video/{video_id}")
            else:
                await message.reply(f"❌ Failed to create video entry.\nError: {create_response.text}")
                os.remove(temp_video_path)
        else:
            await message.reply(f"❌ Error uploading the video.\nError: {upload_video_response.text}")
            os.remove(temp_video_path)
    else:
        await message.reply("⚠️ Please send an MKV video file.")

# Function to handle thumbnail setting
@Bot.on_message(filters.user(OWNER_ID) & filters.photo)
async def handle_thumbnail(client, message):
    thumbnail_file = await message.download()

    # Get the video file associated with the uploaded video
    video_file = "path_to_video_file.mkv"  # You'll need to associate this with the video message somehow
    video_id = "video_id_from_dailymotion"  # Get this ID after video creation

    # Dailymotion API requires thumbnail to be a square image of 1280x720 resolution.
    thumbnail_url = f"https://api.dailymotion.com/video/{video_id}/thumbnail"
    with open(thumbnail_file, "rb") as thumb:
        files = {"thumbnail": thumb}
        response = requests.post(thumbnail_url, files=files)

    if response.status_code == 200:
        await message.reply("✅ Thumbnail set successfully!")
    else:
        await message.reply(f"❌ Failed to set thumbnail.\nError: {response.text}")
    os.remove(thumbnail_file)
