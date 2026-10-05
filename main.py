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
    BotCommand
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8963661833:AAHUEUDY9Rj9pNS9h8jh-RACpKH_LGtxgHY")

REQUIRED_CHANNEL = "@Auto_Captions"
CHANNEL_ID = -1004317372728
CHANNEL_LINK = "https://t.me/Auto_Captions"

ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 0  # O'zingizning Telegram raqamli ID raqamingizni kiriting

dp = Dispatcher()

# Dastlabki ma'lumotlar bazasi
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

# Taymer vazifalari uchun xotira
quiz_timers = {}


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


# Murakkablashtirilgan DTM testlar bazasi
CATEGORIES_DB = {
    "logic": {
        "title": "🧠 Mantiq & Analitika (DTM)",
        "questions": [
            ("Agar barcha A lar B bo'lsa va ba'zi B lar C bo'lsa, qaysi xulosa qat'iy mantiqiy to'g'ri?", 
             ["Barcha A lar C dir", "Hech qanday A C emas", "A va C o'rtasida qat'iy bog'liqlik kafolatlanmagan", "Ba'zi A lar qat'iyan C dir"], 2),
            ("Ketma-ketlikning keyingi sonini toping: 2, 6, 12, 20, 30, 42, ?", 
             ["56", "54", "64", "48"], 0),
            ("Bir poyezd 120 km/soat tezlik bilan harakatlanib, 300 m uzunlikdagi tunneldan 15 sekundda to'liq o'tdi. Poyezdning uzunligi necha metr?", 
             ["200 m", "250 m", "150 m", "300 m"], 0),
            ("Soat 15:40 bo'lganda soat va daqiqa millari orasidagi kichik burchak necha gradus bo'ladi?", 
             ["130°", "140°", "125°", "135°"], 0),
            ("Kriptografik qonuniyat: AGAR = 17118 bo'lsa, DTM = ?", 
             ["42013", "41913", "42014", "31912"], 0),
            ("Idishda 80 litr 25% li tuz eritmasi bor. Tuz konsentratsiyasini 40% ga yetkazish uchun qancha suv bug'latilishi kerak?", 
             ["30 litr", "25 litr", "20 litr", "35 litr"], 0),
            ("Hovuz birinchi quvur orqali 6 soatda, ikkinchisi orqali 8 soatda to'ladi. Uchinchi quvur to'la hovuzni 12 soatda bo'shatadi. Uchtasi birga ochilsa, hovuz necha soatda to'ladi?", 
             ["4.8 soat", "4 soat", "5.2 soat", "3.6 soat"], 0),
            ("Uch xonali sonning raqamlari yig'indisi 14 ga teng. O'nliklar xonasi birlikdan 2 barobar katta. Yuzliklar xonasi raqami o'nlikdan 1 ga kam. Bu son qaysi?", 
             ["563", "642", "743", "581"], 0),
            ("Bir kishi har kuni oldingi kundagiga qaraganda 2 barobar ko'p sahifa kitob o'qiydi. 6 kunda kitob tugadi. U 4-kuni kitobning qancha qismini o'qigan?", 
             ["8/63", "16/63", "4/31", "1/8"], 0),
            ("Qutida 6 ta oq, 8 ta qora va 10 ta qizil shar bor. Tavakkaliga olingan 2 ta sharning ikkalasi ham qora bo'lishi ehtimolini toping.", 
             ["7/69", "4/23", "2/15", "8/69"], 0)
        ]
    },
    "it": {
        "title": "💻 IT, Dasturlash & Algoritmlar",
        "questions": [
            ("QuickSort algoritmida eng yomon holatdagi (worst-case) vaqt murakkabligi (Time Complexity) qanday?", 
             ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], 1),
            ("IPv6 protokoli bo'yicha tarmoq manzillari necha bitdan iborat bo'ladi?", 
             ["32 bit", "64 bit", "128 bit", "256 bit"], 2),
            ("Relyatsion ma'lumotlar bazasida 3-Normal Forma (3NF) talabiga ko'ra jadvalda nima bo'lmasligi kerak?", 
             ["Qisman bog'liqlik", "Tranzitiv bog'liqlik", "Birlamchi kalit", "Indekslar"], 1),
            ("Python'da quyidagi kod natijasi nima bo'ladi: `bool('False') == False`?", 
             ["True", "False", "TypeError", "None"], 1),
            ("OSI tarmoq modelining qaysi pog'onasida marshrutizatorlar (Router) va IP protokoli ishlaydi?", 
             ["Transport pog'onasi", "Tarmoq pog'onasi (Network)", "Kanal pog'onasi (Data Link)", "Sessiya pog'onasi"], 1),
            ("Dasturlashda 'Deadlock' yuzaga kelishi uchun quyidagilardan qaysi biri zaruriy shart hisoblanmaydi?", 
             ["O'zaro istisno (Mutual Exclusion)", "Ushlab turish va kutish", "Preyempsiya mavjudligi (Majburiy resurs tortib olish)", "Doiraviy kutish"], 2),
            ("TCP va UDP protokollari o'rtasidagi eng muhim farq nima?", 
             ["TCP ulanishsiz ishlaydi", "TCP ma'lumot yetkazilishini kafolatlaydi, UDP esa yo'q", "UDP faqat shifrlangan paket uzatadi", "TCP faqat lokal tarmoqda ishlaydi"], 1),
            ("Git tizimida `git rebase` va `git merge` komandalarining asosiy farqi nimada?", 
             ["Rebase tarixni chiziqli ko'rinishga keltiradi, merge esa qo'shilish nuqtasi yaratadi", "Rebase barcha commitlarni o'chirib tashlaydi", "Merge yangi branch yaratadi", "Farqi yo'q"], 0),
            ("Asinxron dasturlashda 'Event Loop' ning asosiy vazifasi nima?", 
             ["Kodni kompilyatsiya qilish", "Kallback va I/O topshiriqlarini navbat bilan rejalashtirish va chaqirish", "Xotirani tozalash (GC)", "Fayllarni shifrlash"], 1),
            ("B-Daraxti (B-Tree) qidiruv strukturasining asosiy maqsadi nimada?", 
             ["Operativ xotirani tejash", "Diskdagi katta hajmli ma'lumotlarda o'qish/yozish amallarini kamaytirish", "Faqat satrlarni saralash", "Graflarni tahlil qilish"], 1)
        ]
    },
    "history": {
        "title": "🏛 O'zbekiston & Jahon Tarixi (DTM)",
        "questions": [
            ("Amir Temur va Boyazid Yildirim o'rtasidagi mashhur Anqara jangi qaysi yili bo'lib o'tgan?", 
             ["1402-yil 20-iyul", "1395-yil 15-aprel", "1399-yil 12-sentyabr", "1405-yil 18-fevral"], 0),
            ("Qadimgi Baqtriya davlatining poytaxti qaysi shahar bo'lgan?", 
             ["Zariaspa (Baqtra)", "Marokanda", "Afrosiyob", "Dovon"], 0),
            ("O'zbekiston hududida ilk konstitutsiyaviy monarxiya va jadidlar harakati faollashgan Buxoro Xalq Sovet Respublikasi qachon tuzilgan?", 
             ["1920-yil oktyabr", "1917-yil noyabr", "1924-yil may", "1918-yil mart"], 0),
            ("Birinchi jahon urushini rasman yakunlagan Versal tinchlik shartnomasi qaysi yilda imzolangan?", 
             ["1919-yil", "1918-yil", "1921-yil", "1917-yil"], 0),
            ("Qoraxoniylar davlatida Islom dini davlat dini sifatida qaysi hukmdor davrida qabul qilingan?", 
             ["Sotuq Bug'roxon", "Nasr ibn Ali", "Ibrohim Bo'ritegin", "Yusuf Qodirxon"], 0),
            ("1868-yilgi Zirabuloq jangida qaysi ikki tomon to'qnashgan?", 
             ["Rossiya imperiyasi va Buxoro amirligi", "Qo'qon xonligi va Rossiya", "Xiva xonligi va Eron", "Buxoro va Afg'oniston"], 0),
            ("Miloddan avvalgi 530-yilda massagetlar malikasi To'maris qaysi Eron shohini mag'lub etgan?", 
             ["Kir II", "Doro I", "Kserks", "Kambiz II"], 0),
            ("Mirzo Ulug'bek tomonidan barpo etilgan Samarqand rasadxonasining asosiy asbobi nima deb atalgan?", 
             ["Sekstant (Kvadrant)", "Asturlob", "Teleskop", "Kompas"], 0),
            ("O'rta asrlarda yozilgan 'Qutadg'u bilig' asari muallifi kim?", 
             ["Yusuf Xos Hojib", "Mahmud Qoshg'ariy", "Ahmad Yugnakiy", "Xoja Ahmad Yassaviy"], 0),
            ("1991-yil 31-avgustda O'zbekiston Respublikasining davlat mustaqilligi qaysi anjumanda e'lon qilingan?", 
             ["Oliy Kengashning navbatdan tashqari sessiyasida", "Vazirlar Mahkamasi majlisida", "Referendumda", "Markaziy Komite plenumida"], 0)
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
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            approved_users.add(user_id)
            return True
    except Exception:
        pass

    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            approved_users.add(user_id)
            return True
    except Exception:
        pass

    return False


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
                        f"🎁 Sizga: <b>+3 Ball</b> va <b>+10,000 so'm</b> hisobingizga o'tkazildi!"
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
    user_name = message.from_user.full_name

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
            f"Botimizdan to'liq foydalanish va konkursda ishtirok etish uchun "
            f"rasmiy kanalimizga a'zo bo'ling:\n\n"
            f"👉 <b>{REQUIRED_CHANNEL}</b>"
        )
        await message.answer(text, reply_markup=keyboard)
        return

    await process_referral_reward(message.bot, user_id, user_name)

    welcome_text = (
        f"🌟 <b>Bilag'on Quiz Platformasiga Xush Kelibsiz!</b>\n"
        f"────────────────────────\n"
        f"👤 Foydalanuvchi: <b>{html.escape(user_name)}</b>\n"
        f"💡 Qiyin DTM savollarini yeching, ball to'plang va pul mukofotlarini yutib oling!\n\n"
        f"👇 Kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_reply_keyboard())


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name

    if not await check_user_subscription(callback.bot, user_id):
        await callback.answer("❌ Siz hali kanalga a'zo emassiz!", show_alert=True)
        return

    approved_users.add(user_id)
    await callback.answer("✅ Obuna tasdiqlandi!")
    await process_referral_reward(callback.bot, user_id, user_name)

    try:
        await callback.message.delete()
    except Exception:
        pass

    welcome_text = (
        f"🌟 <b>Bilag'on Quiz Platformasiga Xush Kelibsiz!</b>\n"
        f"────────────────────────\n"
        f"👤 Foydalanuvchi: <b>{html.escape(user_name)}</b>\n\n"
        f"Pastdagi menyudan xizmatingizni tanlang:"
    )
    await callback.message.answer(welcome_text, reply_markup=get_reply_keyboard())


async def verify_access(message: Message) -> bool:
    user_id = message.from_user.id
    if not await check_user_subscription(message.bot, user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="🔄 Obunani Tekshirish", callback_data="check_joined")]
        ])
        await message.answer("⚠️ Botdan foydalanish uchun rasmiy kanalga obuna bo'lish shart!", reply_markup=keyboard)
        return False
    return True


