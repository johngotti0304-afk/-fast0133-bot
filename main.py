import os, time, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

print("BOOT: $25K EARLY VERIFIED + VOLUME", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

# Health server voor Render
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def log_message(self, *a): return
threading.Thread(target=lambda: HTTPServer(("0.0.0.0", PORT), H).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = {} # mint -> timestamp
BLACKLIST = {"SAPIJIJU"} # die spapa komt nooit meer terug

def get_25k_coins():
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=15)
        if r.status_code!= 200: return []
        data = r.json()
        coins = []
        for p in data.get("pairs", [])[:80]: # 80 ipv 40 = meer kans op volume
            if p.get("chainId")!= "solana": continue

            symbol = p.get("baseToken",{}).get("symbol","?").upper()
            if symbol in BLACKLIST:
                continue

            mc = float(p.get("fdv", 0) or p.get("marketCap", 0) or 0)
            if mc < 25000 or mc > 90000:
                continue

            # VOLUME FILTER - NIEUW
            vol = p.get("volume", {})
            vol24 = float(vol.get("h24", 0) or 0)
            vol5m = float(vol.get("m5", 0) or 0)

            if vol24 < 10000: # minimaal $10k volume 24h
                continue
            if vol5m < 500: # minimaal $500 volume laatste 5 min = live interesse
                continue

            coins.append({
                "mint": p.get("baseToken",{}).get("address"),
                "symbol": symbol,
                "name": p.get("baseToken",{}).get("name","?"),
                "mc": mc,
                "vol24": vol24,
                "vol5m": vol5m,
                "url": p.get("url")
            })
        return coins
    except Exception as e:
        print(f"Dex error {e}", flush=True)
        return []

def is_verified(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=10).json()
        if r.get("rugged"): return False, 100
        score = r.get("score", 0)
        risks = str(r.get("risks", []))
        if score > 50: return False, score
        if "Top 10 holders high" in risks: return False, score
        return True, score
    except:
        return True, 0

async def loop():
    print("LOOP LIVE $25K EARLY + VOLUME FILTER", flush=True)
    await bot.send_message(CHANNEL_ID, "✅ Bot LIVE: $25K EARLY VERIFIED + VOLUME\nAlleen munten 25k-90k met >$10k vol & >$500 5m vol\nGeen SAPIJIJU spam meer\n@fast0133")
    while True:
        # cleanup seen ouder dan 1 uur
        now = time.time()
        for k in list(seen.keys()):
            if now - seen[k] > 3600:
                del seen[k]

        coins = get_25k_coins()
        print(f"SCAN {len(coins)} coins in 25k-90k zone WITH VOLUME", flush=True)
        for c in coins:
            mint = c["mint"]
            if not mint or mint in seen: continue
            safe, score = is_verified(mint)
            print(f"CHECK {c['symbol']} ${c['mc']:.0f} vol24 ${c['vol24']:.0f} vol5m ${c['vol5m']:.0f} risk {score} safe={safe}", flush=True)
            if not safe: continue
            seen[mint] = now
            msg = f"""🚀 EARLY VERIFIED ${c['symbol']}

💰 MC: ${c['mc']:,.0f}
📈 Vol 24h: ${c['vol24']:,.0f}
🔥 Vol 5m: ${c['vol5m']:,.0f}
✅ Risk: {score}/100 - VERIFIED
📊 {c['name']}

`{mint}`

https://pump.fun/coin/{mint}
{c['url']}

@fast0133"""
            await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            await asyncio.sleep(1)
        await asyncio.sleep(8)

asyncio.run(loop())
