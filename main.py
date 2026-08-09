import os, asyncio, requests, time
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)
seen = set()

def get_new_tokens():
    try:
        url = "https://frontend-api.pump.fun/coins?offset=0&limit=20&sort=created_timestamp&order=DESC"
        r = requests.get(url, timeout=10).json()
        return r
    except Exception as e:
        print(f"API error: {e}")
        return []

def rugcheck(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=10).json()
        return r.get("score", 100)
    except:
        return 100

async def main():
    await bot.send_message(chat_id=CHANNEL_ID, text="🚀 FAST0133 Scanner LIVE!\nFilter: <3min oud | MC > $2K | RugCheck < 35")
    print("Scanner gestart")
    while True:
        tokens = get_new_tokens()
        for t in tokens:
            mint = t.get("mint")
            if not mint or mint in seen: continue
            seen.add(mint)
            name = t.get("name","?")
            symbol = t.get("symbol","?")
            mc = t.get("usd_market_cap",0)
            created = t.get("created_timestamp",0)
            age_min = (time.time()*1000 - created)/1000/60
            if age_min > 3: continue
            if mc < 2000: continue
            risk = rugcheck(mint)
            if risk > 35: continue
            msg = f"🚨 NEW: {name} (${symbol})\n💰 MC: ${mc:,.0f} | Age: {age_min:.1f}m\n🛡️ Risk: {risk}/100\n\nCA: `{mint}`\n[Chart](https://pump.fun/coin/{mint}) | [RugCheck](https://rugcheck.xyz/tokens/{mint})\n\n
