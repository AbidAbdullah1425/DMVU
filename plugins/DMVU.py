from pyrogram import Client, filters
import requests
import os


# Handle receiving video or document
@Bot.on_message(filters.user(OWNER_ID) & filters.document & filters.video)
async def handle_video(client, message):
    if message.video or (message.document and message.document.file_name.endswith('.mkv')):
        # Handle video file
        video_file = await message.download()
        file_name = os.path.basename(video_file)
        title = file_name.split('.')[0]  # Title is taken from the file name

        # Notify the user that the upload has started
        await message.reply("Uploading your video to Dailymotion...")

        # Upload video to Dailymotion
        upload_url = "https://api.dailymotion.com/file/upload"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
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
                # Stop listening for tags after the operation is complete
                app.remove_handler(handle_tags)

        else:
            await message.reply("Error during video upload. Please try again.")
            # Clean up the downloaded file
            os.remove(video_file)

    else:
        await message.reply("Please send a video (MKV format) to upload.")

