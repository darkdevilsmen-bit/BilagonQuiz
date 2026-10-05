import asyncio
import datetime
import logging
import random
import sys
import os

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8963661833:AAHUEUDY9Rj9pNS9h8jh-RACpKH_LGtxgHY")

REQUIRED_CHANNEL = "@Auto_Captions"
CHANNEL_ID = -1004317372728
CHANNEL_LINK = "https://t.me/Auto_Captions"

ADMIN_USERNAME = "manmode_admin2"
# O'zingizning Telegram raqamli ID'ingizni yozing (masalan: 123456789)
ADMIN_ID = 0

dp = Dispatcher()

# Dastlabki soxta/haqiqiy baza
users_db = {
    1001: {"score": 156, "money": 450000, "withdrawn": 150000, "name": "Bekzod To'rayev", "referrals_count": 52, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
    1002: {"score": 141, "money": 400000, "withdrawn": 100000, "name": "Jasurbek Karimov", "referrals_count": 47, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
    1003: {"score": 120, "money": 350000, "withdrawn": 100000, "name": "Dilshod Olimov", "referrals_count": 40, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
}

for i in range(4, 25):
    users_db[1000 + i] = {
        "score": random.randint(10, 90),
        "money": random.randint(20000, 180000),
        "withdrawn": 0,
        "name": f"Ishtirokchi {i}",
        "referrals_count": random.randint(1, 15),
        "referred_users": [],
        "is_contestant": True,
        "last_quiz_time": None
    }

pending_referrals = {}
approved_users = set()
active_timers = {}


class WithdrawStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_card = State()


class ContestStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()


class BroadcastStates(StatesGroup):
    waiting_for_broadcast_message = State()


class AdminScoreStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_score_amount = State()


CATEGORIES_DB = {
    "logic": {
        "title": "🧠 Mantiqiy Fikrlash & Analitika (DTM)",
        "questions": [
            ("Ketma-ketlikdagi qonuniyatni aniqlang va keyingi sonni toping:\n2, 6, 12, 20, 30, 42, ?", 
             ["56", "54", "64", "48"], 0),
            ("Soat 15:40 bo'lganda soat va daqiqa millari orasidagi kichik burchak necha gradus bo'ladi?", 
             ["130°", "140°", "125°", "135°"], 0),
            ("Agar barcha A lar B bo'lsa va ayrim B lar C bo'lsa, qaysi xulosa mutlaqo to'g'ri?", 
             ["A va C o'rtasida qat'iy bog'liqlik mavjud emas", "Barcha A lar C dir", "Hech qanday A C emas", "Ba'zi A lar C dir"], 0),
            ("80 litr 25% li eritmadan 40% li eritma hosil qilish uchun qancha suv bug'latilishi kerak?", 
             ["30 litr", "25 litr", "20 litr", "35 litr"], 0),
            ("Bir poyezd 120 km/soat tezlikda 300 m lik tunneldan 15 sekundda o'tdi. Poyezd uzunligi qancha?", 
             ["200 m", "250 m", "150 m", "180 m"], 0),
            ("Hovuz 1-quvurdan 6 soatda, 2-quvurdan 8 soatda to'ladi, 3-quvurdan 12 soatda bo'shaydi. Uchtasi birgalikda ochilsa, necha soatda to'ladi?", 
             ["4.8 soat", "4 soat", "5.2 soat", "3.6 soat"], 0),
            ("Qutida 6 oq, 8 qora, 10 qizil shar bor. Tavakkal olingan 2 ta sharning ikkalasi ham qora bo'lish ehtimoli?", 
             ["7/69", "4/23", "2/15", "8/69"], 0),
            ("Kitob sahifalari 1 dan boshlab raqamlanganda 687 ta raqam ishlatilgan bo'lsa, kitob necha sahifali?", 
             ["265", "250", "280", "275"], 0),
            ("Agar 5 ta mushuk 5 ta sichqonni 5 minutda tutsa, 100 ta mushuk 100 ta sichqonni necha minutda tutadi?", 
             ["5 minut", "100 minut", "20 minut", "50 minut"], 0),
            ("Uch xonali sonning raqamlari yig'indisi 14 ga teng. O'nliklar xonasi birlikdan 2 barobar katta. Yuzliklar xonasi raqami o'nlikdan 1 ga kam. Bu qaysi son?", 
             ["563", "642", "743", "581"], 0)
        ]
    },
    "it": {
        "title": "💻 IT, Dasturlash & Algoritmlar",
        "questions": [
            ("QuickSort algoritmida eng yomon holatdagi (worst-case) asimptotik vaqt murakkabligi qanday?", 
             ["O(n²)", "O(n log n)", "O(n)", "O(log n)"], 0),
            ("IPv6 protokoli bo'yicha tarmoq manzillari necha bitdan iborat bo'ladi?", 
             ["128 bit", "64 bit", "32 bit", "256 bit"], 0),
            ("Relyatsion ma'lumotlar bazasida 3-Normal Forma (3NF) nimani istisno qiladi?", 
             ["Tranzitiv bog'liqlikni", "Qisman bog'liqlikni", "Birlamchi kalitni", "Bog'lanishsiz yozuvlarni"], 0),
            ("Python tilida bool('False') == False ifodasi qanday natija qaytaradi?", 
             ["False", "True", "TypeError", "None"], 0),
            ("OSI tarmoq modelining qaysi pog'onasi IP marshrutlash (routing) uchun javobgar?", 
             ["Tarmoq pog'onasi (Network)", "Kanal pog'onasi (Data Link)", "Transport pog'onasi", "Sessiya pog'onasi"], 0),
            ("Operatsion tizimlarda Deadlock sodir bo'lishining zaruriy shartlariga kirmaydigan omil qaysi?", 
             ["Majburiy resurs tortib olish (Preemption)", "O'zaro istisno (Mutual Exclusion)", "Ushlab turish va kutish", "Doiraviy kutish"], 0),
            ("Git tizimida git rebase ning git merge dan asosiy farqi nimada?", 
             ["Commitlar tarixini chiziqli ko'rinishga keltiradi", "Barcha o'zgarishlarni o'chiradi", "Faqat yangi branch yaratadi", "Fayllarni siqadi"], 0),
            ("B-Daraxti (B-Tree) ma'lumotlar tuzilmasi asosan qayerda samarali qo'llaniladi?", 
             ["Diskdagi katta hajmli indekslarda va DB larda", "Operativ xotirani kesh qilishda", "Matnlarni siqishda", "Faqat tarmoq marshrutida"], 0),
            ("TCP protokoli UDP dan farqli o'laroq nimani ta'minlaydi?", 
             ["Paketlar yetkazilishi kafolati va tartibini", "Tezroq videoshaffoflikni", "Faqat mahalliy ulanishni", "Faqat bir tomonlama aloqani"], 0),
            ("Asinxron dasturlashda Event Loop ning vazifasi nima?", 
             ["Kallback va I/O topshiriqlari navbatini boshqarish", "Kodni mashina tiliga o'girish", "Xotirani tozalash", "Shifrlash algoritmlarini yechish"], 0)
        ]
    },
    "history": {
        "title": "🏛 O'zbekiston & Jahon Tarixi (DTM)",
        "questions": [
            ("Amir Temur va Boyazid Yildirim o'rtasidagi Anqara jangi qachon sodir bo'lgan?", 
             ["1402-yil 20-iyul", "1395-yil 15-aprel", "1399-yil 12-sentyabr", "1405-yil 18-fevral"], 0),
            ("Qadimgi Baqtriya davlatining markaziy poytaxti qaysi shahar bo'lgan?", 
             ["Zariaspa (Baqtra)", "Marokanda", "Afrosiyob", "Dovon"], 0),
            ("Birinchi jahon urushini rasman yakunlagan Versal tinchlik shartnomasi qaysi yili imzolangan?", 
             ["1919-yil", "1918-yil", "1920-yil", "1921-yil"], 0),
            ("Qoraxoniylar davlatida Islom dini davlat dini sifatida qaysi hukmdor davrida e'lon qilingan?", 
             ["Sotuq Bug'roxon", "Nasr ibn Ali", "Ibrohim Bo'ritegin", "Yusuf Qodirxon"], 0),
            ("1868-yilgi Zirabuloq jangida qaysi ikki tomon qo'shinlari to'qnashgan?", 
             ["Rossiya imperiyasi va Buxoro amirligi", "Rossiya va Qo'qon xonligi", "Xiva xonligi va Eron", "Buxoro va Afg'oniston"], 0),
            ("Miloddan avvalgi 530-yilda To'maris qaysi Eron podshohini mag'lub etgan?", 
             ["Kir II", "Doro I", "Kserks", "Kambiz"], 0),
            ("Mirzo Ulug'bek Samarqand rasadxonasida osmon jismlarini kuzatish uchun o'rnatgan asosiy ulkan asbob nima?", 
             ["Sekstant (Kvadrant)", "Asturlob", "Optik teleskop", "Kompas"], 0),
            ("O'rta asr turkiy adabiyotining durdonasi hisoblangan 'Qutadg'u bilig' asari muallifi kim?", 
             ["Yusuf Xos Hojib", "Mahmud Qoshg'ariy", "Ahmad Yugnakiy", "Xo'ja Ahmad Yassaviy"], 0),
            ("Buxoro Xalq Sovet Respublikasi (BXSR) qachon tashkil etilgan?", 
             ["1920-yil oktyabr", "1917-yil noyabr", "1924-yil may", "1918-yil mart"], 0),
            ("O'zbekiston Respublikasining mustaqilligi qaysi anjumanda e'lon qilingan?", 
             ["Oliy Kengashning navbatdan tashqari sessiyasida", "Vazirlar Mahkamasida", "Umumxalq referendumida", "Markaziy Kengashda"], 0)
        ]
    }
}


def get_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎯 Viktorinani Boshlash")],
        [KeyboardButton(text="💳 Balans & Kabinet"), KeyboardButton(text="🎁 Kunlik Bonus")],
        [KeyboardButton(text="🏆 Top Reyting"), KeyboardButton(text="🔗 Do'stlarni Taklif Qilish")],
        [KeyboardButton(text="🎖 Katta Konkurs"), KeyboardButton(text="📜 Qoidalar va Shartlar")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    if user_id in approved_users:
        return True
    
    # Kanal obunasini xavfsiz tekshirish
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            approved_users.add(user_id)
            return True
    except Exception as e:
        logging.warning(f"Obunani tekshirishda xatolik (username bo'yicha): {e}")

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            approved_users.add(user_id)
            return True
    except Exception as e:
        logging.warning(f"Obunani tekshirishda xatolik (ID bo'yicha): {e}")

    # Agar bot kanalda admin bo'lmasa yoki xato chiqsa, foydalanuvchini bloklab qo'ymaslik uchun True qaytaramiz
    return True


async def process_referral_reward(bot: Bot, user_id: int, user_name: str):
    if user_id in pending_referrals:
        referrer_id = pending_referrals[user_id]
        if referrer_id in users_db and referrer_id != user_id:
            if not any(u.get("id") == user_id for u in users_db[referrer_id].get("referred_users", [])):
                users_db[referrer_id]["referred_users"].append({"id": user_id, "name": user_name})
                users_db[referrer_id]["referrals_count"] += 1
                users_db[referrer_id]["score"] += 3
                users_db[referrer_id]["money"] += 10000

                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 <b>Yangi taklif muvaffaqiyatli qo'shildi!</b>\n"
                        f"👤 Do'stingiz: <b>{html.escape(user_name)}</b>\n"
                        f"🎁 Sizga: <b>+3 Ball</b> va <b>+10,000 so'm</b> balansingizga qo'shildi!"
                    )
                except Exception:
                    pass
        pending_referrals.pop(user_id, None)


@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    user_id = request.from_user.id
    approved_users.add(user_id)
    await process_referral_reward(request.bot, user_id, request.from_user.full_name)


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name or "Foydalanuvchi"

    if user_id not in users_db:
        users_db[user_id] = {
            "score": 0, "money": 0, "withdrawn": 0, "question_num": 0,
            "game_questions": [], "referrals_count": 0, "referred_users": [],
            "last_bonus": None, "category": "logic", "name": user_name,
            "in_game": False, "is_contestant": False, "last_quiz_time": None
        }
    else:
        users_db[user_id]["name"] = user_name

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].split("_")[1])
            if ref_id != user_id and ref_id in users_db:
                pending_referrals[user_id] = ref_id
        except Exception:
            pass

    is_member = await check_user_subscription(message.bot, user_id)
    if not is_member:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="🔄 Obunani Tekshirish", callback_data="check_joined")]
        ])
        text = (
            f"👋 Assalomu alaykum, <b>{html.escape(user_name)}</b>!\n\n"
            f"Botdan to'liq foydalanish uchun rasmiy kanalimizga a'zo bo'ling:\n"
            f"👉 <b>{REQUIRED_CHANNEL}</b>"
        )
        await message.answer(text, reply_markup=keyboard)
        return

    await process_referral_reward(message.bot, user_id, user_name)

    welcome_text = (
        f"🌟 <b>Bilag'on Quiz Platformasiga Xush Kelibsiz!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Foydalanuvchi: <b>{html.escape(user_name)}</b>\n"
        f"💡 Qiyin DTM savollarini yeching, ball to'plang va pul mukofotlarini yutib oling!\n\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_reply_keyboard())


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or "Foydalanuvchi"

    approved_users.add(user_id)
    await callback.answer("✅ Obuna tasdiqlandi!")
    await process_referral_reward(callback.bot, user_id, user_name)

    try:
        await callback.message.delete()
    except Exception:
        pass

    welcome_text = (
        f"🌟 <b>Bilag'on Quiz Platformasiga Xush Kelibsiz!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await callback.message.answer(welcome_text, reply_markup=get_reply_keyboard())


# ------------------ VIKTORINA & 30 SEKUNDLIK TAYMER ------------------

@dp.message(F.text == "🎯 Viktorinani Boshlash")
async def quiz_category_selection(message: Message) -> None:
    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})

    if u_data.get("in_game", False):
        await message.answer("⚠️ Sizda hozir faol test davom etmoqda!")
        return

    last_time = u_data.get("last_quiz_time")
    if last_time:
        diff_hours = (datetime.datetime.now() - last_time).total_seconds() / 3600
        if diff_hours < 24:
            rem_h = int(24 - diff_hours)
            await message.answer(
                f"⏳ <b>Kunlik limit!</b>\n"
                f"Siz oxirgi testni topshirgansiz. Yangi urinish <b>{rem_h} soatdan</b> keyin ochiladi."
            )
            return

    keyboard = []
    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard.append([InlineKeyboardButton(text=cat_val["title"], callback_data=f"cat_{cat_key}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Bosh Menyu", callback_data="cancel_quiz")])

    text = (
        "📚 <b>DTM Test Yo'nalishini Tanlang:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏱ <b>Vaqt chegarasi:</b> Har bir savolga <b>30 soniya</b> beriladi!\n"
        "Barcha savollarni to'g'ri topsangiz qo'shimcha mukofot olasiz."
    )
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.callback_query(F.data.startswith("cat_"))
async def start_quiz_session(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    cat_key = callback.data.split("_")[1]

    if user_id not in users_db:
        users_db[user_id] = {
            "score": 0, "money": 0, "withdrawn": 0, "question_num": 0,
            "game_questions": [], "referrals_count": 0, "referred_users": [],
            "last_bonus": None, "name": callback.from_user.full_name,
            "in_game": False, "is_contestant": False, "last_quiz_time": None
        }

    questions_pool = CATEGORIES_DB[cat_key]["questions"]
    selected_questions = random.sample(questions_pool, min(len(questions_pool), 10))

    users_db[user_id]["game_questions"] = selected_questions
    users_db[user_id]["question_num"] = 0
    users_db[user_id]["correct_count"] = 0
    users_db[user_id]["in_game"] = True
    users_db[user_id]["category"] = cat_key

    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_quiz_step(callback.bot, callback.message.chat.id, user_id)


async def quiz_timer_countdown(bot: Bot, chat_id: int, user_id: int, question_index: int, msg_id: int):
    try:
        await asyncio.sleep(30)
        u_data = users_db.get(user_id)
        if not u_data or not u_data.get("in_game", False):
            return

        if u_data.get("question_num") == question_index:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text="⌛️ <b>Vaqt tugadi!</b> (30 soniya ichida javob berilmadi ❌)"
                )
            except Exception:
                pass
            
            u_data["question_num"] += 1
            await send_quiz_step(bot, chat_id, user_id)
    except asyncio.CancelledError:
        pass


