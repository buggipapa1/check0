from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import uuid
import time
import asyncio
from datetime import datetime

# --- Configuration ---
TOKEN = "8257436505:AAG_-VLawZVUYRa_OqWmAxiJXpWvzHDTOFg"   # apna bot token daalo
OWNER_USER_ID = 7501870513     # apna telegram user id daalo
OWNER_USERNAME = "@TF_BUGGI"   # Owner ka username
FORCE_JOIN = "UPPERMOONxCHATGROUP"  # channel/group username without @

# --- Storage ---
users = {}   # {userid: {"username": str, "coins": int}}
codes = {}   # {code: {"amount": int, "maxusers": int, "redeemed": list}}
deduct_amount = 1  # default deduction

# --- API and Formatting Functions ---
def call_api(number, retries=3, delay=1):
    url = f"https://pirate-osint.onrender.com/api?key=kQ5hlafjxfgJTJ5d&num={number}"
    for _ in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        time.sleep(delay)
    return None

def format_response(data, number):
    if not data:
        return "⚠️ No details found."

    result = [f"📱 *Result for {number}*:\n"]
    for idx, item in enumerate(data, start=1):
        result.append(
            f"🔹 *Record {idx}*\n"
            f"👤 Name: `{item.get('name', 'N/A')}`\n"
            f"👨‍👩‍👦 Father: `{item.get('father_name', 'N/A')}`\n"
            f"📍 Address: `{item.get('address', 'N/A')}`\n"
            f"📞 Mobile: `{item.get('mobile', 'N/A')}`\n"
            f"☎️ Alt Mobile: `{item.get('alt_mobile', 'N/A')}`\n"
            f"🌐 Circle: `{item.get('circle', 'N/A')}`\n"
            f"🆔 ID: `{item.get('id_number', 'N/A')}`\n"
            f"📧 Email: `{item.get('email', 'N/A')}`\n"
            "---------------------------"
        )
    return "\n".join(result)

