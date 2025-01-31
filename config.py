
import os
import logging
from logging.handlers import RotatingFileHandler

API_ID = int(os.environ.get("API_ID", "26254064"))
API_HASH = os.environ.get("API_HASH", "72541d6610ae7730e6135af9423b319c")
OWNER_ID = int(os.environ.get("OWNER_ID", "5296584067"))
BOT_TOKEN = '0'

# Dailymotion API credentials
CLIENT_ID = '8fc35d2179736e12a797'
CLIENT_SECRET = '3f999282f562df4d2e890ee38a7bc659c5c1edf1'
ACCESS_TOKEN = "czhIS2EYN3p5Hh1RRypnOhkKXwBNREQ4EA0kTFYhIiEO"  # New Access Token
REFRESH_TOKEN = "274f209725e532615d9c77c933614b2633243257"  # New Refresh Token


ADMINS.append(OWNER_ID)
ADMINS.append(5296584067)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