async def send_quiz_step(bot: Bot, chat_id: int, user_id: int):
    if user_id in active_timers and not active_timers[user_id].done():
        active_timers[user_id].cancel()

    u_data = users_db.get(user_id)
    q_idx = u_data["question_num"]
    questions = u_data["game_questions"]

    if q_idx >= len(questions):
        u_data["in_game"] = False
        u_data["last_quiz_time"] = datetime.datetime.now()
        corrects = u_data.get("correct_count", 0)

        if corrects >= 10:
            u_data["score"] += 5
            u_data["money"] += 15000
            res_text = (
                f"🎉 <b>MUKAMMAL NATIJA!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Barcha 10 ta savolga to'g'ri javob berdingiz!\n"
                f"🎁 Mukofot: <b>+5 Ball</b> va <b>+15,000 so'm</b> hisobingizga qo'shildi!"
            )
        else:
            res_text = (
                f"🏁 <b>Test Yakunlandi!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 To'g'ri javoblar: <b>{corrects} / 10</b>\n"
                f"💡 Qo'shimcha 5 ball va 15,000 so'm olish uchun barcha savollarni to'g'ri yechish lozim."
            )
        await bot.send_message(chat_id, res_text, reply_markup=get_reply_keyboard())
        return

    q_text, options, correct_opt = questions[q_idx]

    total_q = len(questions)
    filled_blocks = int(((q_idx + 1) / total_q) * 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

    keyboard_buttons = []
    option_letters = ["A", "B", "C", "D"]
    for idx, opt in enumerate(options):
        letter = option_letters[idx] if idx < len(option_letters) else f"{idx+1}"
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{letter}) {opt}", callback_data=f"ans_{idx}_{correct_opt}_{q_idx}")
        ])

    keyboard_buttons.append([InlineKeyboardButton(text="🛑 Testdan Chiqish", callback_data="cancel_quiz")])

    msg_body = (
        f"📝 <b>Savol {q_idx + 1} / {total_q}</b>\n"
        f"Progress: [{bar}]\n"
        f"⏱ <b>Qolgan vaqt: 30 soniya</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{q_text}</b>"
    )

    sent_msg = await bot.send_message(chat_id, msg_body, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))

    timer_task = asyncio.create_task(quiz_timer_countdown(bot, chat_id, user_id, q_idx, sent_msg.message_id))
    active_timers[user_id] = timer_task


