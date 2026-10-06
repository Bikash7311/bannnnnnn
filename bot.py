import asyncio
import json
import os
import time
import threading
from flask import Flask

# --- 1. EVENT LOOP FIX ---
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters
from hydrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ChatJoinRequest
)
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

HEADER_VIDEO = "https://videotourl.com/videos/1791282196960-032c9029-1397-468f-a61f-d9ce71d18614.mp4"

app = Client("NobitaBanBotSession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. DUMMY FLASK SERVER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Nobita Ban Bot is Active!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- 4. DATA STORAGE ---
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

# --- 5. JOIN REQUEST HANDLER ---
@app.on_chat_join_request()
async def track_join_requests(client, chat_join_request: ChatJoinRequest):
    user_id = chat_join_request.from_user.id
    approved_req_users.add(user_id)
    save_json(REQ_FILE, approved_req_users)

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
        "<b><u>ACCESS DENIED - MANDATORY JOIN REQUIRED</u></b>\n\n"
        "<blockquote>✨ <i>Bot features use karne ke liye Main Channel Join karein aur Baaki Links par Request Send karein!</i></blockquote>\n\n"
        "1️⃣ <b>📢 Main Channel (Join Mandatory)</b>\n"
        "2️⃣ <b>💬 Discussion Group (Send Request)</b>\n"
        "3️⃣ <b>🔒 Private Channel (Send Request)</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Main Channel", url=f"https://t.me/{MANDATORY_CHANNEL}")],
        [InlineKeyboardButton("💬 Request Group Join", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 Request Private Channel", url=REQ_CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 Try Again", callback_data="check_join_status")]
    ])
    return text, buttons

# Video Title & Blockquote Style Caption
def get_main_menu(user_id):
    user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
    
    if user_id == OWNER_ID:
        status_str = "👑 OWNER"
    elif user_data.get('is_premium', False):
        status_str = "👑 PREMIUM"
    else:
        status_str = "🪙 FREE"

    ref_str = f"{user_data.get('referrals', 0)}/10"
    u_str = str(user_id)

    caption = (
        "🥊 <b>NOBITA BAN x UNBAN PREMIUM BOT</b> 🥊\n\n"
        "<blockquote>"
        "😮 <b>Good morning!</b>\n\n"
        "• 💀 <b>Permanent Ban</b>\n"
        "• ⏳ <b>Temporary Ban</b>\n"
        "• 📊 <b>Ban Status Checker</b>\n"
        "• 🔥 <b>Mass Reporting System</b>\n\n"
        "                👥 <b>User</b>\n\n"
        "<code>┌─────────────────────────┐\n"
        f"│ Field     │ Value       │\n"
        "├─────────────────────────┤\n"
        f"│ 👤 User   │ {u_str:<11} │\n"
        f"│ 👑 Status │ {status_str:<11} │\n"
        f"│ 🚀 Refs   │ {ref_str:<11} │\n"
        "└─────────────────────────┘</code>\n\n"
        "📸 <b>Choose an action below:</b>"
        "</blockquote>"
    )
    return caption

# Bottom Reply Keyboard (Screenshot Match)
def get_bottom_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Permanent Ban"), KeyboardButton("⏳ Temporary Ban")],
            [KeyboardButton("Mass Report"), KeyboardButton("✅ Unban Target")],
            [KeyboardButton("📊 Ban Status Checker"), KeyboardButton("🗄️ Bot Status")],
            [KeyboardButton("🚀 Invite a Friend"), KeyboardButton("🏆 Thanks To")],
            [KeyboardButton("👤 Language")]
        ],
        resize_keyboard=True
    )

# --- 7. COMMAND HANDLERS ---
@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_cmd(client, message):
    total_users = len(users_db)
    premium_users = sum(1 for u in users_db.values() if u.get('is_premium', False))
    free_users = total_users - premium_users
    
    stats_text = (
        "📊 <b><u>BOT STATS</u></b>\n\n"
        f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
        f"👑 <b>Premium Users:</b> <code>{premium_users}</code>\n"
        f"🪙 <b>Free Users:</b> <code>{free_users}</code>"
    )
    await message.reply_video(video=HEADER_VIDEO, caption=stats_text)

@app.on_message(filters.command("addpremium") & filters.user(OWNER_ID))
async def add_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ <b>Usage:</b> <code>/addpremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id not in users_db:
            users_db[target_id] = {'referrals': 0, 'is_premium': True}
        else:
            users_db[target_id]['is_premium'] = True
        save_json(USERS_FILE, users_db)
        await message.reply_text(f"✅ User <code>{target_id}</code> upgraded to 👑 <b>PREMIUM</b>!")
    except ValueError:
        await message.reply_text("❌ Invalid User ID.")