# ------------------ VIKTORINA VA TAYMER TIZIMI ------------------

@dp.message(F.text == "🎯 Viktorinani Boshlash")
async def quiz_category_selection(message: Message) -> None:
    if not await verify_access(message):
        return

    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})

    if u_data.get("in_game", False):
        await message.answer("⚠️ Sizda tugatilmagan viktorina mavjud! Davom ettiring yoki bekor qiling.")
        return

    last_time = u_data.get("last_quiz_time")
    if last_time:
        diff_hours = (datetime.datetime.now() - last_time).total_seconds() / 3600
        if diff_hours < 24:
            rem_h = int(24 - diff_hours)
            await message.answer(
                f"⏳ <b>Kunlik limit!</b>\n"
                f"Siz so'nggi 24 soat ichida test ishlagansiz.\n"
                f"Qayta kirish uchun <b>{rem_h} soat</b> kutishingiz yoki 3 ta do'stingizni taklif qilishingiz kerak."
            )
            return

    keyboard = []
    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard.append([InlineKeyboardButton(text=cat_val["title"], callback_data=f"cat_{cat_key}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Asosiy Menyu", callback_data="cancel_quiz")])

    text = (
        "📚 <b>DTM Standartidagi Fan Yo'nalishini Tanlang:</b>\n"
        "────────────────────────\n"
        "⏱ <b>Diqqat:</b> Har bir savolga roppa-rosa <b>30 soniya</b> vaqt beriladi!\n"
        "Agar vaqt tugasa, savol o'tkazib yuboriladi."
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


async def quiz_timer_countdown(bot: Bot, chat_id: int, user_id: int, current_q_idx: int):
    try:
        await asyncio.sleep(30)
        u_data = users_db.get(user_id)
        if not u_data or not u_data.get("in_game", False):
            return

        if u_data.get("question_num") == current_q_idx:
            await bot.send_message(chat_id, "⌛️ <b>Vaqt tugadi!</b> 30 soniya ichida javob berilmadi.")
            u_data["question_num"] += 1
            await send_quiz_step(bot, chat_id, user_id)
    except asyncio.CancelledError:
        pass


async def send_quiz_step(bot: Bot, chat_id: int, user_id: int):
    # Oldingi taymerni to'xtatish
    if user_id in quiz_timers and not quiz_timers[user_id].done():
        quiz_timers[user_id].cancel()

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
                f"🏆 <b>AQL BOVAR QILMAS NATIJA!</b>\n"
                f"────────────────────────\n"
                f"🎯 Siz barcha 10 ta murakkab DTM savoliga to'g'ri javob berdingiz!\n"
                f"🎁 Mukofot: <b>+5 Ball</b> va <b>+15,000 so'm</b> balansingizga qo'shildi! 🚀"
            )
        else:
            res_text = (
                f"🏁 <b>Test Yakunlandi!</b>\n"
                f"────────────────────────\n"
                f"📊 To'g'ri javoblar: <b>{corrects} / 10</b>\n"
                f"💡 Qo'shimcha 5 ball va 15,000 so'm yutib olish uchun barcha 10 ta savolni to'g'ri yechishingiz lozim."
            )
        await bot.send_message(chat_id, res_text, reply_markup=get_reply_keyboard())
        return

    q_text, options, correct_opt = questions[q_idx]

    # Progress bar yaratish
    total_q = len(questions)
    filled_blocks = int(((q_idx + 1) / total_q) * 10)
    bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

    keyboard_buttons = []
    option_letters = ["A", "B", "C", "D"]
    for idx, opt in enumerate(options):
        letter = option_letters[idx] if idx < 4 else f"{idx+1}"
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"{letter}) {opt}", callback_data=f"ans_{idx}_{correct_opt}_{q_idx}")
        ])

    keyboard_buttons.append([InlineKeyboardButton(text="🛑 Testni Bekor Qilish", callback_data="cancel_quiz")])

    msg_body = (
        f"📋 <b>Savol {q_idx + 1} / {total_q}</b>\n"
        f"📊 Progress: [{bar}]\n"
        f"⏱ <b>Vaqt: 30 soniya</b>\n"
        f"────────────────────────\n\n"
        f"<b>{q_text}</b>"
    )

    sent_msg = await bot.send_message(chat_id, msg_body, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))

    # 30 soniyalik taymerni boshlash
    timer_task = asyncio.create_task(quiz_timer_countdown(bot, chat_id, user_id, q_idx))
    quiz_timers[user_id] = timer_task


