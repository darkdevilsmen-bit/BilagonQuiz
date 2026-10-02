import asyncio
import datetime
import logging
import random
import sys
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup, Message

BOT_TOKEN = "8963661833:AAFxzjb0n0HZux7ss8v_gQUwo-JgsSsZ8_c"
CHANNEL_USERNAME = "@llFGqeWBsuZlMGYy"  # Rasmiy kanal (Bot kanalga ADMIN bo'lishi shart!)
CHANNEL_LINK = "https://t.me/+llFGqeWBsuZlMGYy"
ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 000000000

dp = Dispatcher()

# Foydalanuvchilar bazasi va boshlang'ich 10 ta o'zbek ismli bot / raqobatchi liderlar
users_db = {
    "bot_1": {"score": 95, "name": "Bekzod To'rayev", "referrals_count": 0},
    "bot_2": {"score": 85, "name": "Jasurbek Karimov", "referrals_count": 0},
    "bot_3": {"score": 75, "name": "Dilshod Olimov", "referrals_count": 0},
    "bot_4": {"score": 68, "name": "Sardor Rahimov", "referrals_count": 0},
    "bot_5": {"score": 60, "name": "Azizbek Toshmatov", "referrals_count": 0},
    "bot_6": {"score": 52, "name": "Oybek Sharipov", "referrals_count": 0},
    "bot_7": {"score": 45, "name": "Bobur Mirzayev", "referrals_count": 0},
    "bot_8": {"score": 38, "name": "Madina Rahimova", "referrals_count": 0},
    "bot_9": {"score": 30, "name": "Ziyoda Saidova", "referrals_count": 0},
    "bot_10": {"score": 25, "name": "Shaxzodbek", "referrals_count": 0}
}

verified_users = set()


class WithdrawStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_card = State()


class BroadcastStates(StatesGroup):
    waiting_for_broadcast_message = State()


class AdminScoreStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_score_amount = State()


