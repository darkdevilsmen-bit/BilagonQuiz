import os
import html
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import (
    TelegramObject,
    Message,
    CallbackQuery,
    ChatJoinRequest,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8963661833:AAENuseyKPy2iHz9LYldALkfr6Z3DdTJR5w")
CHANNEL_ID = -1004317372728
CHANNEL_INVITE_LINK = "https://t.me/+llFGqeWBsuZlMGYy"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# So'rov tashlagan foydalanuvchilar ID ro'yxati (xotirada saqlanadi)
PENDING_REQUEST_USERS = set()


# ==================== YORDAMCHI FUNKSIYALAR ====================
def get_subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga so'rov yuborish", 
                    url=CHANNEL_INVITE_LINK
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish", 
                    callback_data="check_subscription"
                )
            ]
        ]
    )


async def has_access(user_id: int) -> bool:
    # 1. Agar foydalanuvchi kanalga kirish so'rovini (request) yuborgan bo'lsa
    if user_id in PENDING_REQUEST_USERS:
        return True

    # 2. Agar foydalanuvchi allaqachon a'zo yoki admin bo'lsa
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logging.error(f"Kanal a'zoligini tekshirishda xato: {e}")

    return False


# ==================== CHAT JOIN REQUEST HANDLER ====================
# User kanal havolasini bosib "Request to join" qilganda avtomatik ushlaydi
# DIQQAT: Bot so'rovni qabul qilmaydi (approve qilmaydi), so'rov request bo'limida qolaveradi!
@dp.chat_join_request(F.chat.id == CHANNEL_ID)
async def handle_join_request(update: ChatJoinRequest):
    user_id = update.from_user.id
    PENDING_REQUEST_USERS.add(user_id)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "✅ <b>Kanalga so'rovingiz qabul qilindi!</b>\n\n"
                "Endi botdan to'liq foydalanishingiz mumkin. /start buyrug'ini bosing yoki xabar yozing."
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass


# ==================== MIDDLEWARE (HIMOYA FILTRI) ====================
# So'rov yubormagan userlarni boshqa hech qaysi handlerga o'tkazmaydi
class AccessCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # "Tekshirish" callback tugmasi tekshiruvdan to'siqsiz o'tishi kerak
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        user_id = user.id
        user_name = html.escape(user.full_name)

        # Ruxsatni tekshirish
        if not await has_access(user_id):
            text = (
                f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\n"
                f"⚠️ Botdan foydalanish uchun kanalimizga <b>qo'shilish so'rovi (request)</b> yuborishingiz kerak.\n\n"
                f"<i>Pastdagi tugma orqali havola ustiga bosing, 'Request to Join' tugmasini bosing va so'ng 'Tekshirish'ni bosing:</i>"
            )
            if isinstance(event, Message):
                await event.answer(text, reply_markup=get_subscription_keyboard(), parse_mode=ParseMode.HTML)
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Kanalga hali so'rov yubormagansiz!", show_alert=True)
            return

        return await handler(event, data)


# ==================== SO'ROV VA TEKSHIRISH HANDLERLARI ====================
@dp.callback_query(F.data == "check_subscription")
async def check_callback(query: CallbackQuery):
    user_id = query.from_user.id
    if await has_access(user_id):
        await query.message.delete()
        text = (
            "✅ <b>Rahmat!</b> So'rovingiz tasdiqlandi.\n\n"
            "Botdan bemalol foydalanishingiz mumkin! 🚀"
        )
        await query.message.answer(text, parse_mode=ParseMode.HTML)
    else:
        await query.answer(
            "❌ Siz hali kanalga so'rov tashlamadingiz! Avval havola orqali kanalga kirib so'rov yuboring.",
            show_alert=True
        )


# ==================== SIZNING ASOSIY 800 QATOR KODINGIZ ====================
# Sizdagi barcha /start, AI funksiyalari, tugmalar, videolar, inline modlar
# va boshqa handlerlaringiz aynan shu yerdan pastga joylashadi.
# Middleware ularning barchasini avtomatik himoya qiladi.

@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_name = html.escape(message.from_user.full_name)
    await message.answer(
        f"🎉 Xush kelibsiz, <b>{user_name}</b>!\n\n"
        f"Bot sizning xizmatingizda. Marhamat, buyruq yoki xabar yuboring! 🚀",
        parse_mode=ParseMode.HTML
    )

# Qolgan barcha handlerlaringiz shu yerda davom etadi...


# ==================== ISHGA TUSHIRISH (MAIN) ====================
async def main():
    # Middleware filtrlarni ro'yxatdan o'tkazamiz
    dp.message.middleware(AccessCheckMiddleware())
    dp.callback_query.middleware(AccessCheckMiddleware())

    # Eski webhook va navbatdagi xabarlarni tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)

    # Muhim: Telegram'dan 'chat_join_request' signallarini qabul qilishni yoqamiz
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_join_request"]
    )

if __name__ == "__main__":
    asyncio.run(main())
