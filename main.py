import asyncio
import json
import requests
import websockets
import os   # ← เพิ่มบรรทัดนี้

# ================== ใช้ ENV แทน (สำคัญ) ==================
TOKEN = os.environ.get("TOKEN")   # Render จะอ่านจาก Environment Variable
if not TOKEN:
    TOKEN = "ใส่ Token ของคุณที่นี่"   # ถ้าไม่มี ENV ค่อยใช้ตัวนี้ (สำรอง)

STATUS = "online"                    # online / idle / dnd
CUSTOM_STATUS = "ออนไลน์ 24/7 🔥"     # ใส่ข้อความไทย-อังกฤษได้
USE_EMOJI = True
EMOJI = "🔥"
# =======================================================

headers = {"Authorization": TOKEN}

# เช็ค Token
r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
if r.status_code != 200:
    print("Token ผิด หรือไม่ได้ใส่ ENV!")
    print("กรุณาใส่ Environment Variable ชื่อ TOKEN")
    exit()

user = r.json()
print(f"✅ เข้าสู่ระบบแล้ว → {user['username']} ({user['id']})")

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
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": STATUS,
                    "afk": False,
                    "activities": [activity]
                }
            }
        }
        await ws.send(json.dumps(identify))

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("op") == 11:
                    continue
            except Exception as e:
                print("Connection lost, reconnecting...", e)
                break

while True:
    asyncio.run(discord_gateway())
    await asyncio.sleep(5)   # แก้จาก asyncio.sleep เป็น await
