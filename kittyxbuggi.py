from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import uuid
import time
import asyncio
from datetime import datetime, timedelta

# --- Configuration ---
TOKEN = "7018741878:AAHlCp46jAeKWUVNENQJMECYeRjqC8FtLkg"   # apna bot token daalo
OWNER_USER_ID = 7501870513  # apna telegram user id daalo

# Dictionaries to store keys and user access
redeem_keys = {}
user_access = {}

# --- API and Formatting Functions ---

def call_api(number, retries=3, delay=1):
    """Call OSINT API with retry system"""
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

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Mujhe koi number bhejo, main uski info dunga 🔍\n"
        "Agar aapke paas key hai, toh use karne ke liye /redeem command use karein."
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Access check
    if user_id not in user_access or user_access[user_id] < current_time:
        await update.message.reply_text("❌ Aapke paas access nahi hai. Access lene ke liye /redeem command use karein.")
        return

    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("❌ Kripya ek valid number bhejein.")
        return

    # Step 1: Initial message
    analyzing_msg = await update.message.reply_text("🔴 Ꭿɳαℓყzιɳɠ . 0%")

    # Step 2: Start API call (measure time)
    start_time = time.time()
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, call_api, number)
    end_time = time.time()

    duration = max(2, end_time - start_time)  # at least 2s
    steps = 30
    step_delay = duration / steps  

    # Step 3: Animate blinking dots + colors
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

    # Step 4: Flash "Analysis Complete!"
    try:
        await analyzing_msg.edit_text("🟢 ✔️ Analysis Complete!")
    except:
        pass
    await asyncio.sleep(1.5)

    # Step 5: Show result
    if data and isinstance(data, list) and len(data) > 0:
        formatted = format_response(data, number)
        await analyzing_msg.edit_text(formatted, parse_mode="Markdown")
    else:
        await analyzing_msg.edit_text("⚠️ No details found.")

async def redeem_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        key_to_redeem = context.args[0]
        if key_to_redeem in redeem_keys:
            key_data = redeem_keys[key_to_redeem]
            if key_data['is_used']:
                await update.message.reply_text("❌ Yeh key pehle hi istemaal ho chuki hai.")
            else:
                expiry = key_data['expiry_date']
                key_data['is_used'] = True
                key_data['used_by'] = user_id
                user_access[user_id] = expiry
                
                await update.message.reply_text(
                    f"✅ Key successfully redeem ho gayi hai! Aapka access {expiry.strftime('%Y-%m-%d %H:%M:%S')} tak valid hai."
                )
        else:
            await update.message.reply_text("❌ Invalid key. Kripya sahi key daalein.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Kripya /redeem <key> format ka upyog karein.")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Aapko is command ka upyog karne ki anumati nahi hai.")
        return

    try:
        days = int(context.args[0])
        new_key = str(uuid.uuid4())[:8]
        expiry_date = datetime.now() + timedelta(days=days)
        redeem_keys[new_key] = {
            'expiry_date': expiry_date,
            'is_used': False,
            'used_by': None
        }
        await update.message.reply_text(
            f"✅ Nayi key ban gayi hai: `{new_key}`\nYeh {days} dinon ke liye valid hai."
        )
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Kripya /genkey <days> format ka upyog karein.")

async def deletekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Aapko is command ka upyog karne ki anumati nahi hai.")
        return

    try:
        key_to_delete = context.args[0]
        if key_to_delete in redeem_keys:
            if redeem_keys[key_to_delete]['used_by']:
                del user_access[redeem_keys[key_to_delete]['used_by']]
            del redeem_keys[key_to_delete]
            await update.message.reply_text(f"✅ Key `{key_to_delete}` successfully delete ho gayi hai.")
        else:
            await update.message.reply_text("❌ Invalid key. Key mili nahi.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Kripya /deletekey <key> format ka upyog karein.")

async def list_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Aapko is command ka upyog karne ki anumati nahi hai.")
        return

    if not redeem_keys:
        await update.message.reply_text("ℹ️ Koi keys nahi hain.")
        return

    message = ["🔑 *All Keys:*\n"]
    for key, data in redeem_keys.items():
        status = "Used" if data['is_used'] else "Unused"
        used_by = f"Used by: `{data['used_by']}`" if data['used_by'] else ""
        message.append(
            f"`{key}` - Status: *{status}* | Expiry: `{data['expiry_date'].strftime('%Y-%m-%d')}` {used_by}"
        )
    
    await update.message.reply_text("\n".join(message), parse_mode="Markdown")

# --- Bot start function ---

def main():
    app = Application.builder().token(TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem_key))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    # Owner commands
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("deletekey", deletekey))
    app.add_handler(CommandHandler("keys", list_keys))

    print("🤖 Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()