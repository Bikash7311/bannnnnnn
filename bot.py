import sys
import asyncio
import json
import os
import time

# --- EVENT LOOP FIX FOR PYTHON 3.10+ / 3.14 (RENDER FIX) ---
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
from hydrogram.errors import UserNotParticipant

# --- CONFIGURATION ---
API_ID = 33772941  
API_HASH = "3b6ab6b1940c87915439bb41e4e80ea8"  
BOT_TOKEN = "8904752333:AAFeTxNjK0VhzBU60qT8asTIZo09too2ahE"

OWNER_ID = 6132146801
OWNER_USERNAME = "Znonsence"
BOT_USERNAME = "Nobita_banbot"

MANDATORY_CHANNEL = "nobitabanxunban"
MANDATORY_GROUP_LINK = "https://t.me/chatgctest"
REQ_CHANNEL_LINK = "https://t.me/+vM_Qw32vxK81NmNl"

HEADER_VIDEO = "https://example.com/your_video.mp4"

# CLIENT INITIALIZATION
app = Client("NobitaBanBotSession", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- APPROVED REQUEST USERS FILE SYSTEM ---
REQ_FILE = "approved_users.json"

def load_approved_users():
    if os.path.exists(REQ_FILE):
        try:
            with open(REQ_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_approved_user(user_id):
    approved_req_users.add(user_id)
    with open(REQ_FILE, "w") as f:
        json.dump(list(approved_req_users), f)

approved_req_users = load_approved_users()
users_db = {}
cooldowns = {}
user_states = {}
COOLDOWN_TIME = 600

# --- JOIN REQUEST EVENT HANDLER ---

@app.on_chat_join_request()
async def track_join_requests(client, chat_join_request: ChatJoinRequest):
    user_id = chat_join_request.from_user.id
    save_approved_user(user_id)
    print(f"✅ [JOIN REQUEST APPROVED] User ID: {user_id}")

# --- HELPER FUNCTIONS ---

def render_progress_bar(percent: int, length: int = 10) -> str:
    filled = int(length * percent // 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent}%"

async def check_force_join(client, user_id):
    if user_id == OWNER_ID:
        return True
    
    # 1. Check Mandatory Channel Membership
    try:
        await client.get_chat_member(MANDATORY_CHANNEL, user_id)
    except UserNotParticipant:
        return False
    except Exception:
        pass

    # 2. Check if user sent a join request earlier
    if user_id in approved_req_users:
        return True

    # 3. Fallback Check: Direct membership in discussion group
    try:
        chat_member = await client.get_chat_member("chatgctest", user_id)
        if chat_member:
            save_approved_user(user_id)
            return True
    except Exception:
        pass

    return False

def get_force_join_menu():
    text = (
        "⚠️ <b><u>ACCESS DENIED - MANDATORY JOIN REQUIRED</u></b> ⚠️\n\n"
        "<i>Bot features use karne ke liye Main Channel Join karein aur Baaki Links par Request Send karein!</i>\n\n"
        "1️⃣ <b>Main Channel (Join Mandatory)</b>\n"
        "2️⃣ <b>Discussion Group (Send Request)</b>\n"
        "3️⃣ <b>Private Channel (Send Request)</b>\n\n"
        "✅ <i>Sabhi complete karne ke baad <b>'Try Again'</b> button par click karein.</i>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Main Channel", url=f"https://t.me/{MANDATORY_CHANNEL}")],
        [InlineKeyboardButton("💬 Request Group Join", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 Request Private Channel", url=REQ_CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 Try Again / Check Join", callback_data="check_join_status")]
    ])
    return text, buttons