@dp.callback_query(F.data.startswith("ans_"))
async def handle_user_answer(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db or not users_db[user_id].get("in_game", False):
        await callback.answer("⚠️ Faol test topilmadi!", show_alert=True)
        return

    parts = callback.data.split("_")
    chosen_idx = int(parts[1])
    correct_idx = int(parts[2])
    q_idx = int(parts[3])

    if users_db[user_id].get("question_num") != q_idx:
        await callback.answer("⚠️ Bu savolning vaqti o'tib ketgan!")
        return

    if user_id in active_timers and not active_timers[user_id].done():
        active_timers[user_id].cancel()

    if chosen_idx == correct_idx:
        users_db[user_id]["correct_count"] = users_db[user_id].get("correct_count", 0) + 1
        await callback.answer("✅ To'g'ri!", show_alert=False)
    else:
        await callback.answer("❌ Noto'g'ri!", show_alert=False)

    users_db[user_id]["question_num"] += 1

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_quiz_step(callback.bot, callback.message.chat.id, user_id)


@dp.callback_query(F.data == "cancel_quiz")
async def cancel_quiz_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id in active_timers and not active_timers[user_id].done():
        active_timers[user_id].cancel()

    if user_id in users_db:
        users_db[user_id]["in_game"] = False

    await callback.answer("Amal bekor qilindi.")
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer("🏠 Asosiy menyudasiz:", reply_markup=get_reply_keyboard())


# ------------------ BALANS & KABINET ------------------

@dp.message(F.text == "💳 Balans & Kabinet")
async def show_user_profile(message: Message) -> None:
    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})

    score = u_data.get("score", 0)
    money = u_data.get("money", 0)
    withdrawn = u_data.get("withdrawn", 0)
    refs = u_data.get("referrals_count", 0)

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        f"💎 <b>Shaxsiy Kabinet & Moliyaviy Holat</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID raqam: <code>{user_id}</code>\n"
        f"👤 Foydalanuvchi: <b>{html.escape(u_data.get('name', 'Ishtirokchi'))}</b>\n"
        f"👥 Taklif qilgan do'stlar: <b>{refs} ta</b>\n"
        f"🏆 Jami to'plangan ball: <b>{score} ball</b>\n"
        f"💰 Asosiy hisob: <b>{money:,} so'm</b>\n"
        f"💸 Yechib olingan jami: <b>{withdrawn:,} so'm</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Pulni Yechib Olish", callback_data="withdraw_funds")],
        [InlineKeyboardButton(text="🔙 Orqaga Qaytish", callback_data="cancel_quiz")]
    ])
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "withdraw_funds")
async def start_withdrawal_flow(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    u_data = users_db.get(user_id, {})
    score = u_data.get("score", 0)
    money = u_data.get("money", 0)

    if score < 50 or money <= 0:
        needed = max(0, 50 - score)
        text = (
            f"🚫 <b>Pul yechish imkonsiz!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Minimal talab: <b>50 ball</b> va hisobda mablag' bo'lishi kerak.\n"
            f"📊 Sizning ballingiz: <b>{score} ball</b> (Yana {needed} ball kerak)\n"
            f"💰 Balansingiz: <b>{money:,} so'm</b>"
        )
        await callback.answer("Ball yetarli emas!", show_alert=True)
        await callback.message.answer(text)
        return

    await callback.answer()
    await state.set_state(WithdrawStates.waiting_for_name)
    await callback.message.answer("📝 Pulni o'tkazish uchun <b>Ism va Familiyangizni</b> kiriting:")


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(message: Message, state: FSMContext) -> None:
    await state.update_data(user_fullname=message.text.strip())
    await state.set_state(WithdrawStates.waiting_for_card)
    await message.answer("💳 16 xonali <b>Karta raqamingizni</b> kiriting:")


@dp.message(WithdrawStates.waiting_for_card)
async def process_withdraw_card(message: Message, state: FSMContext) -> None:
    card_info = message.text.strip().replace(" ", "")
    user_id = message.from_user.id
    data = await state.get_data()
    fullname = data.get("user_fullname")

    money = users_db.get(user_id, {}).get("money", 0)
    users_db[user_id]["withdrawn"] = users_db[user_id].get("withdrawn", 0) + money
    users_db[user_id]["money"] = 0
    users_db[user_id]["score"] = 0

    await state.clear()

    admin_notification = (
        f"🚨 <b>Yangi Pul Yechish So'rovi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📝 F.I.SH: <b>{fullname}</b>\n"
        f"💳 Karta: <code>{card_info}</code>\n"
        f"💰 Summa: <b>{money:,} so'm</b>"
    )

    if ADMIN_ID != 0:
        try:
            await message.bot.send_message(ADMIN_ID, admin_notification)
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xatolik: {e}")

    await message.answer(
        f"✅ <b>So'rovingiz qabul qilindi!</b>\n"
        f"Mablag' (<b>{money:,} so'm</b>) tez orada kartangizga o'tkaziladi.",
        reply_markup=get_reply_keyboard()
    )


# ------------------ BONUS & KONKURS ------------------

@dp.message(F.text == "🎁 Kunlik Bonus")
async def claim_daily_bonus(message: Message) -> None:
    user_id = message.from_user.id
    now = datetime.datetime.now()
    last_bonus = users_db.get(user_id, {}).get("last_bonus")

    if last_bonus and (now - last_bonus).total_seconds() < 86400:
        rem_sec = 86400 - (now - last_bonus).total_seconds()
        rem_h = int(rem_sec // 3600)
        await message.answer(f"⏳ Kunlik bonus olingan! Keyingisi <b>{rem_h} soatdan</b> so'ng beriladi.")
        return

    b_score = random.randint(1, 3)
    b_money = b_score * 3000
    users_db[user_id]["score"] = users_db[user_id].get("score", 0) + b_score
    users_db[user_id]["money"] = users_db[user_id].get("money", 0) + b_money
    users_db[user_id]["last_bonus"] = now

    await message.answer(
        f"🎉 <b>Kunlik Sovg'angiz:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Ball: <b>+{b_score} ball</b>\n"
        f"💰 Balans: <b>+{b_money:,} so'm</b>"
    )


@dp.message(F.text == "🔗 Do'stlarni Taklif Qilish")
async def referral_program_info(message: Message) -> None:
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    u_data = users_db.get(user_id, {})
    refs = u_data.get("referrals_count", 0)

    text = (
        f"👥 <b>Do'stlarni Taklif Qilish Tizimi</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Har bir taklif qilingan faol a'zo uchun:\n"
        f"🎁 <b>+3 Ball</b> va <b>+10,000 so'm</b>!\n\n"
        f"📊 Sizning referallaringiz: <b>{refs} ta</b>\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )
    await message.answer(text)


@dp.message(F.text == "🏆 Top Reyting")
async def show_leaderboard(message: Message) -> None:
    sorted_users = sorted(
        users_db.values(),
        key=lambda x: (x.get("score", 0), x.get("money", 0)),
        reverse=True
    )[:10]

    board = "🏆 <b>Top-10 Liderlar Jadvali</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, u in enumerate(sorted_users, 1):
        name = u.get("name", "Ishtirokchi")
        score = u.get("score", 0)
        money = u.get("money", 0)
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        board += f"{medal} <b>{html.escape(name)}</b>\n   └ Ball: <b>{score}</b> | Balans: <b>{money:,} so'm</b>\n\n"

    await message.answer(board)


@dp.message(F.text == "🎖 Katta Konkurs")
async def contest_screen(message: Message) -> None:
    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})
    is_contestant = u_data.get("is_contestant", False)

    contestants = sorted(
        [u for u in users_db.values() if u.get("is_contestant", False)],
        key=lambda x: x.get("referrals_count", 0),
        reverse=True
    )

    top_name = contestants[0].get("name", "—") if contestants else "—"
    top_refs = contestants[0].get("referrals_count", 0) if contestants else 0

    text = (
        f"🎖 <b>Katta Pul Mukofoti Konkursi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Mukofot jamg'armasi: <b>500,000 so'm naqd pul!</b>\n"
        f"📌 Shart: Eng ko'p referal to'plagan 1-o'rin sohibi mukofotni yutib oladi.\n\n"
        f"🥇 1-o'rindagi ishtirokchi: <b>{top_name}</b> ({top_refs} ta taklif)\n"
    )

    keyboard_btns = []
    if not is_contestant:
        text += "\n❌ <i>Siz hali konkursda ro'yxatdan o'tmadingiz!</i>"
        keyboard_btns.append([InlineKeyboardButton(text="✍️ Konkursga Ro'yxatdan O'tish", callback_data="register_contest")])
    else:
        rank = 1
        for idx, c in enumerate(contestants, 1):
            if c.get("name") == u_data.get("name"):
                rank = idx
                break
        text += f"\n✅ Siz konkurs a'zosisiz! O'rningiz: <b>{rank}-o'rin</b>"

    keyboard_btns.append([InlineKeyboardButton(text="🔙 Bosh Menyu", callback_data="cancel_quiz")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_btns))


@dp.callback_query(F.data == "register_contest")
async def register_contest_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ContestStates.waiting_for_name)
    await callback.message.answer("1️⃣ Konkurs uchun <b>Ismingizni</b> yozing:")


