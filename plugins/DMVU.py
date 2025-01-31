import requests
import os
from pyrogram import filters
from bot import Bot
from config import OWNER_ID, CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN

# Add a /start command to check if the bot is working
@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_command(client, message):
    await message.reply("Bot is working! Send me a video to upload to Dailymotion.")


# Helper function to refresh the access token using the refresh token
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
        # Extract the new access token from the response
        new_access_token = response.json().get('access_token')
        if new_access_token:
            # Update the ACCESS_TOKEN variable or store it securely
            os.environ["ACCESS_TOKEN"] = new_access_token  # Or use any secure storage method
            return new_access_token
        else:
            raise Exception("Failed to retrieve the access token.")
    else:
        raise Exception(f"Error refreshing access token: {response.status_code}, {response.text}")


# Use the refresh_access_token function if the access token has expired
def get_access_token():
    access_token = os.getenv("ACCESS_TOKEN")  # Fetch from environment variable or use your preferred method

    # If the access token is invalid or expired, refresh it
    if not access_token or access_token_is_expired():
        access_token = refresh_access_token()

    return access_token


# Helper function to check if the access token is expired (useful for API error checks)
def access_token_is_expired():
    try:
        # Make a test request to verify the token's validity
        url = "https://api.dailymotion.com/me"
        headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:  # 401 means unauthorized, likely due to expired token
            return True
        return False
    except requests.RequestException:
        return True


# Now, update your bot's video upload handler
@Bot.on_message(filters.user(OWNER_ID) & filters.document & filters.video)
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        # Handle video file
        video_file = await message.download()
        file_name = os.path.basename(video_file)
        title = file_name.split('.')[0]  # Title is taken from the file name

        # Notify the user that the upload has started
        await message.reply("Uploading your video to Dailymotion...")

        # Get the valid access token (refresh if expired)
        access_token = get_access_token()

        # Upload video to Dailymotion
        upload_url = "https://api.dailymotion.com/file/upload"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        files = {
            'file': open(video_file, 'rb')
        }

        response = requests.post(upload_url, headers=headers, files=files)

        # Check if upload is successful
        if response.status_code == 200:
            video_id = response.json()['id']
            upload_progress_url = f"https://api.dailymotion.com/video/{video_id}"

            # Wait for video to finish processing and get its metadata
            video_metadata = requests.get(upload_progress_url, headers=headers).json()

            # Prompt user to add tags
            await message.reply("The video has been uploaded! Please send tags separated by commas.")

            # Listen for the tags response
            @Bot.on_message(filters.user(OWNER_ID) & filters.text)
            async def handle_tags(client, message):
                tags = message.text.split(",")  # Tags are taken from user input
                video_title = title
                video_description = video_title

                # Now that the video is uploaded, set the metadata
                video_metadata_update_url = f"https://api.dailymotion.com/video/{video_id}"
                video_metadata_params = {
                    'title': video_title,
                    'description': video_description,
                    'tags': ",".join(tags),
                }

                update_response = requests.post(video_metadata_update_url, headers=headers, data=video_metadata_params)

                if update_response.status_code == 200:
                    await message.reply(f"Video uploaded successfully: {video_metadata['url']}")
                else:
                    await message.reply("Failed to update video metadata.")

                # Clean up the downloaded file
                os.remove(video_file)

        else:
            await message.reply("Error during video upload. Please try again.")
            # Clean up the downloaded file
            os.remove(video_file)

    else:
        await message.reply("Please send a video (MKV format) to upload.")
