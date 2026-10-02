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
    "bot_1": {"score": 45, "money": 135000, "name": "Bekzod To'rayev", "referrals_count": 0, "referred_users": []},
    "bot_2": {"score": 38, "money": 114000, "name": "Jasurbek Karimov", "referrals_count": 0, "referred_users": []},
    "bot_3": {"score": 32, "money": 96000, "name": "Dilshod Olimov", "referrals_count": 0, "referred_users": []},
    "bot_4": {"score": 28, "money": 84000, "name": "Sardor Rahimov", "referrals_count": 0, "referred_users": []},
    "bot_5": {"score": 24, "money": 72000, "name": "Azizbek Toshmatov", "referrals_count": 0, "referred_users": []},
    "bot_6": {"score": 20, "money": 60000, "name": "Oybek Sharipov", "referrals_count": 0, "referred_users": []},
    "bot_7": {"score": 17, "money": 51000, "name": "Bobur Mirzayev", "referrals_count": 0, "referred_users": []},
    "bot_8": {"score": 14, "money": 42000, "name": "Madina Rahimova", "referrals_count": 0, "referred_users": []},
    "bot_9": {"score": 11, "money": 33000, "name": "Ziyoda Saidova", "referrals_count": 0, "referred_users": []},
    "bot_10": {"score": 8, "money": 24000, "name": "Shaxzodbek", "referrals_count": 0, "referred_users": []}
}

verified_users = set()
pending_referrals = {}


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
            ("Dunyodagi eng tez harakatlanadigan narsa nima?", ["Ovoz", "Nur (Yorug'lik)", "Shamolsiz havo", "Raketa"], 1)
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
            ("Sun'iy intellekt qisqartmasi qaysi?", ["AI", "IT", "CPU", "UI"], 0)
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
            ("Yer yuzida nechta okean bor?", ["4 ta", "5 ta", "6 ta", "3 ta"], 1)
        ]
    }
}


async def process_referral_reward(bot: Bot, user_id: int, user_name: str):
    if user_id in pending_referrals:
        referrer_id = pending_referrals[user_id]
        if referrer_id in users_db and referrer_id != user_id:
            if user_id not in users_db[referrer_id]["referred_users"]:
                users_db[referrer_id]["referred_users"].append({"id": user_id, "name": user_name})
                users_db[referrer_id]["referrals_count"] += 1
                users_db[referrer_id]["score"] += 5
                users_db[referrer_id]["money"] += 10000  # Referal uchun +10,000 so'm
                
                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 **Ajoyib yangilik!** Siz taklif qilgan do'stingiz (**{user_name}**) kanalimizga qo'shildi!\n"
                        f"🎁 Hisobingizga **+5 ball** va **+10,000 so'm** qo'shildi! 🚀"
                    )
                except:
                    pass
        del pending_referrals[user_id]


@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    user_id = request.from_user.id
    user_name = request.from_user.full_name
    verified_users.add(user_id)
    await process_referral_reward(request.bot, user_id, user_name)


async def check_real_subscription(bot: Bot, user_id: int, user_name: str) -> bool:
    if user_id in verified_users:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator", "restricted"]:
            verified_users.add(user_id)
            await process_referral_reward(bot, user_id, user_name)
            return True
    except Exception:
        return True
    return False


