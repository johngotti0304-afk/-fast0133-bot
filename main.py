import os, requests, asyncio, threading, time, random
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

BOT_TOKEN=os.getenv("BOT_TOKEN")
CHANNEL_ID=os.getenv("CHANNEL_ID")
PORT=int(os.getenv("PORT",10000))

MIN_MC=25000
MAX_MC=90000
MAX_RUG=25

class H(BaseHTTPRequestHandler):
 def do_GET(self): self.send_response(200);self.end_headers();self.wfile.write(b"BEST FINAL LIVE")
 def log_message(self,*a):return
threading.Thread(target=lambda:HTTPServer(("0.0.0.0",PORT),H).serve_forever(),daemon=True).start()

bot=Bot(token=BOT_TOKEN)
seen=set()

def get_pairs():
 # retry + 2 endpoints
 headers={"User-Agent":f"Mozilla/5.0 Chrome/{random.randint(110,125)}.0"}
 for attempt in range(3):
  try:
   r=requests.get("https://api.dexscreener.com/latest/dex/search/?q=pump.fun",timeout=15,headers=headers)
   if r.status_code==429:
    print("Dex 429 rate limit, sleep 5s",flush=True)
    time.sleep(5); continue
   if r.status_code!=200:
    print(f"Dex status {r.status_code}",flush=True); time.sleep(2); continue
   data=r.json().get("pairs",[])
   print(f"Dex OK {len(data)} pairs attempt {attempt+1}",flush=True)
   return data[:90]
  except Exception as e:
   print(f"Dex ERR {e} attempt {attempt+1}",flush=True)
   time.sleep(2+attempt)
 # fallback leeg
 return []

def rug_ok(mint):
 try:
  r=requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report",timeout=10,headers={"User-Agent":"Mozilla/5.0"})
  if r.status_code!=200: return True,0
  j=r.json()
  if j.get("rugged"): return False,100
  sc=j.get("score",0) or 0
  if sc>MAX_RUG: return False,sc
  for rk in j.get("risks",[]) or []:
   if rk.get("level")=="danger":
    n=rk.get("name","").lower()
    if "mint" in n or "top holders" in n or "single holder" in n:
     return False,sc
  return True,sc
 except: return True,0

async def loop():
 print("BEST FINAL BOT LIVE",flush=True)
 try: await bot.send_message(CHANNEL_ID,"BEST FINAL BOT LIVE - 25k-90k | RISK <25 | Axiom Ready @fast0133")
 except: pass
 while True:
  pairs=get_pairs()
  cands=[]
  for p in pairs:
   if p.get("chainId")!="solana": continue
   mc=float(p.get("fdv",0) or p.get("marketCap",0) or 0)
   vol=float(p.get("volume",{}).get("m5",0) or p.get("volume",{}).get("h1",0) or p.get("volume",{}).get("h24",0) or 0)
   if not (MIN_MC<=mc<=MAX_MC): continue
   cands.append((p,mc,vol))
  print(f"Gefilterd {len(cands)} coins MC 25k-90k",flush=True)
  cnt=0
  for p,mc,vol in cands:
   mint=p["baseToken"]["address"]
   if mint in seen: continue
   ok,sc=rug_ok(mint)
   sym=p["baseToken"]["symbol"]
   print(f"CHECK {sym} MC {mc:.0f} SC {sc} OK {ok}",flush=True)
   if not ok: continue
   seen.add(mint);cnt+=1
   msg=(f"ROCKET BEST ${sym}\nMC ${mc:.0f} VOL ${vol:.0f} RISK {sc}/100\n`{mint}`\nhttps://axiom.trade/pulse/{mint}\n{p['url']}")
   try: await bot.send_message(CHANNEL_ID,msg,parse_mode="Markdown")
   except Exception as e: print(f"TG ERR {e}",flush=True)
   await asyncio.sleep(1)
  print(f"SCAN DONE {cnt} nieuw - sleep 10s",flush=True)
  await asyncio.sleep(10)

asyncio.run(loop())
