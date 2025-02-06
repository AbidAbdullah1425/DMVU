import time
import requests
import random
from datetime import datetime, timedelta

# Telegram Bot Token
BOT_TOKEN = "7708810325:AAFI883rABgcJgh99OVZD4_CoDg1LU4IlBo"

# Channel ID
CHANNEL_ID = "-1002234026927"

# Message Template (Bot Vibes)
def get_bot_message(count):
    timestamp = datetime.now().strftime("%I:%M %p")  # Bot-style time format
    bot_messages = [
        f"🤖 | **Auto-Update** | {timestamp}\n🔥 Battle Through The Heavens Eng Sub - Stay Tuned!",
        f"🔄 Fetching latest updates... | {timestamp}\n🔥 New episode details coming soon!",
        f"⚡ System Alert | {timestamp}\n🔥 Scheduled Update in Progress...",
        f"🤖 Processing... | {timestamp}\n🔥 Stay tuned for more anime episodes!",
        f"📡 Auto Broadcast | {timestamp}\n🔥 Don't miss the next release!"
    ]
    return bot_messages[count % len(bot_messages)]  # Rotate messages

# Number of messages per day
TOTAL_MESSAGES = 50  

# Time range (10 PM - 6 AM)
START_HOUR = 22
END_HOUR = 6  

# Send Message Function
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    response_data = response.json()
    
    if response.status_code == 200:
        message_id = response_data["result"]["message_id"]
        print(f"✅ Sent message at {datetime.now().strftime('%I:%M %p')}: {text}")
        return message_id
    else:
        print(f"❌ Error: {response.text}")
        return None

# Delete Message Function
def delete_message(message_id):
    time.sleep(3600)  # Wait 1 hour before deleting
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    data = {"chat_id": CHANNEL_ID, "message_id": message_id}
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print(f"✅ Deleted message ID: {message_id}")
    else:
        print(f"❌ Failed to delete message ID: {message_id}")

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

# Main Script
message_times = get_random_times()

for i, msg_time in enumerate(message_times):
    now = datetime.now()
    wait_time = (msg_time - now).total_seconds()
    
    if wait_time > 0:
        print(f"⏳ Waiting until {msg_time.strftime('%I:%M %p')} to send message {i+1}/{TOTAL_MESSAGES}")
        time.sleep(wait_time)  # Wait until the next scheduled message

    message_text = get_bot_message(i)  # Get bot-style message
    message_id = send_message(message_text)
    
    if message_id:
        delete_message(message_id)  # Schedule deletion after 1 hour

print("✅ All 50 messages sent for today!")