@dp.callback_query(F.data.startswith("ans_"))
async def handle_user_answer(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db or not users_db[user_id].get("in_game", False):
        await callback.answer("⚠️ Faol test sessiyasi mavjud emas!", show_alert=True)
        return

    parts = callback.data.split("_")
    chosen_idx = int(parts[1])
    correct_idx = int(parts[2])
    q_idx = int(parts[3])

    if users_db[user_id].get("question_num") != q_idx:
        await callback.answer("⚠️ Bu savol muddati o'tib ketgan!")
        return

    # Taymerni to'xtatish
    if user_id in quiz_timers and not quiz_timers[user_id].done():
        quiz_timers[user_id].cancel()

    if chosen_idx == correct_idx:
        users_db[user_id]["correct_count"] = users_db[user_id].get("correct_count", 0) + 1
        await callback.answer("✅ To'g'ri javob!", show_alert=False)
    else:
        await callback.answer("❌ Noto'g'ri javob!", show_alert=False)

    users_db[user_id]["question_num"] += 1

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_quiz_step(callback.bot, callback.message.chat.id, user_id)


@dp.callback_query(F.data == "cancel_quiz")
async def cancel_quiz_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id in quiz_timers and not quiz_timers[user_id].done():
        quiz_timers[user_id].cancel()

    if user_id in users_db:
        users_db[user_id]["in_game"] = False

    await callback.answer("Test bekor qilindi.")
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer("🏠 Asosiy menyudasiz:", reply_markup=get_reply_keyboard())


# ------------------ BALANS VA FOYDALANUVCHI KABINETI ------------------

@dp.message(F.text == "💳 Balans & Kabinet")
async def show_user_profile(message: Message) -> None:
    if not await verify_access(message):
        return

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
        f"────────────────────────\n"
        f"🆔 ID raqam: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{html.escape(u_data.get('name', 'Foydalanuvchi'))}</b>\n"
        f"👥 Taklif etilgan do'stlar: <b>{refs} ta</b>\n"
        f"🏆 Jami to'plangan ball: <b>{score} ball</b>\n"
        f"💰 Asosiy hisob: <b>{money:,} so'm</b>\n"
        f"💸 Yechib olingan jami pul: <b>{withdrawn:,} so'm</b>\n"
        f"────────────────────────\n"
        f"🔗 <b>Sizning shaxsiy referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n"
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
            f"🚫 <b>Mablag' yechish imkonsiz!</b>\n"
            f"────────────────────────\n"
            f"📌 Minimal talab: <b>50 ball</b> va balansda mablag' bo'lishi kerak.\n"
            f"📊 Sizning ballingiz: <b>{score} ball</b> (Yana {needed} ball zarur)\n"
            f"💰 Hozirgi balansingiz: <b>{money:,} so'm</b>"
        )
        await callback.answer("Ball yetarli emas!", show_alert=True)
        await callback.message.answer(text)
        return

    await callback.answer()
    await state.set_state(WithdrawStates.waiting_for_name)
    await callback.message.answer(
        "📝 Pulni o'tkazish uchun <b>Ism va Familiyangizni</b> to'liq yozib yuboring:\n"
        "(Masalan: <i>Alijon Valiyev</i>)"
    )


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(user_fullname=name)
    await state.set_state(WithdrawStates.waiting_for_card)
    await message.answer("💳 Endi 16 xonali <b>Plastik karta raqamingizni</b> (UzCard/Humo) yuboring:")


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

    # Adminga yuborish
    admin_notification = (
        f"🚨 <b>Yangi Pul Yechish So'rovi!</b>\n"
        f"────────────────────────\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📝 F.I.SH: <b>{fullname}</b>\n"
        f"💳 Karta: <code>{card_info}</code>\n"
        f"💰 Yechilayotgan summa: <b>{money:,} so'm</b>"
    )

    if ADMIN_ID != 0:
        try:
            await message.bot.send_message(ADMIN_ID, admin_notification)
        except Exception as e:
            logging.error(f"Adminga yuborishda xatolik: {e}")

    await message.answer(
        f"✅ <b>So'rovingiz qabul qilindi!</b>\n"
        f"Mablag' (<b>{money:,} so'm</b>) 24 soat ichida kartangizga o'tkaziladi.",
        reply_markup=get_reply_keyboard()
    )