def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🚀 Viktorinani Boshlash", callback_data="select_category")],
        [InlineKeyboardButton(text="🎁 Kunlik Bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="🏆 Top Reyting (Liderlar)", callback_data="top_board")],
        [InlineKeyboardButton(text="💎 Mening Balansim & Kabinet", callback_data="my_balance")],
        [InlineKeyboardButton(text="🔗 Referal Tizimi", callback_data="referral_info")],
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
            "money": 0,
            "question_num": 1,
            "game_questions": [],
            "wrong_answers": [],
            "referrals_count": 0,
            "referred_users": [],
            "last_bonus": None,
            "category": "logic",
            "name": user_name,
            "timer_task": None,
            "combo": 0
        }
    else:
        users_db[user_id]["name"] = user_name

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
            if referrer_id != user_id and referrer_id in users_db:
                pending_referrals[user_id] = referrer_id
        except:
            pass

    has_access = await check_real_subscription(message.bot, user_id, user_name)
    if not has_access:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish / So'rov Yuborish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check_joined")]
        ])
        text = (
            f"✨ **Salom, {html.bold(user_name)}!**\n\n"
            f"📢 Botdan foydalanish uchun avval rasmiy kanalimizga a'zo bo'ling yoki so'rov yuboring:\n\n"
            f"👇 Tugmani bosing, so'ngra **'Obunani Tekshirish'** tugmasini bosing:"
        )
        await message.answer(text, reply_markup=keyboard)
        return

    text = (
        f"✨ **Salom, {html.bold(user_name)}!**\n\n"
        f"🎯 **«Bilag'on Quiz»** botiga xush kelibsiz!\n\n"
        f"🔥 **Combo Tizimi:** Ketma-ket to'g'ri topganingiz sari har bir savol uchun mukofot oshib boradi (**2,000 so'mdan 5,000+ so'mgacha** va ballar!) 🚀\n\n"
        f"⬇️ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_main_menu(user_id))


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    verified_users.add(user_id)
    await process_referral_reward(callback.bot, user_id, user_name)
    
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
        users_db[user_id] = {"score": 0, "money": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": callback.from_user.full_name, "combo": 0}
        
    users_db[user_id]["category"] = cat_key
    await start_quiz_session_processed(callback.message, user_id)
    await callback.answer()


@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": callback.from_user.full_name, "combo": 0}
        
    now = datetime.datetime.now()
    last_bonus = users_db[user_id].get("last_bonus")
    
    if last_bonus and (now - last_bonus).total_seconds() < 86400:
        remaining_hours = int((86400 - (now - last_bonus).total_seconds()) // 3600)
        await callback.answer(f"⏳ Siz kunlik bonusni allaqachon olgansiz! Keyingi bonus {remaining_hours} soatdan keyin ochiladi.", show_alert=True)
        return
        
    bonus_score = random.randint(1, 3)
    bonus_money = bonus_score * 2000
    users_db[user_id]["score"] += bonus_score
    users_db[user_id]["money"] += bonus_money
    users_db[user_id]["last_bonus"] = now
    
    await callback.answer(f"🎉 Tabriklaymiz! Kunlik bonus: +{bonus_score} ball va +{bonus_money:,} so'm qo'shildi! 🎁", show_alert=True)
    
    text = "🏠 **Asosiy Menyu:**\n\nKerakli bo'limni tanlang:"
    await callback.message.edit_text(text, reply_markup=get_main_menu(user_id))


@dp.callback_query(F.data == "top_board")
async def top_board_handler(callback: CallbackQuery) -> None:
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
    
    text = "🏆 **Top 10 Liderlar Reytingi (Pul bo'yicha)**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, (u_id, u_data) in enumerate(sorted_users, 1):
        name = u_data.get("name", "Foydalanuvchi")
        money = u_data.get("money", 0)
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        text += f"{medal} **{name}** — 💰 {money:,} so'm\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "referral_info")
async def referral_info_handler(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    bot_username = "BilagonQuizBot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    u_data = users_db.get(user_id, {"referrals_count": 0, "referred_users": []})
    refs = u_data.get("referrals_count", 0)
    referred_list = u_data.get("referred_users", [])
    
    list_text = ""
    if referred_list:
        list_text = "\n📋 **Sizdan kelgan foydalanuvchilar ro'yxati:**\n"
        for idx, ref in enumerate(referred_list, 1):
            list_text += f"{idx}. {ref['name']}\n"
    else:
        list_text = "\n📋 *Hozircha sizning havolangiz orqali hech kim qo'shilmadi.*"
    
    text = (
        f"🔗 **Sizning Shaxsiy Referal Tizimingiz**\n\n"
        f"👥 Taklif qilgan do'stlarim: **{refs} ta**\n"
        f"🎁 Har bir do'st uchun: **+5 ball va +10,000 so'm** beriladi!\n"
        f"{list_text}\n"
        f"📋 **Sizning taklif havolangiz:**\n`{ref_link}`\n"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "name": callback.from_user.full_name, "combo": 0}
        
    u_data = users_db[user_id]
    score = u_data.get("score", 0)
    money = u_data.get("money", 0)
    refs = u_data.get("referrals_count", 0)
    
    bot_username = "BilagonQuizBot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"💎 **Foydalanuvchi Kabineti & Balans**\n\n"
        f"👤 ID: `{user_id}`\n"
        f"👥 Taklif qilingan do'stlar: **{refs} ta**\n"
        f"🏆 Jami ballaringiz: **{score} ta ball**\n"
        f"💰 **Umumiy mablag': {money:,} so'm**\n\n"
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
    money = users_db.get(user_id, {}).get("money", 0)
    
    if money < 50000:
        needed_more = 50000 - money
        text = (
            f"❌ **Mablag'ni yechib olish imkonsiz!**\n\n"
            f"⚠️ Pulni yechib olish uchun hisobingizda kamida **50,000 so'm** bo'lishi kerak!\n"
            f"📊 Hozirgi balansingiz: **{money:,} so'm** (Yana {needed_more:,} so'm kerak)\n\n"
            f"💡 *Combo bilan ko'proq o'ynang va do'stlar taklif qiling!*"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="my_balance")]])
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    await state.set_state(WithdrawStates.waiting_for_name)
    text = (
        f"✅ **Tabriklaymiz! Balansingiz yetarli ({money:,} so'm).**\n\n"
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
    money = users_db.get(user_id, {}).get("money", 0)
    
    await state.clear()
    
    admin_text = (
        f"🔔 **Yangi Pul Yechish So'rovi!**\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{username or 'yoq'}, ID: `{user_id}`)\n"
        f"🔤 Ism Familiya: **{fullname}**\n"
        f"💳 Karta raqami: **{card_info}**\n"
        f"💰 Summa: **{money:,} so'm**"
    )
    
    try:
        await message.bot.send_message(f"@{ADMIN_USERNAME}", admin_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
        
    await message.answer(
        f"🎉 **So'rovingiz muvaffaqiyatli qabul qilindi!**\n\n"
        f"Ism: {fullname}\n"
        f"Karta: {card_info}\n"
        f"Summa: {money:,} so'm\n\n"
        f"⏳ Adminlar tez orada ma'lumotlarni tekshirib, mablag'ni kartangizga o'tkazib berishadi!",
        reply_markup=get_main_menu(user_id)
    )


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
        
    real_users_count = sum(1 for uid in users_db.keys() if not str(uid).startswith("bot_"))
    total_money = sum(u.get("money", 0) for u in users_db.values())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ / ➖ Balansni O'zgartirish", callback_data="admin_change_score")],
        [InlineKeyboardButton(text="🏠 Asosiy Menyuga Qaytish", callback_data="back_to_menu")]
    ])
    
    text = (
        f"👑 **Admin Panelga Xush Kelibsiz!**\n\n"
        f"📊 **Statistika:**\n"
        f"👥 Haqiqiy foydalanuvchilar: **{real_users_count} ta**\n"
        f"💰 Jami berilgan pul: **{total_money:,} so'm**\n\n"
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
    text = "🆔 Balansini o'zgartirmoqchi bo'lgan foydalanuvchining **Telegram ID** raqamini yuboring:"
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
        current_money = users_db[target_id]["money"]
        await message.answer(f"👤 Foydalanuvchi topildi. Hozirgi puli: **{current_money:,} so'm**\n\nQo'shiladigan pul miqdorini so'mda yuboring (Masalan: `20000` yoki ayirish uchun `-5000`):")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format! Faqat raqam yuboring:")


@dp.message(AdminScoreStates.waiting_for_score_amount)
async def process_admin_score_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_id = data.get("target_user_id")
        await state.clear()
        
        users_db[target_id]["money"] += amount
        new_money = users_db[target_id]["money"]
        
        await message.answer(f"✅ Muvaffaqiyatli o'zgartirildi!\nFoydalanuvchi ID: `{target_id}`\nYangi puli: **{new_money:,} so'm**")
        
        try:
            await message.bot.send_message(target_id, f"🎁 Admin tomonidan balansingiz o'zgartirildi! Hozirgi balansingiz: **{new_money:,} so'm**")
        except:
            pass
    except ValueError:
        await message.answer("❌ Noto'g'ri qiymat! Faqat butun son yuboring:")


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
        "🎯 <b>1. Testlar soni:</b> Jami <b>10 ta savol</b> beriladi.\n\n"
        "🔥 <b>2. Combo Tizimi:</b> Ketma-ket to'g'ri topganingiz sari pul miqdori oshadi (2,000 so'm, 3,500 so'm, 5,000 so'm...). Xato qilsangiz combo yonadi!\n\n"
        "💎 <b>3. Pulni yechish:</b> 50,000 so'm yig'ing va kartangizga o'tkazib oling!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Omad yor bo'lsin! Tugmani bosing va boshlang 👇</i>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()


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
    u_data["money"] = 0
    u_data["combo"] = 0
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
    combo_count = u_data.get("combo", 0)
    combo_text = f" 🔥 Combo: x{combo_count}" if combo_count > 0 else ""
    
    text = (
        f"🎯 **{cat_title} | {q_num}-savol / 10**{combo_text}\n"
        f"⏱ *Vaqt: 30 soniya!*\n\n"
        f"❓ **{q_text}**"
    )
    
    await message.answer(text, reply_markup=reply_markup)
    
    async def timer_countdown():
        await asyncio.sleep(30)
        if user_id in users_db and users_db[user_id]["question_num"] == q_num:
            q_text, options, correct_idx = u_data["current_q_data"]
            u_data["wrong_answers"].append((q_text, options[correct_idx]))
            u_data["combo"] = 0  # Vaqt tugasa combo yonadi
            
            u_data["question_num"] += 1
            try:
                await message.bot.send_message(user_id, "⏰ **Vaqt tugadi!** Combo yondi 😕")
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
        u_data["combo"] = u_data.get("combo", 0) + 1
        combo = u_data["combo"]
        
        # Combo bo'yicha mukofot hisoblash
        if combo == 1:
            earned_money = 2000
        elif combo == 2:
            earned_money = 3500
        else:
            earned_money = 5000  # 3 va undan ortiq combo uchun
            
        u_data["money"] += earned_money
        
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ **To'g'ri! (+{earned_money:,} so'm) 🔥 Combo x{combo}**"
        )
    else:
        u_data["wrong_answers"].append((q_text, options[correct_idx]))
        u_data["combo"] = 0  # Xato qilsa combo 0 ga tushadi
        await callback.message.edit_text(
            callback.message.text + f"\n\n❌ **Noto'g'ri! 😕 (Combo yondi)**\n💡 To'g'ri javob: *{options[correct_idx]}*"
        )
        
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
    final_money = u_data["money"]
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
        f"📊 To'g'ri javoblar: **{final_score} ta**\n"
        f"💰 **Ishlab topgan pulingiz: {final_money:,} so'm**\n"
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
