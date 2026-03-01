import os
import uuid
import time
from datetime import datetime
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
BASE_URL = "http://api.ucbot.store"

if not BOT_TOKEN or not API_TOKEN:
    raise ValueError("BOT_TOKEN or API_TOKEN not set!")

app = ApplicationBuilder().token(BOT_TOKEN).build()

async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("Usage: UID VOUCHER1 VOUCHER2 ...")
            return

        playerid = parts[0]
        vouchers = parts[1:]

        payload = {
            "orderid": str(uuid.uuid4()),
            "playerid": playerid,
            "code": " ".join(vouchers)
        }

        headers = {
            "Authorization": f"{API_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(f"{BASE_URL}/topup-sync", json=payload, headers=headers)
        data = response.json()

        end_time = time.time()
        time_taken = round(end_time - time.time(), 2)
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        if "batch" in data:
            failed_count = data.get("failed", 0)
            overall_status = "SUCCESS" if failed_count == 0 else "PARTIAL / FAILED"

            message = "━━━━━━━━━━━━━━━━━━━\n"
            message += "🎮 TOP-UP RESULT\n"
            message += "━━━━━━━━━━━━━━━━━━━\n\n"

            message += f"🎮 Player Name  : {data.get('username', 'Unknown')}\n"
            message += f"🔢 Player ID    : {playerid}\n"
            message += f"📅 Date         : {date_str}\n"
            message += f"⏰ Time         : {time_str}\n"
            message += f"⚡ Time Taken   : {time_taken} sec\n"
            message += f"📊 Status       : {overall_status}\n\n"

            message += "🎟 Voucher Details:\n"
            message += "━━━━━━━━━━━━━━━━━━━\n"
            for i, item in enumerate(data.get("batch", []), start=1):
                if item["ok"]:
                    status_text = "SUCCESS"
                else:
                    detail_lower = item["detail"].lower()
                    if "used" in detail_lower:
                        status_text = "USED"
                    else:
                        status_text = "PROBLEM"

                message += f"{i}. {item['uc']}\n"
                message += f"   ➜ Status : {status_text}\n"
                message += f"   ➜ Detail : {item['detail']}\n\n"

            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"❌ Top-up Failed\nResponse:\n{data}")

    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected Error:\n{e}")

# Add handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, topup))

# Vercel handler
async def handler(request):
    if request.method == "POST":
        update = Update.de_json(await request.json(), app.bot)
        await app.initialize()
        await app.process_update(update)
        return {"statusCode": 200, "body": "ok"}
    return {"statusCode": 200, "body": "Bot is running"}