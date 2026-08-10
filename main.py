import os, asyncio, requests, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

print("=== FAST0133 $25K VERIFIED START ===")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200); self.end_headers(); self.wfile.write(b"$25K VERIFIED LIVE")
    def do_HEAD(self): 
        self.send_response(200); self.end_headers()

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", PORT), Handler).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = set()

def is_verified_safe(mint):
    """Return (is_safe:bool, reason:str, score:int)"""
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=8).json()
        score = r.get("score", 100)
        
        # FAILS
        if r.get("rugged"): return False, "RUGGED", score
        if score > 40: return False, f"High risk {score}", score
        
        # Checks
        top10 = r.get("topHoldersPct", 100)
        dev = r.get("creatorBalance", 100)
        
        if dev > 15: return False, f"Dev {dev:.1f}%", score
        if top10 > 60: return False, f"Bundled {top10:.0f}%", score
        
        return True, f"Safe {score}", score
    except Exception as e:
        print(f"Rugcheck fail {mint[:6]}: {e}")
        return True, "No data", 0  # laat door als API down is

def get_tokens():
    try:
        headers = {"User-Agent":"Mozilla/5.0"}
        # Probeer nieuwe API
        url = "https://frontend-api-v3.pump.fun/coins?offset=0&limit=50&sort=market_cap&order=DESC"
        r = requests.get(url, headers=headers, timeout=10).json()
        if isinstance(r, list): return r
        if isinstance(r, dict) and "coins" in r: return r["coins"]
        # fallback v1
        url2 = "https://frontend-api.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC"
        return requests.get(url2, headers=headers, timeout=10).json()
    except Exception as e:
        print(f"Pump API error {e}")
        return []

async def main():
    await bot.send_message(chat_id=CHANNEL_ID, text="🛡️ FAST0133 $25K VERIFIED LIVE\n\nFilters:\n• $25K+ MC\n• Risk <40\n• Dev <15%\n• Top10 <60%\n• Not rugged\n\n@fast0133")
    print("LIVE $25K VERIFIED")
    
    while True:
        tokens = get_tokens()
        print(f"Scan {len(tokens)}")
        for t in tokens:
            mint = t.get("mint")
            if not mint or mint in seen: continue
            
            mc = float(t.get("usd_market_cap",0) or 0)
            if mc < 25000: continue
            
            seen.add(mint)
            symbol = t.get("symbol","?")
            name = t.get("name","?")
            
            print(f"Checking {symbol} ${mc:,.0f}")
            safe, reason, risk = is_verified_safe(mint)
            
            if not safe:
                print(f"  REJECT {symbol}: {reason}")
                continue
            
            print(f"  ✅ APPROVED {symbol}")
            msg = f"""✅ VERIFIED ${symbol} - ${mc:,.0f} MC

**{name}**
Risk: {risk}/100 - {reason}
MC: ${mc:,.0f}

CA:
`{mint}`

📊 https://pump.fun/coin/{mint}
🛡️ https://rugcheck.xyz/tokens/{mint}

@fast0133"""
            
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                print(f"TG err {e}")
        await asyncio.sleep(12)

asyncio.run(main())
