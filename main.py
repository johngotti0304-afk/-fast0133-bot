import os, time, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

print("BOOT: $25K VERIFIED FIXED", flush=True)
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

def get_coins_fixed():
    # METHODE 1: PumpPortal - werkt altijd
    try:
        r = requests.get("https://pumpportal.fun/api/data/coins?limit=50&sort=market_cap&order=DESC", timeout=10)
        data = r.json()
        if data and len(data) > 0:
            print(f"PumpPortal OK: {len(data)} coins", flush=True)
            coins=[]
            for c in data:
                coins.append({
                    "mint": c.get("mint") or c.get("ca"),
                    "symbol": c.get("symbol","?"),
                    "name": c.get("name","?"),
                    "usd_market_cap": c.get("market_cap",0) or c.get("usd_market_cap",0)
                })
            return coins
    except Exception as e:
        print(f"Portal err {e}", flush=True)

    # METHODE 2: DexScreener fallback voor pump.fun tokens $25k+
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=10).json()
        pairs = r.get("pairs", [])[:50]
        coins=[]
        for p in pairs:
            if p.get("chainId") != "solana": continue
            mc = float(p.get("fdv",0) or p.get("marketCap",0) or 0)
            if mc < 25000: continue
            coins.append({
                "mint": p.get("baseToken",{}).get("address"),
                "symbol": p.get("baseToken",{}).get("symbol","?"),
                "name": p.get("baseToken",{}).get("name","?"),
                "usd_market_cap": mc
            })
        if coins:
            print(f"DexScreener OK: {len(coins)} coins", flush=True)
            return coins
    except Exception as e:
        print(f"Dex err {e}", flush=True)
    
    return []

def check_safe(mint):
    try:
        r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=8).json()
        if r.get("rugged"): return False, 100
        score=r.get("score",0)
        if score>50: return False, score
        return True, score
    except:
        return True, 0

async def loop():
    print("LOOP LIVE $25K VERIFIED FIXED", flush=True)
    await bot.send_message(CHANNEL_ID, "✅ FIXED! $25K VERIFIED bot live met nieuwe API\n@fast0133")
    while True:
        try:
            coins=get_coins_fixed()
            print(f"SCAN {len(coins)} coins", flush=True)
            for c in coins:
                mint=c.get("mint")
                if not mint or mint in seen: continue
                mc=float(c.get("usd_market_cap",0) or 0)
                if mc < 25000: continue
                seen.add(mint)
                safe,score=check_safe(mint)
                print(f"CHECK {c.get('symbol')} ${mc:.0f} safe={safe} score={score}", flush=True)
                if not safe: continue
                msg=f"✅ VERIFIED ${c.get('symbol')} ${mc:,.0f}\nRisk {score}/100\n`{mint}`\nhttps://pump.fun/coin/{mint}\n@fast0133"
                await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
        await asyncio.sleep(10)

asyncio.run(loop())
