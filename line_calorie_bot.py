from flask import Flask, request, abort
import json
import requests

app = Flask(__name__)

# ============================================================
# ตั้งค่า LINE OA (ใส่ค่าจริงจาก LINE Developers Console)
# ============================================================
import os
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

# ============================================================
# ฐานข้อมูลเมนูและแคลอรี่ (ตัวอย่าง — เปลี่ยนเป็นข้อมูลจริงได้เลย)
# หน่วย: kcal ต่อ 1 จาน
# ============================================================
MENU_DB = {
    "กระเพราหมู":   {"cal": 420, "protein": 22, "fat": 18, "carb": 38},
    "กระเพราไก่":   {"cal": 380, "protein": 25, "fat": 14, "carb": 36},
    "กระเพราทะเล":  {"cal": 310, "protein": 28, "fat": 10, "carb": 30},
    "ผัดไทย":       {"cal": 490, "protein": 18, "fat": 16, "carb": 65},
    "ข้าวมันไก่":   {"cal": 520, "protein": 30, "fat": 18, "carb": 58},
    "ต้มยำกุ้ง":    {"cal": 180, "protein": 20, "fat":  8, "carb": 10},
    "ต้มข่าไก่":    {"cal": 220, "protein": 18, "fat": 12, "carb":  8},
    "ส้มตำ":        {"cal": 150, "protein":  5, "fat":  4, "carb": 22},
    "แกงเขียวหวาน": {"cal": 350, "protein": 20, "fat": 22, "carb": 18},
    "ข้าวผัดหมู":   {"cal": 450, "protein": 20, "fat": 15, "carb": 60},
}

# ============================================================
# Webhook — LINE ส่งข้อความมาที่นี่
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()

    for event in body.get("events", []):
        if event["type"] != "message":
            continue
        if event["message"]["type"] != "text":
            continue

        user_id    = event["source"]["userId"]
        reply_token = event["replyToken"]
        user_text  = event["message"]["text"].strip()

        reply_text = handle_message(user_text, user_id)
        send_reply(reply_token, reply_text)

    return "OK", 200


# ============================================================
# Logic — ตัดสินใจว่าจะตอบอะไร
# ============================================================
def handle_message(text, user_id):
    # คำสั่งพิเศษ
    if text in ["ดูเมนูทั้งหมด", "เมนู", "menu"]:
        lines = [f"• {name} — {info['cal']} kcal" for name, info in MENU_DB.items()]
        return "เมนูของเราครับ 🍽\n\n" + "\n".join(lines) + "\n\nพิมพ์ชื่อเมนูเพื่อดูแคลอรี่"

    if text in ["แนะนำเมนูสุขภาพ", "เมนูสุขภาพ", "low cal"]:
        sorted_menus = sorted(MENU_DB.items(), key=lambda x: x[1]["cal"])[:3]
        lines = [f"• {name} — {info['cal']} kcal" for name, info in sorted_menus]
        return "เมนูแคลอรี่ต่ำแนะนำครับ 🥗\n\n" + "\n".join(lines)

    if text in ["สวัสดี", "hello", "หวัดดี", "hi"]:
        return (
            "สวัสดีครับ! ยินดีต้อนรับ 🍜\n\n"
            "พิมพ์ชื่อเมนูที่ต้องการเช็คแคลอรี่ได้เลยครับ\n"
            "เช่น 'กระเพราหมู' หรือ 'ผัดไทย'\n\n"
            "หรือพิมพ์ 'ดูเมนูทั้งหมด' เพื่อดูรายการ"
        )

    # ค้นหาเมนูจาก MENU_DB
    matched = find_menu(text)
    if matched:
        name, info = matched
        return format_calorie_reply(name, info)

    # ไม่พบเมนู
    return (
        f"ขออภัยครับ ยังไม่มีข้อมูล '{text}' ในระบบ 😅\n\n"
        "ลองพิมพ์ 'ดูเมนูทั้งหมด' เพื่อดูว่ามีอะไรบ้างครับ"
    )


def find_menu(text):
    """ค้นหาเมนูแบบ fuzzy — พิมพ์ไม่ครบก็หาเจอ"""
    # ตรงเป๊ะก่อน
    if text in MENU_DB:
        return text, MENU_DB[text]
    # ค้นหาแบบ contains
    for name, info in MENU_DB.items():
        if text in name or name in text:
            return name, info
    return None


def format_calorie_reply(name, info):
    """จัดรูปแบบข้อความตอบกลับแคลอรี่"""
    return (
        f"🍽 {name}\n"
        f"{'─' * 20}\n"
        f"แคลอรี่:  {info['cal']} kcal\n"
        f"โปรตีน:   {info['protein']} g\n"
        f"ไขมัน:    {info['fat']} g\n"
        f"คาร์โบไฮเดรต: {info['carb']} g\n"
        f"{'─' * 20}\n"
        f"ข้อมูลอ้างอิงจากกรมอนามัย"
    )


# ============================================================
# ส่งข้อความกลับหา LINE
# ============================================================
def send_reply(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    requests.post(url, headers=headers, json=body)


# ============================================================
# รัน Server
# ============================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
