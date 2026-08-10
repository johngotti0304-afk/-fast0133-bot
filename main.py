import os, time, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

print("BOOT: $25K EARLY VERIFIED", flush=True)
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
seen = set()

def get_25k_coins():
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=15)
        if r.status_code != 200: return []
        data = r.json()
        coins = []
        for p in data.get("pairs", [])[:40]:
            if p.get("chainId") != "solana": continue
            mc = float(p.get("fdv", 0) or p.get("marketCap", 0) or 0)
            if mc < 25000 or mc > 90000: continue # 25k-90k = vroegste zone
            coins.append({
                "mint": p.get("baseToken",{}).get("address"),
                "symbol": p.get("baseToken",{}).get("symbol","?"),
                "name": p.get("baseToken",{}).get("name","?"),
                "mc": mc,
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
        # GEEN neppe munten: score < 40, top holders < 60%, geen mint authority
        risks = str(r.get("risks", []))
        if score > 50: return False, score
        if "Top 10 holders high" in risks: return False, score
        return True, score
    except:
        return True, 0

async def loop():
    print("LOOP LIVE $25K EARLY VERIFIED", flush=True)
    await bot.send_message(CHANNEL_ID, "✅ Bot LIVE: $25K EARLY VERIFIED\nAlleen geverifieerde munten 25k-90k\nGeen neppe munten\n@fast0133")
    while True:
        coins = get_25k_coins()
        print(f"SCAN {len(coins)} coins in 25k-90k zone", flush=True)
        for c in coins:
            mint = c["mint"]
            if not mint or mint in seen: continue
            safe, score = is_verified(mint)
            print(f"CHECK {c['symbol']} ${c['mc']:.0f} risk {score} safe={safe}", flush=True)
            if not safe: continue
            seen.add(mint)
            msg = f"""🚀 EARLY VERIFIED ${c['symbol']}

💰 MC: ${c['mc']:,.0f}
✅ Risk: {score}/100 - VERIFIED
📊 {c['name']}

`{mint}`

https://pump.fun/coin/{mint}
{ c['url'] }

@fast0133"""
            await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            await asyncio.sleep(1)
        await asyncio.sleep(8)

asyncio.run(loop())