# --- KENGAYTIRILGAN VA HAR XIL SAVOLLAR BAZASI ---
CATEGORIES_DB = {
    "logic": {
        "title": "🧠 Mantiqiy Savollar",
        "questions": [
            ("Qaysi oyda 28 kun bor?", ["Hamma oylarda", "Faqat fevralda", "Faqat iyunda", "Fevral va martda"], 0),
            ("O'choqqa o'tin qablasangiz, birinchi bo'lib nimani yoqasiz?", ["O'tinni", "Gugurtni", "Kül ni", "Qog'ozni"], 1),
            ("Yerdan ko'tarish oson, lekin uzoqqa otib bo'lmaydi. Bu nima?", ["Tosh", "Tuk", "Qum", "Suv"], 1),
            ("5 ta olma bor edi, 3 tasini olib qo'yishdi. Sizda nechta olma bor?", ["2 ta", "3 ta", "5 ta", "1 ta"], 1),
            ("O'z egasidan qochib ketmaydigan, lekin doim ergashadigan narsa nima?", ["Soyaboni", "Soya", "Etik", "Do'ppi"], 1),
            ("Ikki kishi shaxmat o'ynashdi. Ular 5 ta partiya o'ynashdi va har biri 3 tadan g'alaba qozondi. Bu qanday mumkin?", ["Durang bo'lgan", "Ular birga o'ynashmagan", "Boshqalar bilan o'ynagan", "Xato savol"], 1),
            ("Besh aka-ukaning bittadan singlisi bor. Hammasi bo'lib uylar nechta kishi yashaydi?", ["6 kishi", "10 kishi", "5 kishi", "7 kishi"], 0),
            ("Qaysi dengizda suv yo'q?", ["Qora dengizda", "Xaritadagi dengizda", "Orol dengizida", "Qizil dengizda"], 1),
            ("Qaysi narsa qanchalik ko'p tozalasangiz, shunchalik qorayib boradi?", ["Doska", "Kiyim", "Oyna", "Gilam"], 0),
            ("Dunyodagi eng tez harakatlanadigan narsa nima?", ["Ovoz", "Nur (Yorug'lik)", "Shamolsiz havo", "Raketa"], 1),
            ("Bir kishi 9 qavatli uyda yashaydi. U har kuni liftda pastga tushadi, lekin yuqoriga chiqishda faqat 5-qavatgacha chiqib, qolganini piyoda chiqadi. Nega?", ["Charchaydi", "Bo'yi past (tugmani bosa olmaydi)", "Sport uchun", "Lift buzilgan"], 1),
            ("Qaysi savolga hech qachon 'Ha' deb javob berib bo'lmaydi?", ["Uxlayapsizmi?", "Tirikmisiz?", "Suv ichdingizmi?", "Ovqatedingizmi?"], 0),
            ("Qaysi narsani sindirish uchun uning nomini aytish kifoya?", ["Sukunat (Jimlik)", "Shisha", "Tuxum", "Muz"], 0),
            ("Qaysi tilda gaplashadigan odamlar juda ko'p, lekin ular hech qachon so'z yozishmaydi?", ["Chaqaloqlar", "Dam oluvchilar", "Hayvonlar", "Tilaklar"], 0),
            ("Qaysi haroratda suv muzga aylanmaydi, lekin qaynamaydi ham?", ["0 daraja", "100 daraja", "Xona harorati (20°C)", "Minus 10"], 2)
        ]
    },
    "it": {
        "title": "💻 IT & Texnologiyalar",
        "questions": [
            ("Python dasturlash tilining asoschisi kim?", ["Guido van Rossum", "Livan Torvalds", "Bill Geyts", "Stiv Jobs"], 0),
            ("Kompyuterning 'miyasi' nima deb ataladi?", ["RAM", "Protsessor (CPU)", "Videokarta", "Qattiq disk"], 1),
            ("WWW qisqartmasi nimani anglatadi?", ["World Wide Web", "World Web Wide", "Web Wide World", "Wide World Web"], 0),
            ("Qaysi biri operatsion tizim emas?", ["Linux", "Windows", "Google Chrome", "macOS"], 2),
            ("1 Bayt necha Bitdan iborat?", ["8", "1024", "16", "32"], 0),
            ("Internetning otasi deb kim hisoblanadi?", ["Tim Berners-Li", "Vint Cerf", "Mark Zukerberg", "Ilon Mask"], 1),
            ("HTML bu nima?", ["Dasturlash tili", "Belgilash tili", "Ma'lumotlar bazasi", "Antivirus"], 1),
            ("Eng mashhur ma'lumotlar bazasini boshqarish tizimlaridan biri?", ["SQL Server", "Photoshop", "Notepad", "Word"], 0),
            ("Kibernetika fanining asoschisi kim?", ["Norbert Winner", "Alan Turing", "Blez Paskal", "Albert Eynshteyn"], 0),
            ("Sun'iy intellekt qisqartmasi qaysi?", ["AI", "IT", "CPU", "UI"], 0),
            ("JavaScript asosan qayerda ishlatiladi?", ["Faqat serverda", "Veb-sahifalarni interaktiv qilishda", "Faqat operatsion tizimda", "Antiviruslarda"], 1),
            ("GitHub qanday maqsad uchun xizmat qiladi?", ["Kodlarni saqlash va jamoaviy boshqarish", "Video montaj qilish", "Dizayn chizish", "Chat qilish"], 0),
            ("Eng birinchi yaratilgan dasturlash tili qaysi?", ["Fortran", "Python", "C++", "Java"], 0),
            ("SSD xotira qaysi texnologiyaga asoslangan?", ["Magnit plastinalar", "Flesh xotira (Chips)", "Optik disk", "Lenta"], 1),
            ("IP manzil nima uchun kerak?", ["Tarmoqdagi qurilmalarni aniqlash uchun", "Fayllarni ochish uchun", "Parolni saqlash uchun", "Internet tezligini oshirish uchun"], 0)
        ]
    },
    "history": {
        "title": "🏛 Tarix & Geografiya",
        "questions": [
            ("Amir Temur qaysi yilda tavallud topgan?", ["1336-yil", "1365-yil", "1405-yil", "1219-yil"], 0),
            ("O'zbekistonning poytaxti qaysi shahar?", ["Samarqand", "Buxoro", "Toshkent", "Xiva"], 2),
            ("Dunyodagi eng katta okean qaysi?", ["Tinch okeani", "Atlantika okeani", "Hind okeani", "Shimoliy Muz okeani"], 0),
            ("Buyuk Ipak yo'li qaysi qit'alarni bog'lagan?", ["Osiyo va Yevropa", "Afrika va Amerika", "Avstraliya va Antarktida", "Faqat Osiyo"], 0),
            ("Yer yuzidagi eng uzun daryo qaysi?", ["Nil", "Amazonka", "Sirdaryo", "Amudaryo"], 0),
            ("Alisher Navoiy qaysi asrda yashab ijod qilgan?", ["XV asr", "XIV asr", "XVI asr", "XII asr"], 0),
            ("Fransiyaning poytaxti qaysi shahar?", ["Berlin", "Parij", "Madrid", "Rim"], 1),
            ("Dunyodagi eng baland tog' cho'qqisi qaysi?", ["Everest", "Elbrus", "Kilimanjaro", "Chimyon"], 0),
            ("Boburiylar sulolasining asoschisi kim?", ["Zahiriddin Muhammad Bobur", "Amir Temur", "Mirzo Ulug'bek", "Temur Malik"], 0),
            ("Yer yuzida nechta okean bor?", ["4 ta", "5 ta", "6 ta", "3 ta"], 1),
            ("Ibn Sino tavallud topgan shahar?", ["Buxoro", "Samarqand", "Urganch", "Xiva"], 0),
            ("Dunyodagi eng katta cho'l qaysi?", ["Sahara", "Qoraqum", "Gobi", "Antarktida cho'li"], 3),
            ("Rim shahri qaysi davlatda joylashgan?", ["Italiya", "Gretsiya", "Ispaniya", "Fransiya"], 0),
            ("Buyuk Britaniyaning poytaxti qaysi?", ["London", "Dublin", "Parij", "Berlin"], 0),
            ("Ikkinchi jahon urushi qaysi yillarda bo'lib o'tgan?", ["1939–1945", "1914–1918", "1941–1945", "1935–1940"], 0)
        ]
    }
}


