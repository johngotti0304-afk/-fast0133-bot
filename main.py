import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHANNEL_ID, text="✅ Bot @fast0133 is LIVE op Render!")
    print("Bot is live en gepost in kanaal")
    while True:
        await asyncio.sleep(60)

asyncio.run(main())
