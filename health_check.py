#!/usr/bin/env python3
import os
import sys
import requests
from telegram import Bot

def health_check():
    """Simple health check for the bot"""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN not found")
            return False
            
        bot = Bot(token=token)
        me = bot.get_me()
        print(f"✅ Bot is healthy: @{me.username}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)