@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    user_id = request.from_user.id
    verified_users.add(user_id)


async def check_real_subscription(bot: Bot, user_id: int) -> bool:
    if user_id in verified_users:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            verified_users.add(user_id)
            return True
    except Exception:
        return True
    return False


def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🚀 Viktorinani Boshlash", callback_data="select_category")],
        [InlineKeyboardButton(text="🎁 Kunlik Bonus (+1...+5 ball)", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="🏆 Top Reyting (Liderlar)", callback_data="top_board")],
        [InlineKeyboardButton(text="💎 Mening Balansim & Kabinet", callback_data="my_balance")],
        [InlineKeyboardButton(text="🔗 Referal Tizimi (+5 ball)", callback_data="referral_info")],
        [InlineKeyboardButton(text="📜 O'yin Qoidalari", callback_data="rules")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    if user_id not in users_db:
        users_db[user_id] = {
            "score": 0,
            "question_num": 1,
            "game_questions": [],
            "wrong_answers": [],
            "referrals_count": 0,
            "last_bonus": None,
            "category": "logic",
            "name": user_name,
            "timer_task": None
        }

    has_access = await check_real_subscription(message.bot, user_id)
    if not has_access:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data="check_joined")]
        ])
        text = (
            f"✨ **Salom, {html.bold(user_name)}!**\n\n"
            f"📢 Botdan foydalanish uchun avval rasmiy kanalimizga a'zo bo'ling:\n\n"
            f"👇 Avval kanalga obuna bo'ling, so'ngra **'A'zo bo'ldim'** tugmasini bosing:"
        )
        await message.answer(text, reply_markup=keyboard)
        return

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
            if referrer_id != user_id and referrer_id in users_db:
                users_db[referrer_id]["referrals_count"] += 1
                users_db[referrer_id]["score"] += 5
                try:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎉 **Ajoyib yangilik!** Referal havolangiz orqali yangi do'st qo'shildi!\n🎁 Hisobingizga **+5 ball** qo'shildi! 🚀"
                    )
                except:
                    pass
        except:
            pass

    text = (
        f"✨ **Salom, {html.bold(user_name)}!**\n\n"
        f"🎯 **«Bilag'on Quiz»** botiga xush kelibsiz!\n\n"
        f"🧠 Har bir o'yinga har xil va yangi savollar tasodifiy tarzda tanlab beriladi. Savolga javob berish uchun **30 soniya** vaqt bor!\n"
        f"🎁 Kunlik bonus oling, do'stlar taklif qiling va reytingda 1-o'rinni egallang!\n\n"
        f"⬇️ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_main_menu(user_id))


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    verified_users.add(user_id)
    await callback.message.delete()
    await command_start_handler(callback.message, state)
    await callback.answer("Tabriklaymiz, obuna tasdiqlandi! 🎉", show_alert=True)


@dp.callback_query(F.data == "select_category")
async def select_category_handler(callback: CallbackQuery) -> None:
    keyboard_buttons = []
    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard_buttons.append([InlineKeyboardButton(text=cat_val["title"], callback_data=f"cat_{cat_key}")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")])
    
    text = "📚 **Test yo'nalishini tanlang:**"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_"))
async def set_category_handler(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    cat_key = callback.data.split("_")[1]
    
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "last_bonus": None, "name": callback.from_user.full_name}
        
    users_db[user_id]["category"] = cat_key
    await start_quiz_session_processed(callback.message, user_id)
    await callback.answer()


@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "last_bonus": None, "name": callback.from_user.full_name}
        
    now = datetime.datetime.now()
    last_bonus = users_db[user_id].get("last_bonus")
    
    if last_bonus and (now - last_bonus).total_seconds() < 86400:
        remaining_hours = int((86400 - (now - last_bonus).total_seconds()) // 3600)
        await callback.answer(f"⏳ Siz kunlik bonusni allaqachon olgansiz! Keyingi bonus {remaining_hours} soatdan keyin ochiladi.", show_alert=True)
        return
        
    bonus_score = random.randint(1, 5)
    users_db[user_id]["score"] += bonus_score
    users_db[user_id]["last_bonus"] = now
    
    await callback.answer(f"🎉 Tabriklaymiz! Kunlik bonus sifatida hisobingizga +{bonus_score} ball qo'shildi! 🎁", show_alert=True)
    
    text = "🏠 **Asosiy Menyu:**\n\nKerakli bo'limni tanlang:"
    await callback.message.edit_text(text, reply_markup=get_main_menu(user_id))


@dp.callback_query(F.data == "top_board")
async def top_board_handler(callback: CallbackQuery) -> None:
    # Barcha foydalanuvchilar va soxta liderlarni ballari bo'yicha saralaymiz
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get("score", 0), reverse=True)[:10]
    
    text = "🏆 **Top 10 Liderlar Reytingi**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, (u_id, u_data) in enumerate(sorted_users, 1):
        name = u_data.get("name", "Foydalanuvchi")
        score = u_data.get("score", 0)
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        text += f"{medal} **{name}** — 🏆 {score} ball\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_panel_handler(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    
    is_admin = False
    if ADMIN_ID and user_id == ADMIN_ID:
        is_admin = True
    elif ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower():
        is_admin = True
        
    if not is_admin:
        await message.answer("❌ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return
        
    # Haqiqiy userlar soni (bot ismlarini hisoblamaymiz)
    real_users_count = sum(1 for uid in users_db.keys() if not str(uid).startswith("bot_"))
    total_score = sum(u.get("score", 0) for u in users_db.values())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish (Send)", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ / ➖ Foydalanuvchi Ballini O'zgartirish", callback_data="admin_change_score")],
        [InlineKeyboardButton(text="🏠 Asosiy Menyuga Qaytish", callback_data="back_to_menu")]
    ])
    
    text = (
        f"👑 **Admin Panelga Xush Kelibsiz!**\n\n"
        f"📊 **Statistika:**\n"
        f"👥 Haqiqiy foydalanuvchilar: **{real_users_count} ta**\n"
        f"🏆 Jami ballar: **{total_score} ta**\n\n"
        f"Kerakli amalni tanlang:"
    )
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "admin_change_score")
async def admin_change_score_start(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    username = callback.from_user.username
    is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower())
    if not is_admin:
        return
        
    await state.set_state(AdminScoreStates.waiting_for_user_id)
    text = "🆔 Ball qo'shmoqchi yoki ayirmoqchi bo'lgan foydalanuvchining **Telegram ID** raqamini yuboring:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.message(AdminScoreStates.waiting_for_user_id)
