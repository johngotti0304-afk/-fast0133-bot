import os, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

# Filter instellingen BESTE kwaliteit
MIN_MC = 25000
MAX_MC = 90000
MIN_VOL_M5 = 500  # op 500 voor test, zet later op 1000 voor beste
MIN_TX = 10
MAX_RUG_SCORE = 35

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"BOT LIVE")
    def log_message(self,*a): return

threading.Thread(target=lambda: HTTPServer(("0.0.0.0",PORT),Health).serve_forever(), daemon=True).start()

bot = Bot(token=BOT_TOKEN)
seen = set()

def get_pairs():
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=15)
        return r.json().get("pairs", [])[:80]
    except: return []

def rugcheck_ok(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code != 200: return True, 0
        j = r.json()
        if j.get("rugged"): return False, 100
        score = j.get("score",0) or 0
        if score > MAX_RUG_SCORE: return False, score
        # extra checks voor neppe coins
        risks = j.get("risks", []) or []
        for risk in risks:
            name = risk.get("name","").lower()
            if "top holders" in name and risk.get("level")=="danger": return False, score
            if "mint authority" in name and risk.get("level")=="danger": return False, score
        return True, score
    except:
        return True, 0

def is_best_coin(p):
    if p.get("chainId") != "solana": return None
    mc = float(p.get("fdv",0) or p.get("marketCap",0) or 0)
    vol = float(p.get("volume",{}).get("m5",0) or 0)
    tx = (p.get("txns",{}).get("m5",{}).get("buys",0) or 0) + (p.get("txns",{}).get("m5",{}).get("sells",0) or 0)
    if not (MIN_MC <= mc <= MAX_MC): return None
    if vol < MIN_VOL_M5: return None
    if tx < MIN_TX: return None
    return {"mint":p["baseToken"]["address"],"symbol":p["baseToken"]["symbol"],"mc":mc,"vol":vol,"tx":tx,"url":p["url"]}

async def loop():
    print("BEST MEME BOT LIVE", flush=True)
    try:
        await bot.send_message(CHANNEL_ID, "BEST MEME BOT LIVE\n25k-90k | VOL>500 | Axiom Ready\n@fast0133")
    except: pass
    while True:
        try:
            count=0
            for p in get_pairs():
                c = is_best_coin(p)
                if not c: continue
                m = c["mint"]
                if m in seen: continue
                safe, score = rugcheck_ok(m)
                print(f"CHECK {c['symbol']} MC {c['mc']:.0f} VOL {c['vol']:.0f} SCORE {score} SAFE {safe}", flush=True)
                if not safe: continue
                seen.add(m)
                count+=1
                # Axiom + Photon + Dex links
                axiom_link = f"https://axiom.trade/pulse/{m}"
                pump_link = f"https://pump.fun/coin/{m}"
                msg = (
                    f"ROCKET BEST ${c['symbol']}\n"
                    f"MC ${c['mc']:,.0f} | VOL ${c['vol']:,.0f} | TX {c['tx']}\n"
                    f"RISK {score}/100 BEST\n\n"
                    f"`{m}`\n\n"
                    f"Axiom {axiom_link}\n"
                    f"Pump {pump_link}\n"
                    f"Dex {c['url']}"
                )
                try:
                    await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
                except Exception as e:
                    print(f"TG ERR {e}", flush=True)
                await asyncio.sleep(1)
            print(f"SCAN BEST {count} coins", flush=True)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
        await asyncio.sleep(7)

asyncio.run(loop())