@app.on_message(filters.command("rempremium") & filters.user(OWNER_ID))
async def rem_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ <b>Usage:</b> <code>/rempremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id in users_db:
            users_db[target_id]['is_premium'] = False
            save_json(USERS_FILE, users_db)
            await message.reply_text(f"🔻 User <code>{target_id}</code> Premium status removed!")
        else:
            await message.reply_text("❌ User not found in database.")
    except ValueError:
        await message.reply_text("❌ Invalid User ID.")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ <b>Reply to a message to broadcast.</b>")
        return
    
    msg = await message.reply_text("🚀 <b>Starting Broadcast...</b>")
    success, failed = 0, 0
    
    for uid in list(users_db.keys()):
        try:
            await message.reply_to_message.copy(uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await msg.edit(
        "✅ <b><u>BROADCAST COMPLETED</u></b>\n\n"
        f"🎯 <b>Success:</b> <code>{success}</code>\n"
        f"❌ <b>Failed:</b> <code>{failed}</code>"
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
    if user_id not in users_db:
        users_db[user_id] = {'referrals': 0, 'is_premium': False}
        if len(message.command) > 1:
            try:
                ref_by = int(message.command[1])
                if ref_by in users_db and ref_by != user_id:
                    users_db[ref_by]['referrals'] = users_db[ref_by].get('referrals', 0) + 1
                    if users_db[ref_by]['referrals'] >= 10:
                        users_db[ref_by]['is_premium'] = True
            except Exception:
                pass
        save_json(USERS_FILE, users_db)

    caption = get_main_menu(user_id)
    reply_kb = get_bottom_keyboard()
    
    await message.reply_video(video=HEADER_VIDEO, caption=caption, reply_markup=reply_kb)

# Bottom Reply Keyboard Handler
@app.on_message(filters.text & ~filters.command(["start", "stats", "addpremium", "rempremium", "broadcast"]))
async def handle_bottom_buttons(client, message):
    user_id = message.from_user.id
    text = message.text

    if text in ["Permanent Ban", "⏳ Temporary Ban", "Mass Report", "✅ Unban Target"]:
        user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
        
        if user_id != OWNER_ID and not user_data.get('is_premium', False):
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            restricted_text = (
                "<blockquote>"
                "🚫 <b><u>ACCESS RESTRICTED</u></b> 🚫\n\n"
                "⚠️ <i>Upgrade to 👑 PREMIUM to use this feature!</i>\n\n"
                f"📊 <b>Your Referrals:</b> <code>{user_data.get('referrals', 0)}/10</code>\n\n"
                f"🔗 <b>Invite Link:</b>\n<code>{ref_link}</code>"
                "</blockquote>"
            )
            await message.reply_text(restricted_text)
            return

        user_states[user_id] = text
        await message.reply_text(
            "<blockquote>🎯 <b><u>ENTER TARGET INFORMATION</u></b>\n\n✍️ <i>Please send target username or ID:</i></blockquote>"
        )
        return

    if text == "🚀 Invite a Friend":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        user_data = users_db.get(user_id, {'referrals': 0})
        invite_text = (
            "<blockquote>"
            "🚀 <b><u>INVITE & EARN PREMIUM</u></b>\n\n"
            f"📊 <b>Your Referrals:</b> <code>{user_data.get('referrals', 0)}/10</code>\n"
            f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>"
            "</blockquote>"
        )
        await message.reply_text(invite_text)
        return

    if text == "🏆 Thanks To":
        thanks_text = (
            "<blockquote>"
            "🏆 <b><u>SPECIAL THANKS TO</u></b>\n\n"
            f"👑 <b>Owner:</b> @{OWNER_USERNAME}\n"
            f"📢 <b>Channel:</b> @{MANDATORY_CHANNEL}"
            "</blockquote>"
        )
        await message.reply_text(thanks_text)
        return

    # User Input Processing
    if user_id in user_states:
        action_type = user_states.pop(user_id)
        target = text.strip()
        
        msg = await message.reply_text("⏳ <b>Processing Task...</b>")
        for pct in [20, 50, 100]:
            await asyncio.sleep(0.5)
            bar = render_progress_bar(pct)
            await msg.edit_text(f"<blockquote>⚡ <b>Status:</b> {bar}</blockquote>")

        await msg.edit_text(
            f"<blockquote>🎯 <b>Target:</b> {target}\n⚡ <b>Action:</b> {action_type}\n✅ <b>Status:</b> Task Completed Successfully!</blockquote>"
        )

# --- 8. EXECUTION ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    app.run()