async def process_admin_user_id(message: Message, state: FSMContext) -> None:
    try:
        target_id = int(message.text.strip())
        if target_id not in users_db:
            await message.answer("❌ Bunday ID raqamidagi foydalanuvchi topilmadi! Qaytadan ID yuboring:")
            return
        await state.update_data(target_user_id=target_id)
        await state.set_state(AdminScoreStates.waiting_for_score_amount)
        current_score = users_db[target_id]["score"]
        await message.answer(f"👤 Foydalanuvchi topildi. Hozirgi balli: **{current_score}**\n\nQo'shiladigan ball miqdorini yuboring (Masalan: `10` yoki ayrish uchun `-5`):")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format! Faqat raqam yuboring:")


@dp.message(AdminScoreStates.waiting_for_score_amount)
async def process_admin_score_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_id = data.get("target_user_id")
        await state.clear()
        
        users_db[target_id]["score"] += amount
        new_score = users_db[target_id]["score"]
        
        await message.answer(f"✅ Muvaffaqiyatli o'zgartirildi!\nFoydalanuvchi ID: `{target_id}`\nYangi bali: **{new_score} ta**")
        
        try:
            await message.bot.send_message(target_id, f"🎁 Admin tomonidan balansingiz o'zgartirildi! Hozirgi balansingiz: **{new_score} ball**")
        except:
            pass
    except ValueError:
        await message.answer("❌ Noto'g'ri qiymat! Faqat butun son yuboring (masalan: 15):")


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    username = callback.from_user.username
    is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower())
    if not is_admin:
        await callback.answer("Huquqingiz yo'q!", show_alert=True)
        return
        
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)
    text = "📢 **Xabar Tarqatish Rejimi**\n\nBarcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.message(BroadcastStates.waiting_for_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower())
    if not is_admin:
        return
        
    await state.clear()
    sent_count = 0
    fail_count = 0
    
    status_msg = await message.answer("⏳ Xabar tarqatilmoqda...")
    
    for uid in users_db.keys():
        if str(uid).startswith("bot_"):
            continue
        try:
            await message.send_copy(chat_id=uid)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1
            
    await status_msg.edit_text(
        f"✅ **Xabar tarqatish yakunlandi!**\n\n"
        f"📤 Muvaffaqiyatli yuborildi: **{sent_count} ta**\n"
        f"❌ Yuborilmadi: **{fail_count} ta**"
    )


