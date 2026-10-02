 import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
    filters,
)

# Loggingni sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- SOZLAMALAR ---
TOKEN = "SIZNING_BOT_TOKENINGIZ"  # O'z bot tokeningizni yozing
CHANNEL_ID = "@kanal_username"     # Kanal username yoki ID raqami (masalan: @bilagon_kanal)

# --- BAZA BILAN ISHLASH (Eski foydalanuvchilar va ma'lumotlar saqlanadi) ---
def init_db():
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    # Foydalanuvchilar jadvali (mavjud bo'lsa o'zgarmaydi, ma'lumotlar saqlanadi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            fullname TEXT,
            balance INTEGER DEFAULT 0,
            referrals_count INTEGER DEFAULT 0,
            referred_by INTEGER,
            is_subscribed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance, referrals_count, referred_by, is_subscribed FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username, fullname, referred_by=None):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute("""
            INSERT INTO users (user_id, username, fullname, referred_by)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, fullname, referred_by))
        
        # Agar referal orqali kirgan bo'lsa va o'zini o'zi taklif qilmagan bo'lsa
        if referred_by and referred_by != user_id:
            cursor.execute("""
                UPDATE users SET referrals_count = referrals_count + 1, balance = balance + 1 
                WHERE user_id = ?
            """, (referred_by,))
        conn.commit()
    conn.close()

def update_subscription_status(user_id, status: int):
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_subscribed = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

# Kanalga a'zolikni tekshirish
async def check_sub_channel(user_id, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Agar foydalanuvchi a'zo bo'lsa (creator, administrator, member)
        if member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR, ChatMember.MEMBER]:
            update_subscription_status(user_id, 1)
            return True
        else:
            update_subscription_status(user_id, 0)
            return False
    except Exception as e:
        logger.error(f"Kanalga a'zolikni tekshirishda xatolik: {e}")
        # Agar xatolik bo'lsa (masalan, bot kanalda admin bo'lmasa), bazadagi holatga tayanadi
        user = get_user(user_id)
        return user and user[4] == 1

# --- START BUYRUG'I VA REFERAL TIZIMI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    referred_by = None
    if args and args[0].isdigit():
        potential_ref = int(args[0])
        if potential_ref != user.id:
            referred_by = potential_ref

    # Foydalanuvchini bazaga qo'shish (eski ma'lumotlar o'chib ketmaydi)
    add_user(user.id, user.username, user.full_name, referred_by)

    # Kanalga a'zoligini tekshiramiz
    is_subbed = await check_sub_channel(user.id, context)

    if not is_subbed:
        # A'zo bo'lmagan bo'lsa, kanalga obuna bo'lishni so'raymiz
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 Botdan foydalanish uchun avval quyidagi kanalimizga a'zo bo'lishingiz kerak:",
            reply_markup=reply_markup
        )
    else:
        # Oldindan a'zo bo'lgan bo'lsa, to'g'ridan-to'g'ri asosiy menyu chiqadi (so'rovnoma tashlash so'ralmaydi)
        await show_main_menu(update, context)

# Obunani tekshirish tugmasi bosilganda
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    is_subbed = await check_sub_channel(user_id, context)

    if is_subbed:
        await query.message.edit_text("Rahmat! Obuna tasdiqlandi. 🎉")
        # Yangi xabar sifatida asosiy menyuni yuboramiz
        fake_update = Update(update.update_id, message=query.message)
        # Context orqali foydalanuvchi ma'nosini tiklaymiz
        await show_main_menu_by_chat(query.message.chat_id, user_id, context)
    else:
        await query.answer("Siz hali kanalga a'zo bo'lmadingiz! Iltimos, avval kanalga a'zo bo'ling.", show_alert=True)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    balance = user[1] if user else 0
    refs = user[2] if user else 0

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"<b>🤖 Xush kelibsiz, {update.effective_user.first_name}!</b>\n\n"
        f"💡 Sizning balansingiz: <b>{balance}</b> ball\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{refs}</b> ta\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n<code>{ref_link}</code>"
    )

    keyboard = [
        [InlineKeyboardButton("👥 Referallarim", callback_data="my_refs")],
        [InlineKeyboardButton("🎮 Viktorinani boshlash", callback_data="start_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def show_main_menu_by_chat(chat_id, user_id, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(user_id)
    balance = user[1] if user else 0
    refs = user[2] if user else 0

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"<b>🤖 Xush kelibsiz!</b>\n\n"
        f"💡 Sizning balansingiz: <b>{balance}</b> ball\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{refs}</b> ta\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n<code>{ref_link}</code>"
    )

    keyboard = [
        [InlineKeyboardButton("👥 Referallarim", callback_data="my_refs")],
        [InlineKeyboardButton("🎮 Viktorinani boshlash", callback_data="start_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")

# Referallarim tugmasi bosilganda
async def my_refs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)
    refs = user[2] if user else 0
    
    await query.answer()
    await query.message.edit_text(
        f"👥 <b>Siz taklif qilgan do'stlar statistikasi:</b>\n\n"
        f"Jami taklif qilingan do'stlar: <b>{refs} ta</b>\n"
        f"Har bir do'st uchun ball qo'shilib boradi!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]])
    )

async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    user = get_user(user_id)
    balance = user[1] if user else 0
    refs = user[2] if user else 0
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    text = (
        f"<b>🤖 Asosiy menyu:</b>\n\n"
        f"💡 Sizning balansingiz: <b>{balance}</b> ball\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{refs}</b> ta\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n<code>{ref_link}</code>"
    )
    keyboard = [
        [InlineKeyboardButton("👥 Referallarim", callback_data="my_refs")],
        [InlineKeyboardButton("🎮 Viktorinani boshlash", callback_data="start_quiz")]
    ]
    await query.message.edit_text(text, reply_markup=reply_markup_generator(keyboard), parse_mode="HTML")

def reply_markup_generator(keyboard):
    return InlineKeyboardMarkup(keyboard)

# --- ASOSIY MAIN FUNKSIYASI ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(my_refs_callback, pattern="^my_refs$"))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^back_to_menu$"))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
