import os
from pyrogram import Client, filters
from pymongo import MongoClient
from bot import Bot

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://abidabdullahown7:abidabdullah1425@cluster0.7lgug.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["bot_db"]
settings = db["settings"]

# In-memory cache
cached_sentence = None

def get_sentence():
    global cached_sentence
    if cached_sentence is None:
        # Try to get from MongoDB
        setting = settings.find_one({"key": "saved_sentence"})
        if setting:
            cached_sentence = setting["value"]
    return cached_sentence

def save_sentence(sentence):
    global cached_sentence
    cached_sentence = sentence
    # Update MongoDB
    settings.update_one(
        {"key": "saved_sentence"},
        {"$set": {"value": sentence}},
        upsert=True
    )

@Bot.on_message(filters.command("start"))
async def start_command(client, message):
    # Check if there's additional text after /start
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) > 1:
        # Save the sentence
        sentence = command_parts[1]
        save_sentence(sentence)
        await message.reply(f"Saved: {sentence}")
    else:
        # Show the saved sentence
        sentence = get_sentence()
        if sentence:
            await message.reply(f"Saved sentence: {sentence}")
        else:
            await message.reply("No sentence saved yet. Use '/start your sentence' to save one.")