def get_main_menu(user_id):
    user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
    
    if user_id == OWNER_ID:
        status_str = "⚡ 𝑶𝑾𝑵𝑬𝑹 ⚡"
    elif user_data['is_premium']:
        status_str = "💎 𝑷𝑹𝑬𝑴𝑰𝑼𝑴"
    else:
        status_str = "🪙 𝑭𝑹𝑬𝑬"

    caption = (
        "🔥 <b><u>𝑵𝑶𝑩𝑰𝑻𝑨 𝑿 𝑩𝑨𝑵 𝑩𝑶𝑻 𝑷𝑹𝑬𝑴𝑰𝑼𝑴</u></b> 🔥\n\n"
        "• 💀 Permanent Ban\n"
        "• ⏳ Temporary Ban\n"
        "• 🔍 Ban Status Checker\n"
        "• 💥 Mass Reporting System\n\n"
        "<code>┌───────────────┬───────────────┐\n"
        "│      Field    │     Value     │\n"
        "├───────────────┼───────────────┤\n"
        f"│ 👤 User       │ {user_id:<13} │\n"
        f"│ 👑 Status     │ {status_str:<13} │\n"
        f"│ 🔮 Referrals  │ {str(user_data['referrals'])+'/10':<13} │\n"
        "└───────────────┴───────────────┘</code>\n\n"
        "📸 <i>Choose an action below:</i>"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💀 Permanent Ban", callback_data="ban_perm"), InlineKeyboardButton("⏳ Temporary Ban", callback_data="ban_temp")],
        [InlineKeyboardButton("💥 Mass Report", callback_data="mass_report"), InlineKeyboardButton("⚡ Unban Target", callback_data="unban")],
        [InlineKeyboardButton("🔍 Ban Status Checker", callback_data="status"), InlineKeyboardButton("🤖 Bot Status", callback_data="bot_status")],
        [InlineKeyboardButton("💎 Invite Friends", callback_data="invite"), InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{MANDATORY_CHANNEL}"), InlineKeyboardButton("💬 Group", url=MANDATORY_GROUP_LINK)],
        [InlineKeyboardButton("🔒 Join Private Channel", url=REQ_CHANNEL_LINK)]
    ])
    return caption, buttons

# --- COMMAND HANDLERS ---

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_cmd(client, message):
    total_users = len(users_db)
    premium_users = sum(1 for u in users_db.values() if u['is_premium'])
    free_users = total_users - premium_users
    
    stats_text = (
        "📊 <b><u>NOBITA X BOT STATS</u></b>\n\n"
        f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
        f"💎 <b>Premium Users:</b> <code>{premium_users}</code>\n"
        f"🪙 <b>Free Users:</b> <code>{free_users}</code>"
    )
    await message.reply(stats_text)

@app.on_message(filters.command("addpremium") & filters.user(OWNER_ID))
async def add_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply("❌ <b>Usage:</b> <code>/addpremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id not in users_db:
            users_db[target_id] = {'referrals': 0, 'is_premium': True}
        else:
            users_db[target_id]['is_premium'] = True
        await message.reply(f"✅ User <code>{target_id}</code> upgraded to 💎 <b>PREMIUM</b>!")
    except ValueError:
        await message.reply("❌ Invalid User ID.")

@app.on_message(filters.command("rempremium") & filters.user(OWNER_ID))
async def rem_premium_cmd(client, message):
    if len(message.command) < 2:
        await message.reply("❌ <b>Usage:</b> <code>/rempremium <user_id></code>")
        return
    try:
        target_id = int(message.command[1])
        if target_id in users_db:
            users_db[target_id]['is_premium'] = False
            await message.reply(f"🔻 User <code>{target_id}</code> Premium status removed!")
        else:
            await message.reply("❌ User not found in database.")
    except ValueError:
        await message.reply("❌ Invalid User ID.")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("❌ <b>Reply to a message to broadcast.</b>")
        return
    
    msg = await message.reply("🚀 <b>Starting Broadcast...</b>")
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
        await message.reply_text(text, reply_markup=buttons)
        return

    if user_id not in users_db:
        users_db[user_id] = {'referrals': 0, 'is_premium': False}
        if len(message.command) > 1:
            try:
                ref_by = int(message.command[1])
                if ref_by in users_db and ref_by != user_id:
                    users_db[ref_by]['referrals'] += 1
                    if users_db[ref_by]['referrals'] >= 10:
                        users_db[ref_by]['is_premium'] = True
            except Exception:
                pass

    msg = await message.reply("⚙️ <i>Initializing System...</i>")
    await asyncio.sleep(0.3)
    await msg.edit("🔥 <i>Finalizing Animations...</i>")
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
        
        msg = await message.reply("⏳ <b>Please wait...</b>")
        
        for pct in [20, 40, 60, 80, 100]:
            await asyncio.sleep(0.8)
            bar = render_progress_bar(pct)
            
            table_text = (
                "<b>NOBITA X BAN BOT PREMIUM</b>\n\n"
                "<code>┌───────────────┬───────────────┐\n"
                f"│ Target Input  │ {target[:8]:<13} │\n"
                "├───────────────┼───────────────┤\n"
                f"│ Action        │ {action_type:<13} │\n"
                "├───────────────┼───────────────┤\n"
                f"│ Progress      │ {bar} │\n"
                "└───────────────┴───────────────┘</code>"
            )
            await msg.edit_text(table_text)

        final_output = (
            "✉️ <b>Action Execution Completed</b>\n\n"
            "📜 <i>Summary Log Output:</i>\n\n"
            f"<blockquote><b>Target:</b> {target}\n"
            f"<b>Action Module:</b> {action_type}\n"
            "<b>Status:</b> Interface routine rendered successfully.</blockquote>"
        )
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])
        await msg.edit_text(final_output, reply_markup=back_btn)

