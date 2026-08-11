import os, requests, asyncio, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHANNEL_ID=os.getenv("CHANNEL_ID")
PORT=int(os.getenv("PORT",10000))

# TEST MODE - looser zodat je nu coins ziet
MIN_MC=20000
MAX_MC=120000
MIN_VOL=300
MIN_TX=8
MAX_RUG=40

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b"TEST MODE")
 def log_message(self,*a):return

threading.Thread(target=lambda:HTTPServer(("0.0.0.0",PORT),H).serve_forever(),daemon=True).start()
bot=Bot(token=BOT_TOKEN)
seen=set()

def get_pairs():
 try:
  r=requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun",timeout=15)
  return r.json().get("pairs",[])[:90]
 except: return []

def rug_ok(mint):
 try:
  r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report",timeout=10,headers={"User-Agent":"Mozilla/5.0"})
  if r.status_code!=200: return True,0
  j=r.json()
  if j.get("rugged"): return False,100
  sc=j.get("score",0) or 0
  if sc>MAX_RUG: return False,sc
  return True,sc
 except: return True,0

async def loop():
 print("TEST MODE LIVE - LOOSE FILTER",flush=True)
 await bot.send_message(CHANNEL_ID,"TEST MODE LIVE - FILTER 20k-120k VOL>300 - kijkt of er coins binnenkomen @fast0133")
 while True:
  pairs=get_pairs()
  print(f"Dex pairs {len(pairs)}",flush=True)
  best=[]
  for p in pairs:
   if p.get("chainId")!="solana": continue
   mc=float(p.get("fdv",0) or 0)
   vol=float(p.get("volume",{}).get("m5",0) or 0)
   tx=(p.get("txns",{}).get("m5",{}).get("buys",0) or 0)+(p.get("txns",{}).get("m5",{}).get("sells",0) or 0)
   if 15000<=mc<=150000:
    print(f"SEEN {p.get('baseToken',{}).get('symbol')} MC {mc:.0f} VOL {vol:.0f} TX {tx}",flush=True)
   if not (MIN_MC<=mc<=MAX_MC): continue
   if vol<MIN_VOL: continue
   if tx<MIN_TX: continue
   best.append((p,mc,vol,tx))
  print(f"Gefilterd {len(best)} coins die door MC/VOL/TX komen",flush=True)
  cnt=0
  for p,mc,vol,tx in best:
   mint=p["baseToken"]["address"]
   if mint in seen: continue
   ok,sc=rug_ok(mint)
   print(f"CHECK {p['baseToken']['symbol']} SC {sc} OK {ok}",flush=True)
   if not ok: continue
   seen.add(mint);cnt+=1
   msg=f"TEST ${p['baseToken']['symbol']} MC ${mc:.0f} VOL ${vol:.0f} TX {tx} RISK {sc}\n`{mint}`\nhttps://axiom.trade/pulse/{mint}\n{p['url']}"
   try: await bot.send_message(CHANNEL_ID,msg,parse_mode="Markdown")
   except: pass
  print(f"SCAN DONE {cnt} nieuw verstuurd",flush=True)
  await asyncio.sleep(7)

asyncio.run(loop())