@dp.callback_query(F.data == "referral_info")
async def referral_info_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    bot_username = "BilagonQuizBot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    refs = users_db.get(user_id, {}).get("referrals_count", 0)
    
    text = (
        f"🔗 **Sizning Shaxsiy Referal Tizimingiz**\n\n"
        f"👥 Taklif qilgan do'stlarim: **{refs} ta**\n"
        f"🎁 Har bir taklif qilingan do'st uchun: **+5 ball** beriladi!\n\n"
        f"📋 **Sizning taklif havolangiz:**\n`{ref_link}`\n\n"
        f"💡 *Ushbu havolani do'stlaringizga yuboring va ballaringizni ko'paytiring!*"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = callback.from_user.id
    await cancel_timer(user_id)
    text = "🏠 **Asosiy Menyu:**\n\nKerakli bo'limni tanlang:"
    await callback.message.edit_text(text, reply_markup=get_main_menu(user_id))
    await callback.answer()


@dp.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery) -> None:
    text = (
        "📜 <b>O ' Y I N   Q O I D A L A R I</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📢 <b>0. Obuna:</b> Botdan foydalanish uchun kanalimizga a'zo bo'ling.\n\n"
        "🎯 <b>1. Testlar soni:</b> Jami <b>10 ta tasodifiy test</b> taqdim etiladi.\n\n"
        "⏱ <b>2. Vaqt cheklovi:</b> Har bir savol uchun aniq <b>30 soniya</b> vaqt bor.\n\n"
        "🏆 <b>3. Liderlar & Bonus:</b> Kunlik bonus oling va Top reytingda liderlarni ortda qoldiring!\n\n"
        "🔄 <b>4. Qaytadan o'ynash sharti:</b> O'yinni qaytadan boshlash uchun kamida <b>3 ta do'st</b> taklif qilishingiz shart.\n\n"
        "💎 <b>5. Pulni yechish:</b> 50 ta ball to'plang va kartangizga pul o'tkazib oling!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Omad yor bo'lsin! Tugmani bosing va boshlang 👇</i>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()


@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "name": callback.from_user.full_name}
        
    u_data = users_db[user_id]
    score = u_data.get("score", 0)
    refs = u_data.get("referrals_count", 0)
    
    bot_username = "BilagonQuizBot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"💎 **Foydalanuvchi Kabineti & Balans**\n\n"
        f"👤 ID: `{user_id}`\n"
        f"👥 **Taklif qilgan do'stlarim:** **{refs} / 3 ta**\n"
        f"🏆 Jami ballaringiz: **{score} ta**\n\n"
        f"🔗 **Sizning referal havolangiz:**\n`{ref_link}`\n"
    )
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="💵 Pulni Yechib Olish", callback_data="withdraw_money")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))
    await callback.answer()


