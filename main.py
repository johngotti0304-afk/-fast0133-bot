import os, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHANNEL_ID=os.getenv("CHANNEL_ID")
PORT=int(os.getenv("PORT",10000))

# FIX - VOL/TX op 0 want Dex geeft 0 bij nieuwe coins
MIN_MC=20000
MAX_MC=120000
MIN_VOL=0
MIN_TX=0
MAX_RUG=35

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b"FIXED")
 def log_message(self,*a):return

threading.Thread(target=lambda:HTTPServer(("0.0.0.0",PORT),H).serve_forever(),daemon=True).start()
bot=Bot(token=BOT_TOKEN)
seen=set()

def get_pairs():
 try:
  r=requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun",timeout=15)
  return r.json().get("pairs",[])[:90]
 except Exception as e:
  print(f"Dex ERR {e}",flush=True)
  return []

def rug_ok(mint):
 try:
  r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report",timeout=10,headers={"User-Agent":"Mozilla/5.0"})
  if r.status_code!=200: return True,0
  j=r.json()
  if j.get("rugged"): return False,100
  sc=j.get("score",0) or 0
  if sc>MAX_RUG: return False,sc
  # block top holders danger
  for rk in j.get("risks",[]) or []:
   if rk.get("level")=="danger" and "top holders" in rk.get("name","").lower():
    return False,sc
  return True,sc
 except Exception as e:
  print(f"Rug ERR {e}",flush=True)
  return True,0

async def loop():
 print("FIXED BOT LIVE - VOL 0 FIX",flush=True)
 await bot.send_message(CHANNEL_ID,"FIXED BOT LIVE - Nu VOL 0 dus je gaat coins zien @fast0133")
 while True:
  pairs=get_pairs()
  print(f"Dex pairs {len(pairs)}",flush=True)
  cands=[]
  for p in pairs:
   if p.get("chainId")!="solana": continue
   mc=float(p.get("fdv",0) or 0)
   vol=float(p.get("volume",{}).get("m5",0) or p.get("volume",{}).get("h1",0) or p.get("volume",{}).get("h24",0) or 0)
   tx=(p.get("txns",{}).get("m5",{}).get("buys",0) or 0)+(p.get("txns",{}).get("m5",{}).get("sells",0) or 0)
   if 15000<=mc<=150000:
    print(f"SEEN {p.get('baseToken',{}).get('symbol')} MC {mc:.0f} VOL {vol:.0f} TX {tx}",flush=True)
   if not (MIN_MC<=mc<=MAX_MC): continue
   cands.append((p,mc,vol,tx))
  print(f"Gefilterd {len(cands)} coins MC ok",flush=True)
  cnt=0
  for p,mc,vol,tx in cands:
   mint=p["baseToken"]["address"]
   if mint in seen: continue
   ok,sc=rug_ok(mint)
   print(f"CHECK {p['baseToken']['symbol']} SC {sc} OK {ok}",flush=True)
   if not ok: continue
   seen.add(mint);cnt+=1
   msg=f"FIXED TEST ${p['baseToken']['symbol']} MC ${mc:.0f} VOL ${vol:.0f} TX {tx} RISK {sc}\n`{mint}`\nhttps://axiom.trade/pulse/{mint}\n{p['url']}"
   try: await bot.send_message(CHANNEL_ID,msg,parse_mode="Markdown")
   except Exception as e: print(f"TG ERR {e}",flush=True)
  print(f"SCAN DONE {cnt} nieuw",flush=True)
  await asyncio.sleep(7)

asyncio.run(loop())
