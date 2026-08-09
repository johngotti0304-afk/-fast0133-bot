import os, asyncio, requests, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.environ.get("PORT", 10000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"FAST0133 Bot is LIVE")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

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
        url = f"https://api.rugcheck.xyz/v1/tokens/{mint}/report"
        r = requests.get(url, timeout=10).json()
        return r.get("score", 100)
    except:
        return 100

async def main():
    await bot.send_message(chat_id=CHANNEL_ID, text="FAST0133 Scanner LIVE! (met webserver)")
    print("Scanner gestart")
    while True:
        tokens = get_new_tokens()
        for t in tokens:
            mint = t.get("mint")
            if not mint or mint in seen:
                continue
            seen.add(mint)
            name = t.get("name","?")
            symbol = t.get("symbol","?")
            mc = t.get("usd_market_cap",0)
            created = t.get("created_timestamp",0)
            age_min = (time.time()*1000 - created)/1000/60
            if age_min > 3:
                continue
            if mc < 2000:
                continue
            risk = rugcheck(mint)
            if risk > 35:
                continue
            text = f"NEW: {name} ({symbol})\nMC: {mc:.0f} Age: {age_min:.1f}m Risk: {risk}\nCA: {mint}\nhttps://pump.fun/coin/{mint}\nhttps://rugcheck.xyz/tokens/{mint}\n@fast0133"
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=text)
                print(f"Posted {symbol}")
            except Exception as e:
                print(e)
        await asyncio.sleep(12)

asyncio.run(main())
