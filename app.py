import os
from flask import Flask, request
from telegram import Bot, Update, ChatMember
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext
from telegram.constants import ChatMemberStatus
from telegram.helpers import mention_html
from dotenv import load_dotenv
import re

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

BAD_WORDS = ['فحش1', 'فحش2', 'بدکلمه']  # ← اینو خودت کامل‌تر کن
LINK_PATTERN = r"(https?://|t\.me/|telegram\.me/)"

ADMIN_USERNAME =Secondsecurity


# 📌 خوش‌آمدگویی
def welcome(update: Update, context: CallbackContext):
    for user in update.message.new_chat_members:
        update.message.reply_text(f"خوش اومدی {user.first_name}! ❤️")


# 🧹 ضد لینک
def anti_link(update: Update, context: CallbackContext):
    if re.search(LINK_PATTERN, update.message.text or ""):
        update.message.delete()


# 🧼 ضد فحاشی
def anti_bad_words(update: Update, context: CallbackContext):
    if any(word in update.message.text.lower() for word in BAD_WORDS):
        update.message.delete()


# 🚫 حذف فوروارد
def no_forward(update: Update, context: CallbackContext):
    if update.message.forward_date:
        update.message.delete()


# 👤 نمایش مشخصات کاربر
def user_info(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat = update.effective_chat
    member = chat.get_member(user.id)

    status_map = {
        ChatMemberStatus.OWNER: "مالک",
        ChatMemberStatus.ADMINISTRATOR: "ادمین",
        ChatMemberStatus.MEMBER: "عضو معمولی",
        ChatMemberStatus.RESTRICTED: "محدودشده",
        ChatMemberStatus.LEFT: "ترک‌کرده",
        ChatMemberStatus.KICKED: "اخراج‌شده"
    }

    msg = f"""🔍 مشخصات شما:
👤 نام: {user.full_name}
🏷 یوزرنیم: @{user.username if user.username else 'ندارد'}
💼 مقام: {status_map.get(member.status, 'نامشخص')}
"""
    update.message.reply_text(msg)


# 🛡 افزودن مدیر
def add_admin(update: Update, context: CallbackContext):
    user = update.message.from_user
    if user.username == ADMIN_USERNAME:
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            update.effective_chat.promote_member(
                target.id,
                can_manage_chat=True,
                can_delete_messages=True,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=True
            )
            update.message.reply_text(f"✅ {target.full_name} ادمین شد.")
        else:
            update.message.reply_text("روی پیام کسی ریپلای کن تا ادمینش کنم.")
    else:
        update.message.reply_text("⛔ فقط سازنده‌ی ربات می‌تونه این کارو انجام بده.")


# 🔧 هندلرها
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(LINK_PATTERN), anti_link))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex("|".join(BAD_WORDS)), anti_bad_words))
dispatcher.add_handler(MessageHandler(Filters.forwarded, no_forward))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, user_info))
dispatcher.add_handler(CommandHandler("addadmin", add_admin))


# 🌐 webhook endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Fire Flyer Bot is alive 🚀"


if __name__ == "__main__":
    app.run(port=8080)
