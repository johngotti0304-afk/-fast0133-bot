import os, time, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

class H(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a): return

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", PORT), H).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = set()

def get_best():
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=15)
        out = []
        for p in r.json().get("pairs", [])[:60]:
            if p.get("chainId") != "solana": continue
            mc = float(p.get("fdv",0) or 0)
            vol5 = float(p.get("volume",{}).get("m5",0) or 0)
            tx = p.get("txns",{}).get("m5",{}).get("buys",0) + p.get("txns",{}).get("m5",{}).get("sells",0)
            if mc < 25000 or mc > 90000: continue
            if vol5 < 1000: continue
            if tx < 15: continue
            out.append({"mint": p["baseToken"]["address"], "symbol": p["baseToken"]["symbol"], "mc": mc, "vol": vol5, "tx": tx, "url": p["url"]})
        print(f"SCAN BEST: {len(out)} coins", flush=True)
        return out
    except Exception as e:
        print(f"ERR {e}", flush=True); return []

def is_best(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=10)
        j = r.json()
        if j.get("rugged"): return False, 100
        score = j.get("score", 0)
        if score > 30: return False, score
        return True, score
    except: return True, 0

async def loop():
    await bot.send_message(CHANNEL_ID, "✅ BEST QUALITY BOT LIVE 25k-90k")
    while True:
        for c in get_best():
            m = c["mint"]
            if not m or m in seen: continue
            safe, score = is_best(m)
            print(f"CHECK {c['symbol']} MC {c['mc']:.0f} VOL {c['vol']:.0f} SCORE {score} SAFE {safe}", flush=True)
            if not safe: continue
            seen.add(m)
            msg = f"🚀 BEST QUALITY ${c['symbol']}\n💰 MC: ${c['mc']:,.0f}\n📊 VOL: ${c['vol']:,.0f}\n✅ RISK {score}\n\n`{m}`\nhttps://pump.fun/coin/{m}\n{c['url']}"
            try: await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
            except: pass
            await asyncio.sleep(1)
        await asyncio.sleep(8)

asyncio.run(loop())