# ------------------ KUNLIK BONUS VA REFFERAL ------------------

@dp.message(F.text == "🎁 Kunlik Bonus")
async def claim_daily_bonus(message: Message) -> None:
    if not await verify_access(message):
        return

    user_id = message.from_user.id
    now = datetime.datetime.now()
    last_bonus = users_db.get(user_id, {}).get("last_bonus")

    if last_bonus and (now - last_bonus).total_seconds() < 86400:
        rem_sec = 86400 - (now - last_bonus).total_seconds()
        rem_h = int(rem_sec // 3600)
        rem_m = int((rem_sec % 3600) // 60)
        await message.answer(f"⏳ Kunlik bonus olingan! Keyingisi <b>{rem_h} soat {rem_m} daqiqa</b>dan so'ng beriladi.")
        return

    b_score = random.randint(1, 3)
    b_money = b_score * 3000
    users_db[user_id]["score"] = users_db[user_id].get("score", 0) + b_score
    users_db[user_id]["money"] = users_db[user_id].get("money", 0) + b_money
    users_db[user_id]["last_bonus"] = now

    await message.answer(
        f"🎉 <b>Tabriklaymiz! Kunlik Sovg'angiz:</b>\n"
        f"────────────────────────\n"
        f"🏆 Ball: <b>+{b_score} ball</b>\n"
        f"💰 Balans: <b>+{b_money:,} so'm</b>\n\n"
        f"Ertaga yana kelib o'z bonusingizni oling!"
    )


@dp.message(F.text == "🔗 Do'stlarni Taklif Qilish")
async def referral_program_info(message: Message) -> None:
    if not await verify_access(message):
        return

    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    u_data = users_db.get(user_id, {})
    refs = u_data.get("referrals_count", 0)
    referred_list = u_data.get("referred_users", [])

    ref_items = ""
    if referred_list:
        for idx, item in enumerate(referred_list[-5:], 1):
            ref_items += f"{idx}. {item['name']}\n"
    else:
        ref_items = "<i>Hozircha do'stlaringiz qo'shilmagan.</i>\n"

    text = (
        f"👥 <b>Do'stlarni Taklif Qilish Tizimi</b>\n"
        f"────────────────────────\n"
        f"Har bir taklif qilingan faol a'zo uchun:\n"
        f"🎁 <b>+3 Ball</b> va <b>+10,000 so'm</b> mukofot!\n\n"
        f"📊 Sizning referallaringiz: <b>{refs} ta</b>\n"
        f"📋 Oxirgi qo'shilganlar:\n{ref_items}\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )
    await message.answer(text)


@dp.message(F.text == "🏆 Top Reyting")
async def show_leaderboard(message: Message) -> None:
    if not await verify_access(message):
        return

    sorted_users = sorted(
        users_db.values(),
        key=lambda x: (x.get("score", 0), x.get("money", 0)),
        reverse=True
    )[:10]

    board = "🏆 <b>Liderlar Jadvali (Top-10)</b>\n"
    board += "────────────────────────\n"

    for idx, u in enumerate(sorted_users, 1):
        name = u.get("name", "Foydalanuvchi")
        score = u.get("score", 0)
        money = u.get("money", 0)
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        board += f"{medal} <b>{html.escape(name)}</b>\n   ├ Ball: <b>{score}</b> | Pul: <b>{money:,} so'm</b>\n"

    await message.answer(board)


@dp.message(F.text == "🎖 Katta Konkurs")
async def contest_screen(message: Message) -> None:
    if not await verify_access(message):
        return

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
        f"🎖 <b>Oylik Super Konkurs!</b>\n"
        f"────────────────────────\n"
        f"💰 Bosh sovrin: <b>500,000 so'm naqd pul!</b>\n"
        f"📌 Shart: Eng ko'p referal va ball to'plagan 1-o'rin sohibi sovrinni yutib oladi.\n\n"
        f"🥇 Hozirgi yetakchi: <b>{top_name}</b> ({top_refs} ta taklif)\n"
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

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_btns))


@dp.callback_query(F.data == "register_contest")
async def register_contest_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ContestStates.waiting_for_name)
    await callback.message.answer("1️⃣ Iltimos, konkursda ko'rinadigan <b>Ismingizni</b> yozing:")


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
        f"🎉 <b>Tabriklaymiz, {full_name}!</b>\n"
        f"Siz muvaffaqiyatli konkurs ishtirokchisiga aylandingiz. Do'stlaringizni taklif qilib g'olib bo'ling!",
        reply_markup=get_reply_keyboard()
    )


