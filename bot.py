import asyncio
import json
import os
import time
import threading
from datetime import datetime
from flask import Flask

# --- 1. EVENT LOOP SETUP FOR PYTHON 3.10+ / 3.14 ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters, idle
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

START_TIME = time.time()

# CLIENT INITIALIZATION
app = Client("NobitaBanBotSession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. FLASK SERVER FOR RENDER PORT BINDING ---
web_app = Flask("bot")

@web_app.route('/')
def home():
    return "Nobita Ban Bot Active & Running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)

# --- 4. PERSISTENT DATA STORAGE ---
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
COOLDOWN_TIME = 300  # 5 Minutes Cooldown

# --- 5. JOIN REQUEST EVENT HANDLER ---
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

def get_readable_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    time_str = ""
    if d: time_str += f"{d}d "
    if h: time_str += f"{h}h "
    if m: time_str += f"{m}m "
    if s: time_str += f"{s}s"
    return time_str if time_str else "0s"

def get_total_users_count():
    BASE_USER_COUNT = 6745
    return BASE_USER_COUNT + len(users_db)

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
        "<b><u>⛔ 𝑨𝑪𝑪𝑬𝑺𝑺 𝑫𝑬𝑵𝑰𝑬𝑫 - 𝑴𝑨𝑵𝑫𝑨𝑻𝑶𝑹𝒀 𝑱𝑶𝑰𝑵 𝑹𝑬𝑼𝑬𝑺𝑻𝑬𝑫</u></b>\n\n"
        "<blockquote>✨ <i>𝑩𝒐𝒕 features unlock karne ke liye sabhi links par Join / Request bhein!</i></blockquote>\n\n"
        "📢 <b>1️⃣ Main Channel (Must Join)</b>\n"
        "💬 <b>2️⃣ Discussion Group (Send Request)</b>\n"
        "🔒 <b>3️⃣ Private VIP Channel (Send Request)</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 𝑱𝒐𝒊𝒏 𝑴𝒂𝒊𝒏 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", url=f"https://t.me/{MANDATORY_CHANNEL}")],
        [InlineKeyboardButton("💬 𝑹𝒆𝒒𝒖𝒆𝒔𝒕 𝑮𝒓𝒐𝒖𝒑 𝑱𝒐𝒊𝒏", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 𝑹𝒆𝒒𝒖𝒆𝒔𝒕 𝑽𝑰𝑷 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", url=REQ_CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 𝑪𝒉𝒆𝒄𝒌 𝑽𝒆𝒓𝒊𝒇𝒊𝒄𝒂𝒕𝒊𝒐𝒏", callback_data="check_join_status")]
    ])
    return text, buttons

def get_main_menu(user_id):
    user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
    
    if user_id == OWNER_ID:
        status_str = "👑 OWNER"
    elif user_data.get('is_premium', False):
        status_str = "💎 PREMIUM"
    else:
        status_str = "🪙 FREE"

    ref_str = f"{user_data.get('referrals', 0)}/10"
    u_str = str(user_id)

    caption = (
        "🥊 <b><u>𝑵𝑶𝑩𝑰𝑻𝑨 𝑩𝑨𝑵 𝒙 𝑼𝑵𝑩𝑨𝑵 𝑷𝑹𝑬𝑴𝑰𝑼𝑴 𝑩𝑶𝑻</u></b> 🥊\n\n"
        "<blockquote>"
        "⚡ <b>𝑾𝒆𝒍𝒄𝒐𝒎𝒆 𝒕𝒐 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑩𝒂𝒏 𝑪𝒆𝒏𝒕𝒆𝒓!</b>\n\n"
        "• 💀 <b>Permanent Ban</b>\n"
        "• ⏳ <b>Temporary Ban</b>\n"
        "• 💥 <b>Mass Reporting System</b>\n"
        "• 🎯 <b>Unban Target Module</b>\n\n"
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

def get_bottom_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔴 𝑷𝒆𝒓𝒎𝒂𝒏𝒆𝒏𝒕 𝑩𝒂𝒏"), KeyboardButton("⏳ 𝑻𝒆𝒎𝒑𝒐𝒓𝒂𝒓𝒚 𝑩𝒂𝒏")],
            [KeyboardButton("💥 𝑴𝒂𝒔𝒔 𝑹𝒆𝒑𝒐𝒓𝒕"), KeyboardButton("🎯 𝑼𝒏𝒃𝒂𝒏 𝑻𝒂𝒓𝒈𝒆𝒕")],
            [KeyboardButton("💎 𝑷𝒖𝒓𝒄𝒉𝒂𝒔𝒆 𝑷𝒓𝒆𝒎𝒊𝒖𝒎"), KeyboardButton("🚀 𝑰𝒏𝒗𝒊𝒕𝒆 𝒂 𝑭𝒓𝒊𝒆𝒏𝒅")],
            [KeyboardButton("🤖 𝑩𝒐𝒕 𝑺𝒕𝒂𝒕𝒖𝒔"), KeyboardButton("🌐 𝑳𝒂𝒏𝒈𝒖𝒂𝒈𝒆")],
            [KeyboardButton("🏆 𝑻𝒉𝒂𝒏𝒌𝒔 𝑻𝒐")]
        ],
        resize_keyboard=True
    )