@dp.callback_query(F.data == "withdraw_money")
async def withdraw_money_handler(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    score = users_db.get(user_id, {}).get("score", 0)
    
    if score < 50:
        text = (
            f"❌ **Mablag'ni yechib olish imkonsiz!**\n\n"
            f"⚠️ Pulni yechib olish uchun hisobingizda kamida **50 ball** bo'lishi kerak!\n"
            f"📊 Hozirgi ballingiz: **{score} / 50**\n\n"
            f"💡 *Ko'proq testlar yeching va referal havolangiz orqali do'stlaringizni taklif qiling!*"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="my_balance")]])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    await state.set_state(WithdrawStates.waiting_for_name)
    text = (
        f"✅ **Tabriklaymiz! Balansingiz yetarli ({score} ball).**\n\n"
        f"📝 Pulni o'tkazib berishimiz uchun iltimos, **Ism va Familiyangizni** kiriting:"
    )
    await callback.message.edit_text(text)
    await callback.answer()


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    await state.update_data(user_fullname=full_name)
    
    await state.set_state(WithdrawStates.waiting_for_card)
    await message.answer("💳 Endi 16 xonali **Karta raqamingizni** (yoki karta turini, masalan: *Uzcard/Humo*) yuboring:")


@dp.message(WithdrawStates.waiting_for_card)
async def process_withdraw_card(message: Message, state: FSMContext) -> None:
    card_info = message.text.strip()
    data = await state.get_data()
    fullname = data.get("user_fullname")
    user_id = message.from_user.id
    username = message.from_user.username
    score = users_db.get(user_id, {}).get("score", 0)
    
    await state.clear()
    
    admin_text = (
        f"🔔 **Yangi Pul Yechish So'rovi!**\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{username or 'yoq'}, ID: `{user_id}`)\n"
        f"🔤 Ism Familiya: **{fullname}**\n"
        f"💳 Karta raqami: **{card_info}**\n"
        f"🏆 Ballari: **{score} ta**"
    )
    
    try:
        await message.bot.send_message(f"@{ADMIN_USERNAME}", admin_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
        
    await message.answer(
        f"🎉 **So'rovingiz muvaffaqiyatli qabul qilindi!**\n\n"
        f"Ism: {fullname}\n"
        f"Karta: {card_info}\n\n"
        f"⏳ Adminlar tez orada ma'lumotlarni tekshirib, mablag'ni kartangizga o'tkazib berishadi!",
        reply_markup=get_main_menu(user_id)
    )


async def start_quiz_session_processed(message: Message, user_id: int):
    u_data = users_db[user_id]
    refs = u_data.get("referrals_count", 0)
    
    if u_data.get("is_finished", False) and refs < 3:
        bot_username = "BilagonQuizBot"
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        text = (
            f"❌ **Qaytadan o'ynash cheklangan!**\n\n"
            f"⚠️ Yangitdan o'yinni boshlash uchun referal havolangiz orqali kamida **3 ta do'stingizni** taklif qilishingiz kerak!\n\n"
            f"👥 **Taklif qilgan do'stlarim:** **{refs} / 3 ta**\n\n"
            f"🔗 **Referal havolangiz:**\n`{ref_link}`"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Referal Havolasini Olish", callback_data="referral_info")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
        ])
        await message.edit_text(text, reply_markup=keyboard)
        return

    cat_key = u_data.get("category", "logic")
    pool = list(CATEGORIES_DB[cat_key]["questions"])
    random.shuffle(pool)
    
    game_questions_processed = []
    for q_text, options, correct_idx in pool[:10]:
        correct_answer_text = options[correct_idx]
        shuffled_options = list(options)
        random.shuffle(shuffled_options)
        new_correct_idx = shuffled_options.index(correct_answer_text)
        game_questions_processed.append((q_text, shuffled_options, new_correct_idx))

    u_data["question_num"] = 1
    u_data["game_questions"] = game_questions_processed
    u_data["wrong_answers"] = []
    u_data["score"] = 0
    u_data["is_finished"] = False
    
    await message.edit_text("⏳ *Har xil va noyob savollar tayyorlanmoqda... 1-savol boshlanadi 🟢*")
    await send_next_question(message, user_id)


