import os, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

MIN_MC = 25000
MAX_MC = 90000
MIN_VOL = 600
MIN_TX = 12

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"VERIFIED BOT LIVE")
    def log_message(self,*a): return

threading.Thread(target=lambda: HTTPServer(("0.0.0.0",PORT),H).serve_forever(), daemon=True).start()
bot = Bot(token=BOT_TOKEN)
seen = set()

def verified_rugcheck(mint):
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code != 200:
            return False, 999, "API fail"
        j = r.json()
        if j.get("rugged"):
            return False, 100, "RUGGED"
        score = j.get("score", 100) or 100
        if score > 25:
            return False, score, f"Score {score} te hoog"

        risks = j.get("risks") or []
        for rk in risks:
            lvl = rk.get("level")
            name = (rk.get("name","") or "").lower()
            desc = (rk.get("description","") or "").lower()
            # BLOCK neppe coins
            if lvl == "danger":
                if "mint" in name or "mint" in desc:
                    return False, score, "Mint auth nog aan"
                if "freeze" in name or "freeze" in desc:
                    return False, score, "Freeze auth"
                if "top holders" in name:
                    return False, score, "Top holders te hoog"
                if "single holder" in name:
                    return False, score, "1 holder owns alles"
                if "low liquidity" in name:
                    return False, score, "Te lage liq"

        # Extra legit checks
        token = j.get("tokenMeta", {}) or {}
        if token.get("mutable") is True:
            # mutable mag wel bij pump maar check extra
            pass

        return True, score, "LEGIT"
    except Exception as e:
        return False, 999, f"ERR {e}"

def get_candidates():
    try:
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun", timeout=15)
        return r.json().get("pairs", [])[:80]
    except:
        return []

async def loop():
    print("VERIFIED LEGIT BOT LIVE", flush=True)
    try:
        await bot.send_message(CHANNEL_ID, "✅ VERIFIED LEGIT BOT LIVE\nAlleen geverifieerde coins 25k-90k\n@fast0133")
    except: pass
    while True:
        try:
            for p in get_candidates():
                if p.get("chainId") != "solana": continue
                mc = float(p.get("fdv",0) or 0)
                vol = float(p.get("volume",{}).get("m5",0) or 0)
                tx = (p.get("txns",{}).get("m5",{}).get("buys",0) or 0) + (p.get("txns",{}).get("m5",{}).get("sells",0) or 0)
                sym = p.get("baseToken",{}).get("symbol","?")

                if not (MIN_MC <= mc <= MAX_MC): continue
                if vol < MIN_VOL: continue
                if tx < MIN_TX: continue

                mint = p["baseToken"]["address"]
                if mint in seen: continue

                ok, score, reason = verified_rugcheck(mint)
                print(f"CHECK {sym} MC {mc:.0f} VOL {vol:.0f} -> {reason} SCORE {score} OK {ok}", flush=True)
                if not ok: continue

                seen.add(mint)
                axiom = f"https://axiom.trade/pulse/{mint}"
                pump = f"https://pump.fun/coin/{mint}"
                msg = (
                    f"✅ VERIFIED LEGIT ${sym}\n"
                    f"MC ${mc:,.0f} | VOL ${vol:,.0f} | TX {tx}\n"
                    f"RISK SCORE {score}/100 LEGIT\n\n"
                    f"`{mint}`\n\n"
                    f"Axiom {axiom}\n"
                    f"Pump {pump}\n"
                    f"Dex {p['url']}"
                )
                try:
                    await bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
                except: pass
                await asyncio.sleep(1)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
        await asyncio.sleep(8)

asyncio.run(loop())