@dp.message(F.text == "📜 Qoidalar va Shartlar")
async def show_rules_handler(message: Message) -> None:
    rules = (
        "📜 <b>Loyihaning Asosiy Qoidalari:</b>\n"
        "────────────────────────\n"
        "1. <b>DTM Testlari:</b> Har bir savolga 30 soniya ajratiladi. 10 ta savoldan barchasini to'g'ri topsangiz +5 ball beriladi.\n"
        "2. <b>Vaqt chegarasi:</b> Testni har 24 soatda bir marotaba bepul topshirish mumkin.\n"
        "3. <b>Referal tizimi:</b> Taklif qilgan har bir do'stingiz uchun 3 ball va 10,000 so'm qo'shiladi.\n"
        "4. <b>Mablag' yechish:</b> Balansdan pul yechish uchun hisobingizda kamida 50 ball bo'lishi shart.\n"
        "5. <b>Halollik:</b> Soxta (nakrutka) akkauntlar aniqlansa, foydalanuvchi konkursdan chetlashtiriladi."
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
        await message.answer("🚫 Sizda adminlik huquqi yo'q!")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish (Broadcast)", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="💳 Balansni O'zgartirish", callback_data="adm_change_balance")]
    ])
    await message.answer("⚙️ <b>Admin boshqaruv paneliga xush kelibsiz:</b>", reply_markup=keyboard)


@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)
    await callback.message.answer("📝 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:")


@dp.message(BroadcastStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    sent_count, err_count = 0, 0
    status_msg = await message.answer("🚀 Xabar yuborilmoqda...")

    for uid in list(users_db.keys()):
        if uid < 10000:
            continue
        try:
            await message.send_copy(chat_id=uid)
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            err_count += 1

    await status_msg.edit_text(f"✅ Yuborildi: {sent_count} ta\n❌ Yetib bormadi: {err_count} ta")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Bosh menyu / Qayta ishga tushirish"),
        BotCommand(command="admin", description="Admin paneli")
    ])
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
