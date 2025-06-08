import os
import re
from flask import Flask, request
from telegram import Bot, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Dispatcher, MessageHandler, filters, CommandHandler
from telegram.ext import CallbackContext
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)

# Dispatcher بدون صف انتظار (برای webhook)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

# لیست فحش‌های ممنوعه (قابل گسترش)
BAD_WORDS = ["فحش", "ناسزا", "بد"]

# --- ضد لینک و فحاشی و حذف پیام‌های فوروارد ---
def message_filter(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text or ""

    # ضد لینک
    if re.search(r"https?://|t\.me|telegram\.me|www\.", text, re.IGNORECASE):
        try:
            message.delete()
            return
        except:
            pass

    # ضد فحاشی
    if any(bad in text.lower() for bad in BAD_WORDS):
        try:
            message.delete()
            return
        except:
            pass

    # حذف پیام فوروارد شده
    if message.forward_from or message.forward_from_chat:
        try:
            message.delete()
            return
        except:
            pass

    # اگر پیام حاوی "من" بود، مشخصات کاربر رو بفرست
    if "من" in text:
        user = message.from_user
        chat = message.chat
        member = chat.get_member(user.id)

        name = user.full_name
        username = f"@{user.username}" if user.username else "ندارد"
        status_map = {
            ChatMemberStatus.OWNER: "مالک",
            ChatMemberStatus.ADMINISTRATOR: "ادمین",
            ChatMemberStatus.MEMBER: "عضو",
        }
        status = status_map.get(member.status, "ناشناس")

        reply = f"\n👤 نام: {name}\n🔗 یوزرنیم: {username}\n🎖 مقام: {status}"
        message.reply_text(reply)

# --- خوش‌آمدگویی ---
def welcome(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        name = member.full_name
        update.message.reply_text(f"🌟 خوش اومدی {name}!")

# --- افزودن مدیر ---
def promote_command(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = message.chat_id

    if not message.reply_to_message:
        message.reply_text("برای افزودن مدیر باید روی پیام شخص ریپلای کنی.")
        return

    user_id = message.reply_to_message.from_user.id

    try:
        bot.promote_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_promote_members=False,
            can_invite_users=True,
        )
        message.reply_text("✅ کاربر با موفقیت مدیر شد!")
    except Exception as e:
        message.reply_text(f"⛔️ خطا: {e}")

# ثبت هندلرها
dispatcher.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
dispatcher.add_handler(CommandHandler("promote", promote_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, message_filter))

# --- وبهوک ---
@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Fire_flyer is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