@dp.message(ContestStates.waiting_for_name)
async def contest_step_name(message: Message, state: FSMContext) -> None:
    await state.update_data(c_name=message.text.strip())
    await state.set_state(ContestStates.waiting_for_surname)
    await message.answer("2️⃣ Endi <b>Familiyangizni</b> kiriting:")


@dp.message(ContestStates.waiting_for_surname)
async def contest_step_surname(message: Message, state: FSMContext) -> None:
    surname = message.text.strip()
    data = await state.get_data()
    full_name = f"{data.get('c_name')} {surname}"

    user_id = message.from_user.id
    users_db[user_id]["name"] = full_name
    users_db[user_id]["is_contestant"] = True

    await state.clear()
    await message.answer(
        f"🎉 <b>Tabriklaymiz, {full_name}!</b>\nSiz konkurs a'zosisiz!",
        reply_markup=get_reply_keyboard()
    )


@dp.message(F.text == "📜 Qoidalar va Shartlar")
async def show_rules_handler(message: Message) -> None:
    rules = (
        "📜 <b>Loyihaning Asosiy Qoidalari:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. <b>Vaqt:</b> Har bir savolga roppa-rosa 30 soniya beriladi.\n"
        "2. <b>Bonus:</b> 10 ta savolning barchasiga to'g'ri javob berilsa, +5 ball va +15,000 so'm beriladi.\n"
        "3. <b>Referal:</b> Taklif qilingan har bir yangi do'st uchun +3 ball va +10,000 so'm hisobga o'tadi.\n"
        "4. <b>Mablag' yechish:</b> Pul yechish uchun kamida 50 ball to'plash lozim."
    )
    await message.answer(rules)


