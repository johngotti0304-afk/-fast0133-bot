import os, asyncio, requests, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

print("=== STARTING BOT ===")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
print(f"Token exists: {bool(BOT_TOKEN)}")
print(f"Channel: {CHANNEL_ID}")

if not BOT_TOKEN or not CHANNEL_ID:
    print("ERROR: BOT_TOKEN of CHANNEL_ID mist!")
    # blijf draaien zodat Render niet crasht
    while True: time.sleep(60)

from telegram import Bot

PORT = int(os.environ.get("PORT", 10000))
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"FAST0133 $20K LIVE")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", PORT), Handler).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = set()

def get_tokens():
    try:
        url = "https://frontend-api-v3.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        # v3 geeft andere format, fallback naar v2
        if isinstance(r, list): return r
        return r.get("coins", [])
    except Exception as e:
        print(f"API error {e}")
        return []

async def main():
    print("=== SCANNER START $20K ===")
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text="FAST0133 LIVE $20K+")
        print("Telegram OK")
    except Exception as e:
        print(f"TELEGRAM ERROR: {e} - Check of bot admin is in @fast0133!")
        return

    while True:
        tokens = get_tokens()
        print(f"Scan: {len(tokens)} coins gevonden")
        for t in tokens:
            mint = t.get("mint")
            if not mint or mint in seen: continue
            seen.add(mint)
            mc = float(t.get("usd_market_cap",0) or 0)
            if mc < 20000: continue
            print(f"FOUND $20K: {t.get('symbol')} MC {mc}")
            msg = f"🔥 ${t.get('symbol')} ${mc:,.0f}\nCA: `{mint}`\nhttps://pump.fun/coin/{mint}\n@fast0133"
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Send error {e}")
        await asyncio.sleep(10)

asyncio.run(main())
