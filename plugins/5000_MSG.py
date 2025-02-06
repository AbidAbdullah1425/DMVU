import time
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import Bot

# Channel ID
CHANNEL_ID = "-1002234026927"

# Message Template (Bot Vibes)
def get_bot_message(count):
    timestamp = datetime.now().strftime("%I:%M %p")  # Bot-style time format
    bot_messages = [
        f"🤖 | **System Initialization** | {timestamp}\n⚡ Neural Network Update - Establishing Data Protocols...",
        f"💻 | **File Synchronization** | {timestamp}\n🧠 Accessing Core Memory - Optimizing Subsystems...",
        f"⚡ | **Power-Up Sequence** | {timestamp}\n🔧 Executing Self-Check - All Systems Normal...",
        f"🔄 | **Data Retrieval** | {timestamp}\n🧑‍💻 Querying Global Data Vault - 56% Complete...",
        f"📡 | **Reboot Sequence** | {timestamp}\n⚙️ Resetting Core Environment - Please Stand By...",
        f"🛠️ | **Resource Allocation** | {timestamp}\n🔋 Stabilizing Energy Fields - Cluster Optimization in Progress...",
        f"⚙️ | **Environment Reset** | {timestamp}\n🔒 Securing Data Vault - Cyber Defense Systems Engaged...",
        f"⚡ | **System Check** | {timestamp}\n💾 Integrating New Data Streams - Uploading Files...",
        f"🤖 | **Execution Mode** | {timestamp}\n💻 Finalizing Computational Load - 72% Complete...",
        f"📡 | **Mainframe Loading** | {timestamp}\n🧠 Memory Encrypted - Launching Subsystems in 3...2...1..."
    ]

    return bot_messages[count % len(bot_messages)]  # Rotate messages

# Number of messages per day
TOTAL_MESSAGES = 50  

# Time range (10 PM - 6 AM)
START_HOUR = 22
END_HOUR = 6  

# Send Message Function (Pyrogram version)
async def send_message(text):
    message = await app.send_message(CHANNEL_ID, text)
    print(f"✅ Sent message at {datetime.now().strftime('%I:%M %p')}: {text}")
    return message.message_id

# Delete Message Function
async def delete_message(message_id):
    time.sleep(3600)  # Wait 1 hour before deleting
    await app.delete_messages(CHANNEL_ID, message_id)
    print(f"✅ Deleted message ID: {message_id}")

# Generate Random Message Times
def get_random_times():
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, START_HOUR, 0, 0)
    if now.hour < END_HOUR:  
        start_time -= timedelta(days=1)  # If past midnight, adjust date
    end_time = start_time + timedelta(hours=8)  # 10 PM to 6 AM

    time_slots = [
        start_time + timedelta(seconds=random.randint(0, int((end_time - start_time).total_seconds())))
        for _ in range(TOTAL_MESSAGES)
    ]
    return sorted(time_slots)  # Ensure ordered times

# Progress Bar Simulation
async def progress_bar(message_id, progress=0):
    while progress <= 100:
        progress_text = f"⚡ **System Alert** | Cleaning Storage... {progress}% | {datetime.now().strftime('%I:%M %p')}"
        await app.edit_message_text(CHANNEL_ID, message_id, progress_text)
        progress += random.randint(5, 15)  # Randomize progress for the effect
        await time.sleep(2)  # Wait before updating again

# Start Bot Process Command
@Bot.on_message(filters.command("start_bot"))
async def start_bot(client, message):
    await message.reply("⚡ Starting the bot message process...")

    # Generate message times
    message_times = get_random_times()

    for i, msg_time in enumerate(message_times):
        now = datetime.now()
        wait_time = (msg_time - now).total_seconds()

        if wait_time > 0:
            print(f"⏳ Waiting until {msg_time.strftime('%I:%M %p')} to send message {i+1}/{TOTAL_MESSAGES}")
            time.sleep(wait_time)  # Wait until the next scheduled message

        # Send the message with bot-like action
        message_text = get_bot_message(i)  # Get bot-style message
        message = await send_message(message_text)

        # Simulate a cyborg-like environment with progress bar
        await progress_bar(message.message_id)

        # Delete the message after 1 hour
        await delete_message(message.message_id)

    await message.reply("✅ All 50 messages sent for today!")

