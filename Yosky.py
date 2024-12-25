import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import firebase_admin
from firebase_admin import credentials, db

# إعدادات البوت وفايربيس
BOT_TOKEN = "7720038332:AAHHORfYTl5kRTeYVZFvfVmfzDadGyGYjRE"
cred = credentials.Certificate("/storage/emulated/0/Yosky.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://correspondent-c7f06-default-rtdb.firebaseio.com/"
})

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}

# دالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📺 أنمي", callback_data="type_anime"),
        InlineKeyboardButton("🎥 أفلام", callback_data="type_movies"),
        InlineKeyboardButton("📚 مانجا", callback_data="type_manga"),
        InlineKeyboardButton("📖 مانهوا", callback_data="type_manhwa"),
    ]
    markup.add(*buttons)
    bot.send_message(
        message.chat.id,
        "🎉 *مرحبًا بك في بوت Yosky!* 🎉\n\n"
        "🔎 اختر نوع المحتوى الذي تريده:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# معالجة الردود
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("type_"):
        selected_type = data.split("_")[1]
        user_state[chat_id] = {"type": selected_type, "classification": None, "index": 0}
        send_classification_menu(call.message, selected_type)

    elif data.startswith("class_"):
        classification = data.split("_")[1]
        user_state[chat_id]["classification"] = classification
        user_state[chat_id]["index"] = 0
        send_content_details(call.message, classification, 0, True)

    elif data.startswith("more_"):
        classification = data.split("_")[1]
        current_index = user_state[chat_id].get("index", 0)
        send_content_details(call.message, classification, current_index + 1, False)

    elif data == "back":
        # عند الضغط على زر الرجوع من التصنيفات، نعود للقائمة الرئيسية
        send_welcome(call.message)

# عرض قائمة التصنيفات بناءً على النوع
def send_classification_menu(message, selected_type):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []

    # إضافة تصنيفات حسب النوع
    if selected_type == "anime":
        buttons = [
            InlineKeyboardButton("👊 شونين", callback_data="class_shonen"),
            InlineKeyboardButton("👧 شوجو", callback_data="class_shojo"),
            InlineKeyboardButton("🌀 إيسيكاي", callback_data="class_isekai"),
            InlineKeyboardButton("🌌 خيال علمي", callback_data="class_scifi"),
            InlineKeyboardButton("❤️ رومانس", callback_data="class_romance"),
            InlineKeyboardButton("🔪 إثارة", callback_data="class_thriller"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back")
        ]
    elif selected_type == "movies":
        buttons = [
            InlineKeyboardButton("🎬 دراما", callback_data="class_drama"),
            InlineKeyboardButton("💥 أكشن", callback_data="class_action"),
            InlineKeyboardButton("🧟‍♂️ رعب", callback_data="class_horror"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back")
        ]
    elif selected_type == "manga":
        buttons = [
            InlineKeyboardButton("🧠 دراما", callback_data="class_drama"),
            InlineKeyboardButton("💥 أكشن", callback_data="class_action"),
            InlineKeyboardButton("🎮 رياضة", callback_data="class_sports"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back")
        ]
    elif selected_type == "manhwa":
        buttons = [
            InlineKeyboardButton("🌟 أكشن", callback_data="class_action"),
            InlineKeyboardButton("🎭 دراما", callback_data="class_drama"),
            InlineKeyboardButton("⚔️ مغامرات", callback_data="class_adventure"),
            InlineKeyboardButton("🔙 رجوع", callback_data="back")
        ]

    markup.add(*buttons)
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=f"📂 *اختر تصنيفًا داخل قسم {selected_type}:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# عرض المحتوى بناءً على التصنيف
def send_content_details(message, classification, index, is_new):
    chat_id = message.chat.id
    selected_type = user_state[chat_id]["type"]

    ref = db.reference("info")
    content_list = ref.get()

    if content_list:
        # تصفية البيانات حسب النوع والتصنيف
        filtered_list = [
            value for value in content_list.values()
            if value.get("type") == selected_type and value.get("classification") == classification
        ]

        if not filtered_list:
            bot.send_message(chat_id, "❌ لا توجد بيانات متوفرة في هذا التصنيف.")
            return

        # إعادة الفهرس إذا تجاوز الطول
        if index >= len(filtered_list):
            index = 0

        data = filtered_list[index]
        user_state[chat_id]["index"] = index  # تحديث الفهرس الحالي

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("👀 عرض المزيد", callback_data=f"more_{classification}")
        )

        if is_new:
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message.message_id,
                media=InputMediaPhoto(
                    media=data["image"],
                    caption=(
                        f"🌟 *{data['title']}*\n\n"
                        f"📝 _{data['description']}_\n\n"
                        f"📚 *تصنيف:* `{classification}`"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=markup
            )
        else:
            # تحديث الرسالة والصورة باستخدام edit_message_media
            media = InputMediaPhoto(
                media=data["image"],
                caption=(
                    f"🌟 *{data['title']}*\n\n"
                    f"📝 _{data['description']}_\n\n"
                    f"📚 *تصنيف:* `{classification}`"
                ),
                parse_mode="Markdown"
            )
            bot.edit_message_media(
                chat_id=chat_id,
                message_id=message.message_id,
                media=media,
                reply_markup=markup
            )

# تشغيل البوت
bot.polling()