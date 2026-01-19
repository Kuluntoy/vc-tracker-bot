import subprocess
import time
import os

BOT_FILE = "bot.py"

while True:
    try:
        # Run the bot
        subprocess.run(["python", BOT_FILE])
    except Exception as e:
        # If something goes wrong, print the error (optional)
        print(f"Bot crashed: {e}")
    
    # Wait a few seconds before restarting
    time.sleep(5)