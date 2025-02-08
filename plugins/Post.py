from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from config import TG_BOT_TOKEN, API_ID, API_HASH, OWNER_ID
from bot import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNELS = ["@HeavenlySubs]

# Temporary storage for user input
user_data = {}

async def reset_user_data(user_id):
    """
    Function to reset user data after the process is complete
    """
    if user_id in user_data:
        user_data.pop(user_id)

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_handler(client, message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    # Check if user is in the process
    if user_id not in user_data or "in_progress" not in user_data[user_id]:
        return  # Ignore irrelevant inputs

    try:
        # Check if the user provided episode number
        episode_number = user_input.split()[1] if len(user_input.split()) > 1 else None
        if not episode_number or not episode_number.isdigit():
            return  # No reply, just exit

        episode_number = int(episode_number)
        if episode_number < 1 or episode_number > 500:
            return  # No reply, just exit

        # Get anime title and cover image
        anime_title = user_data[user_id]["anime_title"]
        anime_cover_url = user_data[user_id]["anime_cover_url"]
        
        # Ask for the button URL
        await message.reply("Please send the URL for the button (starting with http:// or https://).")

        user_data[user_id]["episode"] = episode_number
        user_data[user_id]["in_progress"] = False  # Mark the process as completed
        
        # After URL is provided by the user, the bot will send the final post
    except Exception as e:
        logger.exception("An error occurred while processing the /post command.")

@Bot.on_message(filters.text & filters.private & filters.user(OWNER_ID))
async def url_handler(client, message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    # Check if user is in the process
    if user_id not in user_data or "episode" not in user_data[user_id] or "in_progress" in user_data[user_id]:
        return  # Ignore irrelevant inputs

    # Check for URL input
    if user_input.startswith("http://") or user_input.startswith("https://"):
        # Get anime title, episode, and URL for button
        anime_title = user_data[user_id]["anime_title"]
        episode_number = user_data[user_id]["episode"]
        anime_cover_url = https://raw.githubusercontent.com/AbidAbdullah1425/DMVU/refs/heads/Alpha/assist/20250208_132017.jpg
        
        button_url = user_input
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ •", url=button_url)]]
        )

        # Send the final post to the channels
        post_text = (
    f"**☗   {anime_title}**\n\n"
    f"**⦿   Ratings: 9.8**\n"
    f"**⦿   Status: Airing**\n"
    f"**⦿   Episode: `{episode_number}`**\n"
    f"**⦿   Quality: 720p**\n"
    f"**⦿   Genres: `Action`, `Adventure`, `Harem`, `Romance`, `Cultivation`**\n\n"
    f"**◆   Synopsis : In a land where no magic is present. A land where the strong make the rules and weak have to obey...** [Read More](https://myanimelist.net/anime/36491/Doupo_Cangqiong)\n\n"
)



        # Send the post to each channel
        for channel in CHANNELS:
            try:
                await client.send_photo(
                    chat_id=channel,
                    photo=anime_cover_url,
                    caption=post_text,
                    reply_markup=button
                )
            except Exception as e:
                logger.error("Failed to post to %s: %s", channel, e)

        logger.info("Post created and sent to channels!")

        # Reset user data after completion
        await reset_user_data(user_id)

    else:
        await message.reply("Invalid URL. Please provide a valid URL (starting with http:// or https://).")
