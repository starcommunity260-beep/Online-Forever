import asyncio
import json
import requests
import websockets
import os

# ================== ตั้งค่าที่นี่ ==================
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    TOKEN = "ใส่ Token ที่นี่"   # กรณีไม่มี ENV

STATUS = "online"
CUSTOM_STATUS = "ออนไลน์ 24/7 🔥"
USE_EMOJI = True
EMOJI = "🔥"
# ===============================================

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
                await ws.send(json.dumps({"op": 1, "d": None}))

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

        print("✅ Connected to Discord Gateway")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("op") == 11:
                    continue
            except Exception as e:
                print("Connection lost, reconnecting...", e)
                break

# ============== วนลูปหลัก ==============
while True:
    try:
        asyncio.run(discord_gateway())
    except Exception as e:
        print("เกิดข้อผิดพลาดใหญ่:", e)
    print("Reconnecting in 5 seconds...")
    asyncio.sleep(5)   # ← ใช้แบบนี้ (ไม่ใส่ await)