# --- Utils ---
def add_user(user):
    if user.id not in users:
        users[user.id] = {"username": user.username or user.full_name, "coins": 2}  # 2 free coins for new users

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = await context.bot.get_chat_member(f"@{FORCE_JOIN}", update.effective_user.id)
        if user.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except:
        return False

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_joined(update, context):
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{FORCE_JOIN}")],
            [InlineKeyboardButton("📞 Support", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
        ]
        await update.message.reply_text(
            "🚨 You must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    add_user(user)
    bal = users[user.id]["coins"]

    keyboard = [
        [InlineKeyboardButton("💰 My Coins", callback_data="check_coins")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help_user")],
        [InlineKeyboardButton("📞 Support", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
    ]

    await update.message.reply_text(
        f"👋 Welcome *{user.first_name}*!\n\n"
        f"🎁 You already have *{bal} coins* in your account.\n"
        f"🔍 Send me a number and I will fetch details for you.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_USER_ID:
        keyboard = [
            [InlineKeyboardButton("User Commands", callback_data="help_user")],
            [InlineKeyboardButton("Owner Commands", callback_data="help_owner")]
        ]
    else:
        keyboard = [[InlineKeyboardButton("User Commands", callback_data="help_user")]]
    await update.message.reply_text("📖 Help Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_user":
        text = """🤖 User Commands:
/start - Start bot
/coins - Check balance
/redeem <code> - Redeem coins"""
    elif query.data == "help_owner":
        text = """👑 Owner Commands:
/addcoins <userid> <amount>
/removecoin <userid> <amount>
/setdeduct <amount>
/users - List users
/createcode <amount> <maxusers>"""
    await query.edit_message_text(text)

async def start_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_coins":
        bal = users.get(query.from_user.id, {}).get("coins", 0)
        await query.edit_message_text(f"💰 Your balance: {bal} coins")

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)
    bal = users[update.effective_user.id]["coins"]
    await update.message.reply_text(f"💰 You have {bal} coins.")

async def addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
        if uid in users:
            users[uid]["coins"] += amt
            await context.bot.send_message(uid, f"💰 You received {amt} coins. Added by {OWNER_USERNAME}.")
            await update.message.reply_text("✅ Coins added.")
    except:
        await update.message.reply_text("❌ Usage: /addcoins userid amount")

async def removecoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
        if uid in users and users[uid]["coins"] >= amt:
            users[uid]["coins"] -= amt
            await context.bot.send_message(uid, f"❌ {amt} coins removed by {OWNER_USERNAME}.")
            await update.message.reply_text("✅ Coins removed.")
    except:
        await update.message.reply_text("❌ Usage: /removecoin userid amount")

async def setdeduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global deduct_amount
    if update.effective_user.id != OWNER_USER_ID:
        return
    try:
        deduct_amount = int(context.args[0])
        await update.message.reply_text(f"✅ Deduction set to {deduct_amount} per search.")
    except:
        await update.message.reply_text("❌ Usage: /setdeduct amount")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    msg = ["👥 Users:"]
    for uid, data in users.items():
        msg.append(f"{data['username']} | {uid} | {data['coins']} coins")
    await update.message.reply_text("\n".join(msg))

async def createcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    try:
        amount = int(context.args[0]); maxu = int(context.args[1])
        code = str(uuid.uuid4())[:8]
        codes[code] = {"amount": amount, "maxusers": maxu, "redeemed": []}
        keyboard = [[InlineKeyboardButton("Personal", callback_data=f"personal_{code}"),
                     InlineKeyboardButton("Giveaway", callback_data=f"giveaway_{code}")]]
        await update.message.reply_text(f"🎟️ Code created: {code}", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("❌ Usage: /createcode amount maxusers")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)
    try:
        code = context.args[0]
        if code in codes:
            data = codes[code]
            if update.effective_user.id in data["redeemed"]:
                await update.message.reply_text("❌ You already used this code.")
                return
            if len(data["redeemed"]) >= data["maxusers"]:
                await update.message.reply_text("❌ Code limit reached.")
                return
            users[update.effective_user.id]["coins"] += data["amount"]
            data["redeemed"].append(update.effective_user.id)
            await update.message.reply_text(f"✅ You got {data['amount']} coins!")
        else:
            await update.message.reply_text("❌ Invalid code.")
    except:
        await update.message.reply_text("❌ Usage: /redeem <code>")

async def code_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("personal_"):
        code = query.data.split("_")[1]
        await query.edit_message_text(f"🔒 Personal code created: {code}")
    elif query.data.startswith("giveaway_"):
        code = query.data.split("_")[1]
        for uid in users:
            try:
                await context.bot.send_message(uid, f"🎉 Giveaway! Use /redeem {code} to get free coins!")
            except:
                pass
        await query.edit_message_text(f"📢 Giveaway code sent to all users: {code}")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(update, context):
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{FORCE_JOIN}")],
            [InlineKeyboardButton("📞 Support", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
        ]
        await update.message.reply_text(
            "🚨 Please join our channel first.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    add_user(update.effective_user)
    uid = update.effective_user.id
    if users[uid]["coins"] < deduct_amount:
        await update.message.reply_text(f"❌ Not enough coins. Buy from {OWNER_USERNAME}")
        return

    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("❌ Kripya ek valid number bhejein.")
        return

    analyzing_msg = await update.message.reply_text("🔴 Ꭿɳαℓყzιɳɠ . 0%")
    start_time = time.time()
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, call_api, number)
    end_time = time.time()

    duration = max(2, end_time - start_time)
    steps = 30
    step_delay = duration / steps  
    dot_patterns = [".", "..", "...", "....", "....."]
    colors = ["🔴", "🟡", "🟢"]

    for i in range(steps):
        dots = dot_patterns[i % len(dot_patterns)]
        color = colors[i % len(colors)]
        percent = int((i + 1) * (100 / steps))
        try:
            await analyzing_msg.edit_text(f"{color} Ꭿɳαℓყzιɳɠ {dots} {percent}%")
        except:
            pass
        await asyncio.sleep(step_delay)

    try:
        await analyzing_msg.edit_text("🟢 ✔️ Analysis Complete!")
    except:
        pass
    await asyncio.sleep(1.5)

    if data and isinstance(data, list) and len(data) > 0:
        formatted = format_response(data, number)
        users[uid]["coins"] -= deduct_amount
        await analyzing_msg.edit_text(
            f"{formatted}\n\n💰 Coins deducted: {deduct_amount}\nRemaining: {users[uid]['coins']}",
            parse_mode="Markdown"
        )
    else:
        await analyzing_msg.edit_text("⚠️ No details found. Coins not deducted.")

# --- Bot start function ---
def main():
    app = Application.builder().token(TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(help_buttons, pattern="help_"))
    app.add_handler(CallbackQueryHandler(start_buttons, pattern="check_coins"))
    app.add_handler(CommandHandler("coins", coins))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CallbackQueryHandler(code_buttons, pattern="(personal_|giveaway_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    # Owner commands
    app.add_handler(CommandHandler("addcoins", addcoins))
    app.add_handler(CommandHandler("removecoin", removecoin))
    app.add_handler(CommandHandler("setdeduct", setdeduct))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("createcode", createcode))

    print("🤖 Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()