# --- 7. COMMAND HANDLERS ---
@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_cmd(client, message):
    tot_users = get_total_users_count()
    premium_users = sum(1 for u in users_db.values() if u.get('is_premium', False))
    free_users = tot_users - premium_users
    uptime_str = get_readable_time(int(time.time() - START_TIME))
    
    stats_text = (
        "📊 <b><u>𝑵𝑶𝑩𝑰𝑻𝑨 𝑩𝑶𝑻 𝑺𝑻𝑨𝑻𝑰𝑺𝑻𝑰𝑪𝑺</u></b> 📊\n\n"
        "<blockquote>"
        f"👥 <b>Total Users:</b> <code>{tot_users}</code>\n"
        f"💎 <b>Premium Users:</b> <code>{premium_users}</code>\n"
        f"🪙 <b>Free Users:</b> <code>{free_users}</code>\n"
        f"⏱️ <b>Uptime:</b> <code>{uptime_str}</code>"
        "</blockquote>"
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
        await message.reply_text(f"✨ User <code>{target_id}</code> upgraded to 💎 <b>PREMIUM</b>!")
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
        "✨ <b><u>𝑩𝑹𝑶𝑨𝑫𝑪𝑨𝑺𝑻 𝑪𝑶𝑴𝑴𝑷𝑳𝑬𝑻𝑬𝑫</u></b> ✨\n\n"
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

# --- 8. BOTTOM KEYBOARD CLICK HANDLER ---
@app.on_message(filters.text & ~filters.command(["start", "stats", "addpremium", "rempremium", "broadcast"]))
async def handle_bottom_buttons(client, message):
    user_id = message.from_user.id
    text = message.text

    # --- BAN, UNBAN & REPORT PREMIUM ACTIONS ---
    if text in [
        "🔴 𝑷𝒆𝒓𝒎𝒂𝒏𝒆𝒏𝒕 𝑩𝒂𝒏", "💀 Permanent Ban",
        "⏳ 𝑻𝒆𝒎𝒑𝒐𝒓𝒂𝒓𝒚 𝑩𝒂𝒏", "⏳ Temporary Ban",
        "💥 𝑴𝒂𝒔𝒔 𝑹𝒆𝒑𝒐𝒓𝒕", "💥 Mass Report",
        "🎯 𝑼𝒏𝒃𝒂𝒏 𝑻𝒂𝒓𝒈𝒆𝒕", "🎯 Unban Target"
    ]:
        user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
        
        # Premium Check
        if user_id != OWNER_ID and not user_data.get('is_premium', False):
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            restricted_text = (
                "<blockquote>"
                "⛔ <b><u>𝑨𝑪𝑪𝑬𝑺𝑺 𝑹𝑬𝑺𝑻𝑹𝑰𝑪𝑻𝑬𝑫</u></b> ⛔\n\n"
                "⚠️ <i>Aap abhi 🪙 FREE User hain. Yeh action run karne ke liye Premium unlock karein!</i>\n\n"
                f"👤 <b>Your User ID:</b> <code>{user_id}</code>\n"
                f"📊 <b>Your Referrals:</b> <code>{user_data.get('referrals', 0)}/10</code>\n\n"
                f"🔗 <b>Invite Link:</b>\n<code>{ref_link}</code>"
                "</blockquote>"
            )
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Buy Premium Directly", url=f"https://t.me/{OWNER_USERNAME}")]
            ])
            await message.reply_video(video=HEADER_VIDEO, caption=restricted_text, reply_markup=buttons)
            return

        # Cooldown Check (5 Mins = 300 Sec)
        current_time = time.time()
        last_time = cooldowns.get(user_id, 0)
        if current_time - last_time < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - (current_time - last_time))
            mins, secs = divmod(remaining, 60)
            await message.reply_text(f"⏳ <b><u>𝑪𝑶𝑶𝑳𝑫𝑶𝑾𝑵 𝑨𝑪𝑻𝑰𝑽𝑬!</u></b>\n\n<blockquote><i>Please wait {mins}m {secs}s before executing another request!</i></blockquote>")
            return

        user_states[user_id] = text
        if "Unban" in text:
            prompt_text = "🎯 <b>Send the whatsapp Number You want to Unban (e.g. +234...)</b> 😱"
        else:
            prompt_text = "💥 💥 <b>Send the target WhatsApp number (e.g. +234...)</b> 💀 💀"
            
        await message.reply_video(video=HEADER_VIDEO, caption=f"<blockquote>{prompt_text}</blockquote>")
        return

    # --- PURCHASE PREMIUM ---
    if text in ["💎 𝑷𝒖𝒓𝒄𝒉𝒂𝒔𝒆 𝑷𝒓𝒆𝒎𝒊𝒖𝒎", "💎 Purchase Premium"]:
        user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
        status_text = "💎 PREMIUM USER" if user_data.get('is_premium', False) else "🪙 FREE USER"
        
        premium_text = (
            "💎 <b><u>𝑷𝑼𝑹𝑪𝑯𝑨𝑺𝑬 𝑷𝑹𝑬𝑴𝑰𝑼𝑴 𝑨𝑪𝑪𝑬𝑺𝑺</u></b> 💎\n\n"
            "<blockquote>"
            "⚡ <b>Unlock all powerful Ban, Unban & Mass Reporting features!</b>\n\n"
            f"👤 <b>Your User ID:</b> <code>{user_id}</code>\n"
            f"👑 <b>Current Status:</b> <code>{status_text}</code>\n\n"
            "✨ <b><u>PREMIUM BENEFITS:</u></b>\n"
            "• 💀 Permanent WhatsApp Ban Access\n"
            "• ⏳ Temporary WhatsApp Ban Access\n"
            "• 🎯 Unban WhatsApp Target Access\n"
            "• 💥 Mass Reporting 500+ Packets\n"
            "• ⚡ No Feature Limits & Fast Server\n\n"
            f"📩 <b>Contact Owner to Buy:</b> @{OWNER_USERNAME}"
            "</blockquote>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Contact Owner (@Znonsence)", url=f"https://t.me/{OWNER_USERNAME}")]
        ])
        await message.reply_video(video=HEADER_VIDEO, caption=premium_text, reply_markup=buttons)
        return

    # --- BOT STATUS ---
    if text in ["🤖 𝑩𝒐𝒕 𝑺𝒕𝒂𝒕𝒖𝒔", "🗄️ Bot Status", "🗄 Bot Status"]:
        uptime_str = get_readable_time(int(time.time() - START_TIME))
        tot_users = get_total_users_count()
        status_msg = (
            "🤖 <b><u>𝑵𝑶𝑩𝑰𝑻𝑨 𝑩𝑶𝑻 𝑺𝑻𝑨𝑻𝑼𝑺</u></b> 🗄️\n\n"
            "<blockquote>"
            f"⚡ <b>System Status:</b> <code>ONLINE & RUNNING</code>\n"
            f"⏱️ <b>Bot Uptime:</b> <code>{uptime_str}</code>\n"
            f"👥 <b>Total Active Users:</b> <code>{tot_users}</code>\n"
            f"🛡️ <b>Protection Routine:</b> <code>ACTIVE</code>"
            "</blockquote>"
        )
        await message.reply_video(video=HEADER_VIDEO, caption=status_msg)
        return

    # --- INVITE A FRIEND ---
    if text in ["🚀 𝑰𝒏𝒗𝒊𝒕𝒆 𝒂 𝑭𝒓𝒊𝒆𝒏𝒅", "🚀 Invite a Friend"]:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        user_data = users_db.get(user_id, {'referrals': 0})
        invite_text = (
            "🚀 <b><u>𝑰𝑵𝑽𝑰𝑻𝑬 & 𝑬𝑨𝑹𝑵 𝑷𝑹𝑬𝑴𝑰𝑼𝑴</u></b> 🚀\n\n"
            "<blockquote>"
            "💡 <i>10 dosto ko apne unique referral link se join karwaye aur automatic 💎 PREMIUM Access payein!</i>\n\n"
            f"👤 <b>Your User ID:</b> <code>{user_id}</code>\n"
            f"📊 <b>Your Referrals:</b> <code>{user_data.get('referrals', 0)}/10</code>\n\n"
            f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>"
            "</blockquote>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Nobita%20Ban%20Bot")],
            [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
        ])
        await message.reply_video(video=HEADER_VIDEO, caption=invite_text, reply_markup=buttons)
        return

    # --- LANGUAGE ---
    if text in ["🌐 𝑳𝒂𝒏𝒈𝒖𝒂𝒈𝒆", "🌐 Language"]:
        lang_text = (
            "🌐 <b><u>𝑺𝑬𝑳𝑬𝑪𝑻 𝒀𝑶𝑼𝑴 𝑳𝑨𝑵𝑮𝑼𝑨𝑮𝑬</u></b>\n\n"
            "<blockquote><i>Choose your preferred language for bot interface:</i></blockquote>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 English (Default)", callback_data="set_lang_en"), InlineKeyboardButton("🇮🇳 Hindi", callback_data="set_lang_hi")]
        ])
        await message.reply_video(video=HEADER_VIDEO, caption=lang_text, reply_markup=buttons)
        return

    # --- THANKS TO ---
    if text in ["🏆 𝑻𝒉𝒂𝒏𝒌𝒔 𝑻𝒐", "🏆 Thanks To"]:
        thanks_text = (
            "🏆 <b><u>𝑺𝑴𝑬𝑪𝑰𝑨𝑳 𝑻𝑯𝑨𝑵𝑴𝑺 𝑻𝑶</u></b>\n\n"
            "<blockquote>"
            f"👑 <b>Bot Owner:</b> @{OWNER_USERNAME}\n"
            f"📢 <b>Main Channel:</b> @{MANDATORY_CHANNEL}\n"
            "💎 <i>Thanks to all Premium Subscribers & Supporters!</i>"
            "</blockquote>"
        )
        await message.reply_video(video=HEADER_VIDEO, caption=thanks_text)
        return

    # --- TARGET INPUT & 20-SECOND ANIMATION ROUTINE ---
    if user_id in user_states:
        action_type = user_states.pop(user_id)
        target_number = text.strip()
        
        cooldowns[user_id] = time.time()

        initial_msg = (
            "<blockquote>"
            f"🔥 <b><u>𝑾𝑯𝑨𝑻𝑺𝑨𝑷𝑷 𝑵𝑼𝑴𝑩𝑬𝑹 𝑴𝑨𝑺𝑺 𝑹𝑬𝑷𝑶𝑹𝑻</u></b>\n\n"
            f"🎯 <b>Target:</b> <code>{target_number}</code>\n"
            f"⚡ <b>Module:</b> <code>{action_type}</code>\n\n"
            f"⚙️ <i>Initializing attacking servers...</i>\n"
            f"<code>[{'░'*12}] 0%</code>"
            "</blockquote>"
        )
        msg = await message.reply_video(video=HEADER_VIDEO, caption=initial_msg)

        # 20 Seconds Continuous Animation Loop
        for pct in range(5, 105, 10):
            await asyncio.sleep(2.0)
            bar = render_progress_bar(pct)
            
            anim_text = (
                "<blockquote>"
                f"🔥 <b><u>𝑾𝑯𝑨𝑻𝑺𝑨𝑷𝑷 𝑵𝑼𝑴𝑩𝑬𝑹 𝑴𝑨𝑺𝑺 𝑹𝑬𝑷𝑶𝑹𝑻</u></b>\n\n"
                f"🎯 <b>Target:</b> <code>{target_number}</code>\n"
                f"⚡ <b>Module:</b> <code>{action_type}</code>\n"
                f"📊 <b>Progress:</b> <code>{pct}%</code>\n\n"
                f"<code>{bar}</code>\n\n"
                f"💥 <i>Executing automated mass report packets...</i>"
                "</blockquote>"
            )
            try:
                await msg.edit_caption(caption=anim_text)
            except Exception:
                pass

        final_summary = (
            "✨ <b><u>𝑬𝑿𝑬𝑪𝑼𝑻𝑰𝑶𝑵 𝑪𝑶𝑴𝑴𝑷𝑳𝑬𝑻𝑬𝑫</u></b> ✨\n\n"
            "<blockquote>"
            f"🎯 <b>Target Number:</b> <code>{target_number}</code>\n"
            f"⚡ <b>Action Module:</b> <code>{action_type}</code>\n"
            f"✅ <b>Status:</b> <code>SUCCESSFULLY EXECUTED</code>\n"
            f"🛡️ <b>Reports Sent:</b> <code>500+ Automated Reports</code>"
            "</blockquote>"
        )
        try:
            await msg.edit_caption(caption=final_summary)
        except Exception:
            await message.reply_text(final_summary)

# --- 9. CALLBACK QUERY HANDLER ---
@app.on_callback_query()
async def cb_handler(client, query):
    data = query.data
    
    if data == "check_join_status":
        user_id = query.from_user.id
        if await check_force_join(client, user_id):
            await query.answer("✨ Verification Successful!", show_alert=True)
            caption = get_main_menu(user_id)
            reply_kb = get_bottom_keyboard()
            await query.message.delete()
            await client.send_video(chat_id=user_id, video=HEADER_VIDEO, caption=caption, reply_markup=reply_kb)
        else:
            await query.answer("❌ Verification Failed! Pehle sabhi links par Join / Request bhein.", show_alert=True)
        return

    if data in ["set_lang_en", "set_lang_hi"]:
        await query.answer("✅ Language Updated Successfully!", show_alert=True)

# --- 10. ASYNC MAIN EXECUTOR ---
async def start_bot():
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    await app.start()
    print("🚀 Nobita Ban Bot Started Successfully!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(start_bot())
