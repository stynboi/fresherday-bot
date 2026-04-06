from flask import Flask, request, abort
import json
import requests
import os

app = Flask(__name__)

# ============================================================
# ตั้งค่า LINE OA
# ============================================================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
}

# ============================================================
# ฐานข้อมูลเมนูและแคลอรี่
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
# Webhook
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()

    for event in body.get("events", []):
        if event["type"] != "message":
            continue
        if event["message"]["type"] != "text":
            continue

        user_id     = event["source"]["userId"]
        reply_token = event["replyToken"]
        user_text   = event["message"]["text"].strip()

        reply = handle_message(user_text, user_id)
        send_reply(reply_token, reply)

    return "OK", 200


# ============================================================
# Logic
# ============================================================
def handle_message(text, user_id):
    if text in ["ดูเมนูทั้งหมด", "เมนู", "menu", "📋 ดูเมนูทั้งหมด"]:
        lines = [f"• {name} — {info['cal']} kcal" for name, info in MENU_DB.items()]
        return "เมนูของเราครับ 🍽\n\n" + "\n".join(lines) + "\n\nพิมพ์ชื่อเมนูเพื่อดูแคลอรี่"

    if text in ["แนะนำเมนูสุขภาพ", "เมนูสุขภาพ", "low cal", "🥗 เมนูสุขภาพ"]:
        sorted_menus = sorted(MENU_DB.items(), key=lambda x: x[1]["cal"])[:3]
        lines = [f"• {name} — {info['cal']} kcal" for name, info in sorted_menus]
        return "เมนูแคลอรี่ต่ำแนะนำครับ 🥗\n\n" + "\n".join(lines)

    if text in ["เช็คแคลอรี่", "แคลอรี่", "🔥 เช็คแคลอรี่"]:
        return (
            "พิมพ์ชื่อเมนูที่ต้องการเช็คได้เลยครับ 🔥\n\n"
            "เช่น 'กระเพราหมู' หรือ 'ผัดไทย'\n\n"
            "หรือกดปุ่ม 📋 ดูเมนูทั้งหมด ด้านล่าง"
        )

    if text in ["ติดต่อร้าน", "โทร", "เบอร์", "📞 ติดต่อร้าน"]:
        return (
            "📞 ติดต่อร้าน Fresherday\n"
            "─────────────────────\n"
            "โทร: 065-296-5659 (เบน)\n"
            "LINE: @391onvsx\n"
            "─────────────────────\n"
            "สั่งอาหารล่วงหน้า 1 วันนะครับ 🙏"
        )

    if text in ["สวัสดี", "hello", "หวัดดี", "hi"]:
        return (
            "สวัสดีครับ! ยินดีต้อนรับสู่ Fresherday 🍜\n\n"
            "กดปุ่มเมนูด้านล่างได้เลยครับ หรือพิมพ์ชื่อเมนูเพื่อเช็คแคลอรี่"
        )

    matched = find_menu(text)
    if matched:
        name, info = matched
        return format_calorie_reply(name, info)

    return (
        f"ขออภัยครับ ยังไม่มีข้อมูล '{text}' ในระบบ 😅\n\n"
        "กดปุ่ม 📋 ดูเมนูทั้งหมด ด้านล่างได้เลยครับ"
    )


def find_menu(text):
    if text in MENU_DB:
        return text, MENU_DB[text]
    for name, info in MENU_DB.items():
        if text in name or name in text:
            return name, info
    return None


def format_calorie_reply(name, info):
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
# ส่งข้อความกลับ
# ============================================================
def send_reply(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    requests.post(url, headers=HEADERS, json=body)


# ============================================================
# Rich Menu — เปิด /setup-rich-menu ในเบราว์เซอร์ครั้งเดียว
# ============================================================
@app.route("/setup-rich-menu", methods=["GET"])
def setup_rich_menu():
    # 1) สร้าง Rich Menu
    rich_menu = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Fresherday Menu",
        "chatBarText": "🍽 เมนู Fresherday",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "📋 ดูเมนูทั้งหมด"}
            },
            {
                "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "🥗 เมนูสุขภาพ"}
            },
            {
                "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "🔥 เช็คแคลอรี่"}
            },
            {
                "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
                "action": {"type": "message", "text": "📞 ติดต่อร้าน"}
            },
        ]
    }

    resp = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=HEADERS,
        json=rich_menu,
    )

    if resp.status_code != 200:
        return f"สร้าง Rich Menu ไม่สำเร็จ: {resp.text}", 400

    rich_menu_id = resp.json()["richMenuId"]

    # 2) สร้างรูป Rich Menu
    img = create_rich_menu_image()

    img_resp = requests.post(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "image/png",
        },
        data=img,
    )

    if img_resp.status_code != 200:
        return f"อัปโหลดรูปไม่สำเร็จ: {img_resp.text}", 400

    # 3) ตั้งเป็น Default
    default_resp = requests.post(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers=HEADERS,
    )

    if default_resp.status_code != 200:
        return f"ตั้ง Default ไม่สำเร็จ: {default_resp.text}", 400

    return f"✅ Rich Menu สร้างสำเร็จ! ID: {rich_menu_id}", 200


def create_rich_menu_image():
    """สร้างรูป Rich Menu 2500x1686 px แบบสวยงาม"""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 2500, 1686
    half_w, half_h = W // 2, H // 2

    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # 4 ช่อง สีโทน Fresherday (เขียวสด)
    colors = ["#2ECC71", "#27AE60", "#1ABC9C", "#16A085"]
    boxes = [
        (0, 0, half_w - 3, half_h - 3),
        (half_w + 3, 0, W, half_h - 3),
        (0, half_h + 3, half_w - 3, H),
        (half_w + 3, half_h + 3, W, H),
    ]
    for color, box in zip(colors, boxes):
        draw.rounded_rectangle(box, radius=20, fill=color)

    # ข้อความ
    labels = ["MENU", "HEALTHY", "CALORIE", "CONTACT"]
    emojis = ["📋", "🥗", "🔥", "📞"]
    sub_labels = [
        "All Menu", "Low Cal", "Check Cal", "065-296-5659"
    ]

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 120)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = font_big
        font_emoji = font_big

    centers = [
        (half_w // 2, half_h // 2),
        (half_w + half_w // 2, half_h // 2),
        (half_w // 2, half_h + half_h // 2),
        (half_w + half_w // 2, half_h + half_h // 2),
    ]

    for i, (cx, cy) in enumerate(centers):
        draw.text((cx, cy - 80), emojis[i], fill="white", font=font_emoji, anchor="mm")
        draw.text((cx, cy + 40), labels[i], fill="white", font=font_big, anchor="mm")
        draw.text((cx, cy + 120), sub_labels[i], fill="#FFFFFFCC", font=font_small, anchor="mm")

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============================================================
# รัน Server
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