# ------------------ ADMIN PANEL ------------------

@dp.message(Command("admin"))
async def admin_dashboard(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    is_admin = (ADMIN_ID != 0 and user_id == ADMIN_ID) or (
        ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower()
    )

    if not is_admin:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="adm_broadcast")]
    ])
    await message.answer("⚙️ <b>Admin boshqaruv paneli:</b>", reply_markup=keyboard)


@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)
    await callback.message.answer("📝 Yubormoqchi bo'lgan xabaringizni kiriting:")


@dp.message(BroadcastStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    sent_count = 0
    status_msg = await message.answer("🚀 Xabar yuborilmoqda...")

    for uid in list(users_db.keys()):
        if uid < 10000:
            continue
        try:
            await message.send_copy(chat_id=uid)
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass

    await status_msg.edit_text(f"✅ Xabar {sent_count} ta foydalanuvchiga yuborildi.")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)

    # 1. Hamma oddiy foydalanuvchilar uchun faqat /start buyrug'ini ko'rsatamiz
    await bot.set_my_commands(
        [BotCommand(command="start", description="Bosh menyuni ochish")],
        scope=BotCommandScopeDefault()
    )

    # 2. Agar ADMIN_ID kiritilgan bo'lsa, faqat adminning o'zida /admin menyusi ko'rinadi
    if ADMIN_ID != 0:
        try:
            await bot.set_my_commands(
                [
                    BotCommand(command="start", description="Bosh menyuni ochish"),
                    BotCommand(command="admin", description="Admin panelini ochish")
                ],
                scope=BotCommandScopeChat(chat_id=ADMIN_ID)
            )
        except Exception as e:
            logging.warning(f"Admin buyruqlarini sozlashda xatolik: {e}")

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
