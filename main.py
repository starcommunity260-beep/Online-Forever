import asyncio
import json
import requests
import websockets
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== ตั้งค่าที่นี่ ==================
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    TOKEN = "ใส่ Token ที่นี่"

STATUS = "online"
CUSTOM_STATUS = "ออนไลน์ 24/7 🔥"
USE_EMOJI = True
EMOJI = "🔥"
# ===============================================

# ===== HTTP Server สำหรับ Render =====
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
print("✅ HTTP Server เปิดที่ port 10000")
# =====================================

headers = {"Authorization": TOKEN}

r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
if r.status_code != 200:
    print("❌ Token ผิดหรือไม่ได้ตั้ง ENV!")
    exit()

user = r.json()
print(f"✅ ล็อกอินสำเร็จ → {user['username']} ({user['id']})")

activity = {
    "name": "Custom Status",
    "type": 4,
    "state": CUSTOM_STATUS,
    "id": "custom"
}

if USE_EMOJI and EMOJI:
    activity["emoji"] = {"name": EMOJI, "id": None, "animated": False}

async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"

    async with websockets.connect(uri) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                try:
                    await ws.send(json.dumps({"op": 1, "d": None}))
                except Exception:
                    break

        asyncio.create_task(heartbeat())

        identify = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"},
                "presence": {
                    "status": STATUS,
                    "afk": False,
                    "activities": [activity]
                }
            }
        }
        await ws.send(json.dumps(identify))
        print("✅ เชื่อมต่อ Discord Gateway สำเร็จ → Online 24/7")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("op") == 11:
                    continue
            except Exception as e:
                print("Connection lost, reconnecting...", e)
                break

async def main():
    while True:
        try:
            await discord_gateway()
        except Exception as e:
            print("เกิดข้อผิดพลาดใหญ่:", e)

        print("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

asyncio.run(main())