async def cancel_timer(user_id: int):
    if user_id in users_db and users_db[user_id].get("timer_task"):
        users_db[user_id]["timer_task"].cancel()
        users_db[user_id]["timer_task"] = None


async def send_next_question(message: Message, user_id: int):
    await cancel_timer(user_id)
    u_data = users_db[user_id]
    q_num = u_data["question_num"]
    
    if q_num > len(u_data["game_questions"]):
        await finish_quiz(message, user_id)
        return
        
    selected_q = u_data["game_questions"][q_num - 1]
    q_text, options, correct_idx = selected_q
    
    u_data["current_q_data"] = selected_q
        
    keyboard_buttons = []
    for idx, opt in enumerate(options):
        keyboard_buttons.append([InlineKeyboardButton(text=opt, callback_data=f"ans_{idx}")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    cat_title = CATEGORIES_DB[u_data.get("category", "logic")]["title"]
    text = (
        f"🎯 **{cat_title} | {q_num}-savol / 10**\n"
        f"⏱ *Vaqt: 30 soniya!*\n\n"
        f"❓ **{q_text}**"
    )
    
    await message.answer(text, reply_markup=reply_markup)
    
    async def timer_countdown():
        await asyncio.sleep(30)
        if user_id in users_db and users_db[user_id]["question_num"] == q_num:
            q_text, options, correct_idx = u_data["current_q_data"]
            u_data["wrong_answers"].append((q_text, options[correct_idx]))
            
            u_data["question_num"] += 1
            try:
                await message.bot.send_message(user_id, "⏰ **Vaqt tugadi!** Afsuski, bu savolga ulgurmadingiz 😕")
            except:
                pass
            
            if u_data["question_num"] > len(u_data["game_questions"]):
                await finish_quiz(message, user_id)
            else:
                await send_next_question(message, user_id)

    u_data["timer_task"] = asyncio.create_task(timer_countdown())


@dp.callback_query(F.data.startswith("ans_"))
async def process_answer(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db or "current_q_data" not in users_db[user_id]:
        await callback.answer("O'yin tugagan!", show_alert=True)
        return
        
    await cancel_timer(user_id)
    u_data = users_db[user_id]
    chosen_idx = int(callback.data.split("_")[1])
    q_text, options, correct_idx = u_data["current_q_data"]
    
    if chosen_idx == correct_idx:
        u_data["score"] += 1
        await callback.message.edit_text(callback.message.text + "\n\n✅ **To'g'ri javob! (+1 ball) 🎉**")
    else:
        u_data["wrong_answers"].append((q_text, options[correct_idx]))
        await callback.message.edit_text(callback.message.text + f"\n\n❌ **Noto'g'ri javob! 😕**\n💡 To'g'ri javob: *{options[correct_idx]}*")
        
    u_data["question_num"] += 1
    
    if u_data["question_num"] > len(u_data["game_questions"]):
        await finish_quiz(callback.message, user_id)
    else:
        await send_next_question(callback.message, user_id)
    await callback.answer()


async def finish_quiz(message: Message, user_id: int):
    u_data = users_db[user_id]
    u_data["is_finished"] = True
    final_score = u_data["score"]
    wrong_list = u_data["wrong_answers"]
    
    review_text = ""
    if wrong_list:
        review_text = "\n❌ **Siz xato qilgan savollar va to'g'ri javoblar:**\n"
        for idx, (q, ans) in enumerate(wrong_list, 1):
            review_text += f"{idx}. {q}\n   👉 *To'g'ri javob:* {ans}\n\n"
    else:
        review_text = "\n🌟 **Ajoyib! Barcha savollarga 100% to'g'ri javob berdingiz!** 🎉\n"

    text = (
        f"🏆 **Tabriklaymiz! Test yakunlandi!** 🎉\n\n"
        f"📊 Siz jami testdan **{final_score} ta** to'g'ri topdingiz!\n"
        f"{review_text}"
        f"💎 Balansingizni ko'rish va pulni yechib olish uchun quyidagi tugmani bosing:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Balans & Pulni Yechib Olish", callback_data="my_balance")],
        [InlineKeyboardButton(text="🔄 Qaytadan O'ynash", callback_data="select_category")]
    ])
    await message.answer(text, reply_markup=keyboard)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi!")