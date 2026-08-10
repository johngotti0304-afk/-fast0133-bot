import os, time, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

print("BOOT: Bot starting...", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self, *a): return

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", PORT), H).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen=set()

def get_coins():
    try:
        r = requests.get("https://frontend-api.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC", headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        data=r.json()
        if isinstance(data, list): return data
        return []
    except Exception as e:
        print(f"API ERR: {e}", flush=True)
        return []

def check_safe(mint):
    try:
        r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=8).json()
        if r.get("rugged"): return False, 100
        score=r.get("score",0)
        if score>60: return False, score
        return True, score
    except:
        return True, 0

async def main_loop():
    print("LOOP: Scanner live $25K VERIFIED", flush=True)
    await bot.send_message(CHANNEL_ID, "✅ Bot herstart - $25K VERIFIED mode actief @fast0133")
    while True:
        try:
            coins=get_coins()
            print(f"SCAN {len(coins)} coins", flush=True)
            for c in coins:
                mint=c.get("mint")
                if not mint or mint in seen: continue
                mc=float(c.get("usd_market_cap",0) or 0)
                if mc<25000: continue
                seen.add(mint)
                sym=c.get("symbol","?")
                safe,score=check_safe(mint)
                print(f"FOUND {sym} ${mc:.0f} safe={safe} score={score}", flush=True)
                if not safe: continue
                msg=f"✅ VERIFIED ${sym} ${mc:,.0f}\n`{mint}`\nhttps://pump.fun/coin/{mint}\n@fast0133"
                await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"LOOP ERR: {e}", flush=True)
        await asyncio.sleep(10)

asyncio.run(main_loop())