@app.on_callback_query()
async def cb_handler(client, query):
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_join_status":
        if await check_force_join(client, user_id):
            await query.answer("✅ Verification Successful!", show_alert=True)
            caption, buttons = get_main_menu(user_id)
            try:
                await query.message.edit_caption(caption=caption, reply_markup=buttons)
            except Exception:
                await query.message.edit_text(text=caption, reply_markup=buttons)
        else:
            await query.answer("❌ Aapne 1st channel join nahi kiya ya request send nahi kiya!", show_alert=True)
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
            "🚀 <b><u>INVITE & EARN PREMIUM</u></b>\n\n"
            "💡 <i>Invite 10 friends to automatically unlock 💎 PREMIUM Access!</i>\n\n"
            f"📊 <b>Your Referrals:</b> <code>{user_data['referrals']}/10</code>\n"
            f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Nobita%20Ban%20Bot")],
            [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ])
        try:
            await query.message.edit_caption(caption=invite_text, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=invite_text, reply_markup=buttons)
        return

    if data in ["ban_perm", "ban_temp", "mass_report", "unban"]:
        user_data = users_db.get(user_id, {'referrals': 0, 'is_premium': False})
        
        if user_id != OWNER_ID and not user_data['is_premium']:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            restricted_text = (
                "🚫 <b><u>ACCESS RESTRICTED</u></b> 🚫\n\n"
                "⚠️ <i>You are currently a 🪙 FREE User. Upgrade to 💎 PREMIUM to use this feature!</i>\n\n"
                f"📊 <b>Your Referrals:</b> <code>{user_data['referrals']}/10</code>\n\n"
                "🎯 <b><u>HOW TO UNLOCK PREMIUM?</u></b>\n"
                f"1️⃣ <b>Referral Method:</b> Invite 10 friends using your link:\n<code>{ref_link}</code>\n\n"
                f"2️⃣ <b>Direct Method:</b> Contact Owner to buy Premium."
            )
            restricted_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Nobita%20Ban%20Bot")],
                [InlineKeyboardButton("👑 Contact Owner for Premium", url=f"https://t.me/{OWNER_USERNAME}")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
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
            "🎯 <b><u>ENTER TARGET INFORMATION</u></b>\n\n"
            "✍️ <i>Please send the target input in standard format:</i>"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="back_to_menu")]])
        try:
            await query.message.edit_caption(caption=ask_text, reply_markup=buttons)
        except Exception:
            await query.message.edit_text(text=ask_text, reply_markup=buttons)

# --- BOT EXECUTION ---
if __name__ == "__main__":
    print("🚀 Nobita X Ban Bot Starting...")
    app.run()
