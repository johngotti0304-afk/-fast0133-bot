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
        self.wfile.write(b"FAST0133 Bot $20K LIVE")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = set()

def get_tokens():
    try:
        r = requests.get("https://frontend-api.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=false", timeout=10).json()
        return r
    except:
        return []

def get_risk(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=5).json()
        return r.get("score", 0)
    except:
        return 0

async def main():
    await bot.send_message(chat_id=CHANNEL_ID, text="🚀 FAST0133 LIVE op $20K+ MC\nAlleen sterke runners!\n@fast0133")
    print("LIVE $20K MODE")
    while True:
        tokens = get_tokens()
        print(f"Scan {len(tokens)} coins")
        for t in tokens:
            mint = t.get("mint")
            if not mint or mint in seen: continue
            seen.add(mint)
            
            mc = t.get("usd_market_cap", 0)
            name = t.get("name","")
            symbol = t.get("symbol","")
            created = t.get("created_timestamp",0)
            age_min = (time.time()*1000 - created)/60000 if created else 999
            
            # FILTERS $20K
            if mc < 20000: continue
            if age_min > 60: continue  # max 1 uur oud
            
            risk = get_risk(mint)
            if risk > 50: 
                print(f"Skip {symbol} risk {risk}")
                continue
            
            msg = f"🔥 ${symbol} is pumping!\n\nName: {name}\nMC: ${mc:,.0f}\nAge: {age_min:.0f}m | Risk: {risk}/100\n\nCA:\n`{mint}`\n\nChart: https://pump.fun/coin/{mint}\nRug: https://rugcheck.xyz/tokens/{mint}\n\n@fast0133"
            
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
                print(f"POSTED {symbol} ${mc}")
            except Exception as e:
                print(f"TG error {e}")
                
        await asyncio.sleep(15)

asyncio.run(main())
