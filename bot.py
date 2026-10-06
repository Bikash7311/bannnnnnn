import asyncio
import json
import os
import time
import threading
from flask import Flask

# --- 1. EVENT LOOP FIX FOR PYTHON 3.10+ / 3.14 ---
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest, WebAppInfo
from hydrogram.errors import UserNotParticipant

# --- 2. CONFIGURATION ---
API_ID = 33772941  
API_HASH = "3b6ab6b1940c87915439bb41e4e80ea8"  
BOT_TOKEN = "8904752333:AAFeTxNjK0VhzBU60qT8asTIZo09too2ahE"

OWNER_ID = 6132146801
OWNER_USERNAME = "Znonsence"
BOT_USERNAME = "Nobita_banbot"

MANDATORY_CHANNEL = "nobitabanxunban"
MANDATORY_GROUP_LINK = "https://t.me/chatgctest"
REQ_CHANNEL_LINK = "https://t.me/+vM_Qw32vxK81NmNl"

# Direct Video Link
HEADER_VIDEO = "https://videotourl.com/videos/1791282196960-032c9029-1397-468f-a61f-d9ce71d18614.mp4"

# CLIENT INITIALIZATION
app = Client("NobitaBanBotSession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. FLASK SERVER & STYLISH WEB APP INTERFACE ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "⚡ NOBITA BAN X UNBAN PREMIUM BOT IS ACTIVE & RUNNING ⚡"

# Web App HTML UI Route for Full Screen Experience
@web_app.route('/webapp')
def webapp_interface():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>✨ NOBITA BAN X UNBAN PREMIUM BOT ✨</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                background-color: #0d1117;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }}
            .video-container {{
                width: 100%;
                max-height: 45vh;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            }}
            video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
            .content {{
                padding: 20px;
                width: 100%;
                max-width: 500px;
                text-align: center;
            }}
            .title {{
                font-size: 18px;
                font-weight: bold;
                color: #58a6ff;
                margin-bottom: 20px;
                text-shadow: 0 0 10px rgba(88, 166, 255, 0.4);
            }}
            .btn {{
                background: linear-gradient(135deg, #1f6beb, #8957e5);
                color: white;
                border: none;
                padding: 14px;
                margin: 8px 0;
                width: 100%;
                border-radius: 10px;
                font-weight: bold;
                font-size: 15px;
                cursor: pointer;
                box-shadow: 0 4px 10px rgba(31, 107, 235, 0.3);
                transition: transform 0.1s ease;
            }}
            .btn:active {{
                transform: scale(0.98);
            }}
        </style>
    </head>
    <body>
        <div class="video-container">
            <video autoplay loop muted playsinline src="{HEADER_VIDEO}"></video>
        </div>
        
        <div class="content">
            <div class="title">✦ ⚡ ＮＯＢＩＴＡ ＢＡＮ Ｘ ＵＮＢＡＮ ＰＲＥＭＩＵＭ ⚡ ✦</div>
            
            <button class="btn" onclick="Telegram.WebApp.sendData('ban_perm')">💀 𝑷𝒆𝒓𝒎𝒂𝒏𝒆𝒏𝒕 𝑩𝒂𝒏</button>
            <button class="btn" onclick="Telegram.WebApp.sendData('ban_temp')">⏳ 𝑻𝒆𝒎𝒑𝒐𝒓𝒂𝒓𝒚 𝑩𝒂𝒏</button>
            <button class="btn" onclick="Telegram.WebApp.sendData('mass_report')">💥 𝑴𝒂𝒔𝒔 𝑹𝒆𝒑𝒐𝒓𝒕𝒊𝒏𝒈</button>
            <button class="btn" onclick="Telegram.WebApp.sendData('unban')">⚡ 𝑼𝒏𝒃𝒂𝒏 𝑻𝒂𝒓𝒈𝒆𝒕</button>
        </div>

        <script>
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        </script>
    </body>
    </html>
    """

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- 4. PERSISTENT STORAGE ---
REQ_FILE = "approved_users.json"
USERS_FILE = "users_db.json"

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return set(data) if isinstance(default, set) else data
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(list(data) if isinstance(data, set) else data, f, indent=2)

approved_req_users = load_json(REQ_FILE, set())
raw_users_db = load_json(USERS_FILE, {})
users_db = {int(k): v for k, v in raw_users_db.items()}

cooldowns = {}
user_states = {}
COOLDOWN_TIME = 600

# --- 5. JOIN REQUEST EVENT HANDLER ---

@app.on_chat_join_request()
async def track_join_requests(client, chat_join_request: ChatJoinRequest):
    user_id = chat_join_request.from_user.id
    approved_req_users.add(user_id)
    save_json(REQ_FILE, approved_req_users)
    print(f"✅ [𝑱𝑶𝑰𝑵 𝑹𝑬𝑼𝑬𝑺𝑻 𝑨𝑑𝑷𝑹𝑶𝑽𝑬𝑫] User ID: {user_id}")

# --- 6. HELPER FUNCTIONS ---

def render_progress_bar(percent: int, length: int = 12) -> str:
    filled = int(length * percent // 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent}%"

async def check_force_join(client, user_id):
    if user_id == OWNER_ID:
        return True
    
    try:
        await client.get_chat_member(MANDATORY_CHANNEL, user_id)
    except UserNotParticipant:
        return False
    except Exception:
        pass

    if user_id in approved_req_users:
        return True

    try:
        chat_member = await client.get_chat_member("chatgctest", user_id)
        if chat_member:
            approved_req_users.add(user_id)
            save_json(REQ_FILE, approved_req_users)
            return True
    except Exception:
        pass

    return False

def get_force_join_menu():
    text = (
        "⛔ <b><u>𝑨𝑪𝑪𝑬𝑺𝑺 𝑫𝑬𝑵𝑰𝑬𝑫 - 𝑴𝑨𝑵𝑫𝑨𝑻𝑶𝑹𝒀 𝑱𝑶𝑰𝑵 𝑑𝑬𝑸𝑼𝑰𝑹𝑬𝑫</u></b> ⛔\n\n"
        "✨ <i>𝑩𝒐𝒕 features unlock karne ke liye sabhi links par Join / Request bhein!</i>\n\n"
        "📢 <b>1️⃣ Main Channel (Must Join)</b>\n"
        "💬 <b>2️⃣ Discussion Group (Send Request)</b>\n"
        "🔒 <b>3️⃣ Private VIP Channel (Send Request)</b>\n\n"
        "🔄 <i>Sabhi complete karke <b>'Check Verification'</b> par click karein!</i>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 𝑱𝒐𝒊𝒏 𝑴𝒂𝒊𝒏 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", url=f"https://t.me/{MANDATORY_CHANNEL}")],
        [InlineKeyboardButton("💬 𝑹𝒆𝒒𝒖𝒆𝒔𝒕 𝑮𝒓𝒐𝒖𝒑 𝑱𝒐𝒊𝒏", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 𝑹𝒆𝒒𝒖𝒆𝒔𝒕 𝑽𝑰𝑑 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", url=REQ_CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 𝑪𝒉𝒆𝒄𝒌 𝑽𝒆𝒓𝒊𝒇𝒊𝒄𝒂𝒕𝒊𝒐𝒏", callback_data="check_join_status")]
    ])
    return text, buttons

def get_main_menu(user_id):
    user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
    
    if user_id == OWNER_ID:
        status_str = "⚡ OWNER ⚡"
    elif user_data.get('is_premium', False):
        status_str = "💎 PREMIUM"
    else:
        status_str = "🪙 FREE"

    ref_str = f"{user_data.get('referrals', 0)}/10"
    u_str = str(user_id)

    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://your-render-app.onrender.com")

    caption = (
        "✦ ─────────────────── ✦\n"
        "⚡ <b>ＮＯＢＩＴＡ ＢＡＮ Ｘ ＵＮＢＡＮ ＰＲＥＭＩＵＭ ＢＯＴ</b> ⚡️\n"
        "✦ ─────────────────── ✦\n\n"
        "💀 • <b>𝑷𝒆𝒓𝒎𝒂𝒏𝒆𝒏𝒕 𝑩𝒂𝒏 𝑴𝒐𝒅𝒖𝒍𝒆</b>\n"
        "⏳ • <b>𝑻𝒆𝒎𝒑𝒐𝒓𝒂𝒓𝒚 𝑩𝒂𝒏 𝑴𝒐𝒅𝒖𝒍𝒆</b>\n"
        "🔍 • <b>𝑩𝒂𝒏 𝑺𝒕𝒂𝒕𝒖𝒔 𝑪𝒉𝒆𝒄𝒌𝒆𝒓</b>\n"
        "💥 • <b>𝑴𝒂𝒔𝒔 𝑹𝒆𝒑𝒐𝒓𝒕𝒊𝒏𝒈 𝑺𝒚𝒔𝒕𝒆𝒎</b>\n\n"
        "<code>┌─────────────────────────┐\n"
        f"│ 𝑭𝒊𝒆𝒍𝒅     │ 𝑽𝒂𝒍𝒖𝒆       │\n"
        "├─────────────────────────┤\n"
        f"│ 👤 User   │ {u_str:<11} │\n"
        f"│ 👑 Status │ {status_str:<11} │\n"
        f"│ 🔮 Refs   │ {ref_str:<11} │\n"
        "└─────────────────────────┘</code>\n\n"
        "🎯 <i>𝑷𝒍𝒆𝒂𝒔𝒆 𝒔𝒆𝒍𝒆𝒄𝒕 𝒂𝒏 𝒂𝒄𝒕𝒊𝒐𝒏 𝒃𝒆𝒍𝒐𝒘:</i>"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 𝑶𝑑𝑬𝑵 𝑭𝑼𝑳𝑳 𝑺𝑪𝑑𝑬𝑬𝑵 𝑨𝑑𝑑", web_app=WebAppInfo(url=f"{render_url}/webapp"))],
        [InlineKeyboardButton("💀 𝑷𝒆𝒓𝒎𝒂𝒏𝒆𝒏𝒕 𝑩𝒂𝒏", callback_data="ban_perm"), InlineKeyboardButton("⏳ 𝑻𝒆𝒎𝒑𝒐𝒓𝒂𝒓𝒚 𝑩𝒂𝒏", callback_data="ban_temp")],
        [InlineKeyboardButton("💥 𝑴𝒂𝒔𝒔 𝑹𝒆𝒑𝒐𝒓𝒕", callback_data="mass_report"), InlineKeyboardButton("⚡ 𝑼𝒏𝒃𝒂𝒏 𝑻𝒂𝒓𝒈𝒆𝒕", callback_data="unban")],
        [InlineKeyboardButton("🔍 𝑺𝒕𝒂𝒕𝒖𝒔 𝑪𝒉𝒆𝒄𝒌𝒆𝒓", callback_data="status"), InlineKeyboardButton("🤖 𝑩𝒐𝒕 𝑺𝒕𝒂𝒕𝒖𝒔", callback_data="bot_status")],
        [InlineKeyboardButton("💎 𝑰𝒏𝒗𝒊𝒕𝒆 𝑭𝒓𝒊𝒆𝒏𝒅𝒔", callback_data="invite"), InlineKeyboardButton("👑 𝑶𝒘𝒏𝒆𝒓", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton("📢 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", url=f"https://t.me/{MANDATORY_CHANNEL}"), InlineKeyboardButton("💬 𝑮𝒓𝒐𝒖𝒑", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 𝑱𝒐𝒊𝒏 𝑷𝒓𝒊𝒗𝒂𝒕𝒆 VIP", url=REQ_CHANNEL_LINK)]
    ])
    return caption, buttons

# --- 7. COMMAND HANDLERS ---

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_cmd(client, message):
    total_users = len(users_db)
    premium_users = sum(1 for u in users_db.values() if u.get('is_premium', False))
    free_users = total_users - premium_users
    
    stats_text = (
        "✦ ─────────────────── ✦\n"
        "📊 <b><u>𝑵𝑶𝑩𝑰𝑻𝑨 𝑿 𝑩𝑶𝑻 𝑺𝑻𝑨𝑻𝑰𝑺𝑻𝑰𝑪𝑺</u></b> 📊\n"
        "✦ ─────────────────── ✦\n\n"
        f"👥 <b>𝑻𝒐𝒕𝒂𝒍 𝑼𝒔𝒆𝒓𝒔:</b> <code>{total_users}</code>\n"
        f"💎 <b>𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑼𝒔𝒆𝒓𝒔:</b> <code>{premium_users}</code>\n"
        f"🪙 <b>𝑭𝒓𝒆𝒆 𝑼𝒔𝒆𝒓𝒔:</b> <code>{free_users}</code>"
    )
    await message.reply_video(video=HEADER_VIDEO, caption=stats_text)

@app.on_message(filters.command("addpremium") & filters.user(OWNER_ID))
async def add_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ <b><u>𝑼𝒔𝒂𝒈𝒆:</u></b> <code>/addpremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id not in users_db:
            users_db[target_id] = {'referrals': 0, 'is_premium': True}
        else:
            users_db[target_id]['is_premium'] = True
        save_json(USERS_FILE, users_db)
        await message.reply_text(f"✨ <b><u>𝑺𝑼𝑪𝑪𝑬𝑺𝑺:</u></b> User <code>{target_id}</code> upgraded to 💎 <b>𝑷𝑹𝑬𝑴𝑰𝑼𝑴</b>!")
    except ValueError:
        await message.reply_text("❌ <b><u>𝑬𝑹𝑹𝑶𝑹:</u></b> <i>Invalid User ID format.</i>")

@app.on_message(filters.command("rempremium") & filters.user(OWNER_ID))
async def rem_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ <b><u>𝑼𝒔𝒂𝒈𝒆:</u></b> <code>/rempremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id in users_db:
            users_db[target_id]['is_premium'] = False
            save_json(USERS_FILE, users_db)
            await message.reply_text(f"🔻 <b><u>𝑼𝑷𝑫𝑨𝑻𝑬𝑫:</u></b> User <code>{target_id}</code> Premium access removed!")
        else:
            await message.reply_text("❌ <b><u>𝑬𝑹𝑹𝑶𝑹:</u></b> <i>User not found in database.</i>")
    except ValueError:
        await message.reply_text("❌ <b><u>𝑬𝑹𝑹𝑶𝑹:</u></b> <i>Invalid User ID format.</i>")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ <b><u>𝑬𝑹𝑹𝑶𝑹:</u></b> <i>Reply to a message to broadcast.</i>")
        return
    
    msg = await message.reply_text("🚀 <b><u>𝑩𝑹𝑶𝑨𝑫𝑪𝑨𝑺𝑻𝑰𝑵𝑮:</u></b> <i>Sending message to all users...</i>")
    success, failed = 0, 0
    
    for uid in list(users_db.keys()):
        try:
            await message.reply_to_message.copy(uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await msg.edit(
        "✨ <b><u>𝑩𝑹𝑶𝑨𝑫𝑪𝑨𝑺𝑻 𝑪𝑶𝑴𝑑𝑳𝑬𝑻𝑬𝑫</u></b> ✨\n\n"
        f"🎯 <b>𝑺𝒖𝒄𝒄𝒆𝒔𝒔:</b> <code>{success}</code>\n"
        f"❌ <b>𝑭𝒂𝒊𝒍𝒆𝒅:</b> <code>{failed}</code>"
    )

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    
    if not await check_force_join(client, user_id):
        text, buttons = get_force_join_menu()
        await message.reply_video(video=HEADER_VIDEO, caption=text, reply_markup=buttons)
        return

    # Referral Tracking
    is_new = user_id not in users_db
    if is_new:
        users_db[user_id] = {'referrals': 0, 'is_premium': False}
        if len(message.command) > 1:
            try:
                ref_by = int(message.command[1])
                if ref_by in users_db and ref_by != user_id:
                    users_db[ref_by]['referrals'] = users_db[ref_by].get('referrals', 0) + 1
                    if users_db[ref_by]['referrals'] >= 10:
                        users_db[ref_by]['is_premium'] = True
                    try:
                        await client.send_message(
                            ref_by, 
                            f"🎉 <b><u>𝑵𝑬𝑹 𝑑𝑬𝑭𝑬𝑹𝑹𝑨𝑳:</u></b>\nTotal Referrals: <code>{users_db[ref_by]['referrals']}/10</code>"
                        )
                    except Exception:
                        pass
            except Exception:
                pass
        save_json(USERS_FILE, users_db)

    msg = await message.reply_text("⚙️ <i>𝑰𝒏𝒊𝒕𝒊𝒂𝒍𝒊𝒛𝒊𝒏𝒈 𝑺𝒚𝒔𝒕𝒆𝒎...</i>")
    await asyncio.sleep(0.3)
    await msg.edit("🔥 <i>𝑳𝒐𝒂𝒅𝒊𝒏𝒈 𝑨𝒏𝒊𝒎𝒂𝒕𝒊𝒐𝒏...</i>")
    await asyncio.sleep(0.3)
    await msg.delete()

    caption, buttons = get_main_menu(user_id)
    try:
        await message.reply_video(video=HEADER_VIDEO, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)

@app.on_message(filters.text & ~filters.command(["start", "stats", "addpremium", "rempremium", "broadcast"]))
async def handle_input(client, message):
    user_id = message.from_user.id
    
    if user_id in user_states:
        action_type = user_states.pop(user_id)
        target = message.text.strip()
        
        msg = await message.reply_text("⏳ <b><u>𝑷𝑹𝑶𝑪𝑬𝑺𝑺𝑰𝑵𝑮 𝑻𝑨𝑺𝑑...</u></b>")
        
        for pct in [20, 40, 60, 80, 100]:
            await asyncio.sleep(0.6)
            bar = render_progress_bar(pct)
            
            table_text = (
                "✦ ─────────────────── ✦\n"
                "⚡ <b>ＮＯＢＩＴＡ ＢＡＮ Ｘ ＵＮＢＡＮ ＰＲＥＭＩＵＭ ＢＯＴ</b> ⚡️\n"
                "✦ ─────────────────── ✦\n\n"
                "<code>┌─────────────────────────┐\n"
                f"│ Target   │ {target[:11]:<11} │\n"
                "├─────────────────────────┤\n"
                f"│ Action   │ {action_type[:11]:<11} │\n"
                "├─────────────────────────┤\n"
                f"│ Status   │ {bar:<11} │\n"
                "└─────────────────────────┘</code>"
            )
            await msg.edit_text(table_text)

        final_output = (
            "✨ <b><u>𝑬𝑹𝑬𝑪𝑼𝑻𝑰𝑶𝑵 𝑪𝑶𝑴𝑑𝑳𝑬𝑻𝑬𝑫</u></b> ✨\n\n"
            "📜 <i>𝑺𝒖𝒎𝒎𝒂𝒓𝒚 𝑳𝒐𝒈:</i>\n\n"
            f"<blockquote>🎯 <b>Target:</b> {target}\n"
            f"⚡ <b>Module:</b> {action_type}\n"
            "✅ <b>Status:</b> Interface routine executed successfully.</blockquote>"
        )
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 𝒕𝒐 𝑴𝒆𝒏𝒖", callback_data="back_to_menu")]])
        await msg.edit_text(final_output, reply_markup=back_btn)

# --- 8. CALLBACK QUERY HANDLER ---

@app.on_callback_query()
async def cb_handler(client, query):
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_join_status":
        if await check_force_join(client, user_id):
            await query.answer("✨ Verification Successful!", show_alert=True)
            caption, buttons = get_main_menu(user_id)
            try:
                await query.message.edit_caption(caption=caption, reply_markup=buttons)
            except Exception:
                await query.message.edit_text(text=caption, reply_markup=buttons)
        else:
            await query.answer("❌ Verification Failed! Pehle sabhi channels join karein.", show_alert=True)
        return

    if data == "back_to_menu":
        user_states.pop(user_id, None)
        caption, buttons = get_main_menu(user_id)
        try:
            await query.message.edit_caption(caption=caption, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=caption, reply_markup=buttons)
        return

    if data == "invite":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        user_data = users_db.get(user_id, {'referrals': 0})
        invite_text = (
            "🚀 <b><u>𝑰𝑵𝑽𝑰𝑻𝑬 & 𝑬𝑨𝑹𝑵 𝑷𝑹𝑬𝑴𝑰𝑼𝑴</u></b>\n\n"
            "💡 <i>10 friends ko invite karein aur 💎 PREMIUM access free unlock karein!</i>\n\n"
            f"📊 <b>𝒀𝒐𝒖𝒓 𝑹𝒆𝒇𝒆𝒓𝒓𝒂𝒍𝒔:</b> <code>{user_data.get('referrals', 0)}/10</code>\n"
            f"🔗 <b>𝒀𝒐𝒖𝒓 𝑰𝒏𝒗𝒊𝒕𝒆 𝑳𝒊𝒏𝒌:</b>\n<code>{ref_link}</code>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 𝑺𝒉𝒂𝒓𝒆 𝑹𝒆𝒇𝒆𝒓𝒓𝒂𝒍 𝑳𝒊𝒏𝒌", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Nobita%20Ban%20Bot")],
            [InlineKeyboardButton("👑 𝑪𝒐𝒏𝒕𝒂𝒄𝒕 𝑶𝒘𝒏𝒆𝒓", url=f"https://t.me/{OWNER_USERNAME}")],
            [InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 𝒕𝒐 𝑴𝒆𝒏𝒖", callback_data="back_to_menu")]
        ])
        try:
            await query.message.edit_caption(caption=invite_text, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=invite_text, reply_markup=buttons)
        return

    if data in ["ban_perm", "ban_temp", "mass_report", "unban"]:
        user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
        
        if user_id != OWNER_ID and not user_data.get('is_premium', False):
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            restricted_text = (
                "⛔ <b><u>𝑨𝑪𝑪𝑬𝑺𝑺 𝑹𝑬𝑺𝑻𝑑𝑰𝑪𝑻𝑬𝑫</u></b> ⛔\n\n"
                "⚠️ <i>Aap abhi 🪙 FREE User hain. Yeh feature use karne ke liye Upgrade karein!</i>\n\n"
                f"📊 <b>𝒀𝒐𝒖𝒓 𝑹𝒆𝒇𝒆𝒓𝒓𝒂𝒍𝒔:</b> <code>{user_data.get('referrals', 0)}/10</code>\n\n"
                "💎 <b><u>𝑯𝑶𝑑 𝑻𝑶 𝑼𝑵𝑳𝑶𝑪𝑀 𝑷𝑹𝑬𝑴𝑰𝑼𝑴?</u></b>\n"
                f"1️⃣ <b>Referrals:</b> 10 friends ko link se join karwaye:\n<code>{ref_link}</code>\n\n"
                f"2️⃣ <b>Direct Buy:</b> Owner se buy karein."
            )
            restricted_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 𝑺𝒉𝒂𝒓𝒆 𝑹𝒆𝒇𝒆𝒓𝒓𝒂𝒍 𝑳𝒊𝒏𝒌", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Nobita%20Ban%20Bot")],
                [InlineKeyboardButton("👑 𝑩𝒖𝒚 𝑷𝒓𝒆𝒎𝒊𝒖𝒎", url=f"https://t.me/{OWNER_USERNAME}")],
                [InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 𝒕𝒐 𝑴𝒆𝒏𝒖", callback_data="back_to_menu")]
            ])
            try:
                await query.message.edit_caption(caption=restricted_text, reply_markup=restricted_buttons)
            except Exception:
                await query.message.edit_text(text=restricted_text, reply_markup=restricted_buttons)
            return

        current_time = time.time()
        last_time = cooldowns.get(user_id, 0)
        if current_time - last_time < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - (current_time - last_time))
            mins, secs = divmod(remaining, 60)
            await query.answer(f"⏳ Cooldown Active! Wait {mins}m {secs}s.", show_alert=True)
            return

        cooldowns[user_id] = current_time
        user_states[user_id] = data
        
        ask_text = (
            "🎯 <b><u>𝑬𝑵𝑻𝑬𝑹 𝑻𝑨𝑹𝑮𝑬𝑻 𝑰𝑵𝑭𝑶𝑹𝑴𝑨𝑻𝑰𝑶𝑵</u></b>\n\n"
            "✍️ <i>Please send target details in standard format:</i>"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝑪𝒂𝒏𝒄𝒆𝒍", callback_data="back_to_menu")]])
        try:
            await query.message.edit_caption(caption=ask_text, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=ask_text, reply_markup=buttons)

# --- 9. BOT EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting Web Server for Render Port Binding...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("🚀 Nobita X Ban Bot Starting...")
    app.run()
