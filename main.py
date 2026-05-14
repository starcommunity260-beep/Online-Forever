import asyncio
import json
import requests
import websockets
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.environ.get("TOKEN", "PUT_YOUR_TOKEN_HERE")
STATUS = "online"
GAME_NAME = "Minecraft"  # เปลี่ยนชื่อเกมได้เลย

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

threading.Thread(
    target=lambda: HTTPServer(("0.0.0.0", 10000), Handler).serve_forever(),
    daemon=True
).start()
print("[OK] HTTP Server started on port 10000", flush=True)

headers = {"Authorization": TOKEN}
r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
if r.status_code != 200:
    print(f"[ERROR] Invalid token! Status: {r.status_code}", flush=True)
    exit()

user = r.json()
print(f"[OK] Logged in as {user['username']} ({user['id']})", flush=True)

activity = {
    "name": GAME_NAME,
    "type": 0  # 0 = Playing
}

async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"
    async with websockets.connect(uri, max_size=10_000_000) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]
        print(f"[INFO] Heartbeat interval: {heartbeat_interval}ms", flush=True)

        async def heartbeat():
            count = 0
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                try:
                    await ws.send(json.dumps({"op": 1, "d": None}))
                    count += 1
                    print(f"[HEARTBEAT] Sent #{count} - Bot is alive!", flush=True)
                except:
                    print("[HEARTBEAT] Failed", flush=True)
                    break

        asyncio.create_task(heartbeat())
        await ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"},
                "presence": {"status": STATUS, "afk": False, "activities": [activity]}
            }
        }))
        print(f"[OK] Connected! Playing {GAME_NAME}", flush=True)

        msg_count = 0
        while True:
            try:
                data = json.loads(await ws.recv())
                op = data.get("op")
                if op == 11:
                    continue
                msg_count += 1
                print(f"[EVENT] #{msg_count} op={op} t={data.get('t')}", flush=True)
            except Exception as e:
                print(f"[WARN] Connection lost: {e}", flush=True)
                break

async def main():
    run = 0
    while True:
        run += 1
        print(f"[INFO] Starting connection attempt #{run}", flush=True)
        try:
            await discord_gateway()
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)
        print("[INFO] Reconnecting in 5s...", flush=True)
        await asyncio.sleep(5)

asyncio.run(main())
