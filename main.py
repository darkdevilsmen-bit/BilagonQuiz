Import asyncio
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

BOT_TOKEN = "8963661833:AAERa76qlzRiljTUXkqxFxeDEg6_MJKQ44k"
CHANNEL_ID = -1004317372728  # Sizning yopiq kanalingizning aniq ID raqami
CHANNEL_LINK = "https://t.me/+llFGqeWBsuZlMGYy"
ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 000000000

dp = Dispatcher()

users_db = {
    "bot_1": {"score": 85, "money": 205000, "withdrawn": 150000, "name": "Bekzod To'rayev", "referrals_count": 0, "referred_users": []},
    "bot_2": {"score": 72, "money": 164000, "withdrawn": 100000, "name": "Jasurbek Karimov", "referrals_count": 0, "referred_users": []},
    "bot_3": {"score": 65, "money": 146000, "withdrawn": 100000, "name": "Dilshod Olimov", "referrals_count": 0, "referred_users": []},
    "bot_4": {"score": 58, "money": 124000, "withdrawn": 100000, "name": "Sardor Rahimov", "referrals_count": 0, "referred_users": []},
    "bot_5": {"score": 54, "money": 112000, "withdrawn": 50000, "name": "Azizbek Toshmatov", "referrals_count": 0, "referred_users": []},
    "bot_6": {"score": 51, "money": 100000, "withdrawn": 50000, "name": "Oybek Sharipov", "referrals_count": 0, "referred_users": []},
    "bot_7": {"score": 48, "money": 94000, "withdrawn": 50000, "name": "Bobur Mirzayev", "referrals_count": 0, "referred_users": []},
    "bot_8": {"score": 42, "money": 84000, "withdrawn": 0, "name": "Madina Rahimova", "referrals_count": 0, "referred_users": []},
    "bot_9": {"score": 35, "money": 70000, "withdrawn": 0, "name": "Ziyoda Saidova", "referrals_count": 0, "referred_users": []},
    "bot_10": {"score": 28, "money": 56000, "withdrawn": 0, "name": "Shaxzodbek", "referrals_count": 0, "referred_users": []}
}

pending_referrals = {}
approved_users = set()


class WithdrawStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_card = State()


class BroadcastStates(StatesGroup):
    waiting_for_broadcast_message = State()


class AdminScoreStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_score_amount = State()


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
            if not any(u["id"] == user_id for u in users_db[referrer_id]["referred_users"]):
                users_db[referrer_id]["referred_users"].append({"id": user_id, "name": user_name})
                users_db[referrer_id]["referrals_count"] += 1
                users_db[referrer_id]["score"] += 5
                users_db[referrer_id]["money"] += 10000
                
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
    approved_users.add(user_id)
    user_name = request.from_user.full_name
    try:
        # await request.approve()  # Avtomatik tasdiqlash o'chirildi
        pass
    except:
        pass
    await process_referral_reward(request.bot, user_id, user_name)


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
            "withdrawn": 0,
            "question_num": 1,
            "game_questions": [],
            "wrong_answers": [],
            "referrals_count": 0,
            "referred_users": [],
            "last_bonus": None,
            "category": "logic",
            "name": user_name,
            "timer_task": None,
            "combo": 0,
            "in_game": False
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

    is_member = await check_user_subscription(message.bot, user_id)
    if not is_member:
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

    await process_referral_reward(message.bot, user_id, user_name)

    text = (
        f"✨ **Salom, {html.bold(user_name)}!**\n\n"
        f"🎯 **«Bilag'on Quiz»** botiga xush kelibsiz!\n\n"
        f"🔥 **Combo Tizimi:** Ketma-ket to'g'ri topganingiz sari mukofot oshib boradi (2,000 so'mdan 5,000+ so'mgacha!) 🚀\n\n"
        f"⬇️ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_main_menu(user_id))


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    
    is_member = await check_user_subscription(callback.bot, user_id)
    if not is_member:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz yoki so'rov yubormadingiz! Iltimos, tugmani bosib obuna bo'ling.", show_alert=True)
        return

    approved_users.add(user_id)
    await callback.answer("✅ Obuna tasdiqlandi!")
    await process_referral_reward(callback.bot, user_id, user_name)
    
    try:
        await callback.message.delete()
    except:
        pass
        
    text = (
        f"✨ **Salom, {html.bold(user_name)}!**\n\n"
        f"🎯 **«Bilag'on Quiz»** botiga xush kelibsiz!\n\n"
        f"🔥 **Combo Tizimi:** Ketma-ket to'g'ri topganingiz sari mukofot oshib boradi (2,000 so'mdan 5,000+ so'mgacha!) 🚀\n\n"
        f"⬇️ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await callback.message.answer(text, reply_markup=get_main_menu(user_id))


async def verify_access_middleware(callback: CallbackQuery) -> bool:
    user_id = callback.from_user.id
    is_member = await check_user_subscription(callback.bot, user_id)
    if not is_member:
        await callback.answer("❌ Botdan foydalanish uchun avval kanalimizga a'zo bo'lishingiz kerak!", show_alert=True)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish / So'rov Yuborish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check_joined")]
        ])
        try:
            await callback.message.edit_text(
                "📢 Botdan foydalanish uchun avval rasmiy kanalimizga a'zo bo'ling:\n\n👇 Tugmani bosing:",
                reply_markup=keyboard
            )
        except:
            pass
        return False
    return True


@dp.callback_query(F.data == "select_category")
async def select_category_handler(callback: CallbackQuery) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
    user_id = callback.from_user.id
    
    if user_id in users_db and users_db[user_id].get("in_game", False):
        await callback.message.answer("⚠ Sizda hozir faol o'yin ketmoqda! Avval uni oxirigacha tugating 🛑")
        return

    keyboard_buttons = []
    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard_buttons.append([InlineKeyboardButton(text=cat_val["title"], callback_data=f"cat_{cat_key}")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")])
    
    text = "📚 **Test yo'nalishini tanlang:**"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))


@dp.callback_query(F.data.startswith("cat_"))
async def set_category_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
    user_id = callback.from_user.id
    cat_key = callback.data.split("_")[1]
    
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": callback.from_user.full_name, "combo": 0, "in_game": False}
        
    if users_db[user_id].get("in_game", False):
        await callback.message.answer("⚠️ Hozir boshqa test ishlamoqda! Avval shuni tugating 🛑")
        return

    users_db[user_id]["category"] = cat_key
    await start_quiz_session_processed(callback.message, user_id)


@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_handler(callback: CallbackQuery) -> None:
    if not await verify_access_middleware(callback):
        return
    user_id = callback.from_user.id
    if user_id in users_db and users_db[user_id].get("in_game", False):
        await callback.answer("⚠️ O'yin paytida bonus olib bo'lmaydi!", show_alert=True)
        return

    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": callback.from_user.full_name, "combo": 0, "in_game": False}
        
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
    
    await callback.answer(f"🎉 Tabriklaymiz! Kunlik bonus: +{bonus_score} ball va +{bonus_money:,} so'm! 🎁", show_alert=True)
    
    text = "🏠 **Asosiy Menyu:**\n\nKerakli bo'limni tanlang:"
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu(user_id))
    except:
        pass


@dp.callback_query(F.data == "top_board")
async def top_board_handler(callback: CallbackQuery) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
    sorted_users = sorted(users_db.items(), key=lambda x: (x[1].get("money", 0) + x[1].get("withdrawn", 0)), reverse=True)[:10]
    
    text = "🏆 **Top 10 Liderlar Reytingi**\n📊 *(To'plagan ballar, jami pul va yechib olganlar)*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, (u_id, u_data) in enumerate(sorted_users, 1):
        name = u_data.get("name", "Foydalanuvchi")
        score = u_data.get("score", 0)
        total_earned = u_data.get("money", 0) + u_data.get("withdrawn", 0)
        withdrawn = u_data.get("withdrawn", 0)
        
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        text += f"{medal} **{name}**\n   🏆 {score} ball | 💰 Jami: {total_earned:,} so'm | 💸 Yechgan: {withdrawn:,} so'm\n\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query(F.data == "referral_info")
async def referral_info_handler(callback: CallbackQuery) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀ Orqaga", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query(F.data == "my_balance")
async def show_balance(callback: CallbackQuery) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
    user_id = callback.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "name": callback.from_user.full_name, "combo": 0, "in_game": False}
        
    u_data = users_db[user_id]
    score = u_data.get("score", 0)
    money = u_data.get("money", 0)
    withdrawn = u_data.get("withdrawn", 0)
    refs = u_data.get("referrals_count", 0)
    
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        f"💎 **Foydalanuvchi Kabineti & Balans**\n\n"
        f"👤 ID: `{user_id}`\n"
        f"👥 Taklif qilingan do'stlar: **{refs} ta**\n"
        f"🏆 Jami to'plagan ballaringiz: **{score} ta ball**\n"
        f"💰 **Hozirgi asosiy balans: {money:,} so'm**\n"
        f"💸 **Allaqachon yechib olganingiz: {withdrawn:,} so'm**\n\n"
        f"🔗 **Sizning referal havolangiz:**\n`{ref_link}`\n"
    )
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="💵 Pulni Yechib Olish", callback_data="withdraw_money")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_menu")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))


@dp.callback_query(F.data == "withdraw_money")
async def withdraw_money_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if not await verify_access_middleware(callback):
        return
    await callback.answer()
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
        return

    await state.set_state(WithdrawStates.waiting_for_name)
    text = (
        f"✅ **Tabriklaymiz! Balansingiz yetarli ({money:,} so'm).**\n\n"
        f"📝 Pulni o'tkazib berishimiz uchun iltimos, **Ism va Familiyangizni** kiriting:"
    )
    await callback.message.edit_text(text)


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(message: Message, state: FSMContext) -> None:
    if not await check_user_subscription(message.bot, message.from_user.id):
        await message.answer("❌ Avval kanalimizga a'zo bo'ling!")
        return
    full_name = message.text.strip()
    await state.update_data(user_fullname=full_name)
    
    await state.set_state(WithdrawStates.waiting_for_card)
    await message.answer("💳 Endi 16 xonali **Karta raqamingizni** (yoki karta turini, masalan: *Uzcard/Humo*) yuboring:")


@dp.message(WithdrawStates.waiting_for_card)
async def process_withdraw_card(message: Message, state: FSMContext) -> None:
    if not await check_user_subscription(message.bot, message.from_user.id):
        await message.answer("❌ Avval kanalimizga a'zo bo'ling!")
        return
    card_info = message.text.strip()
    data = await state.get_data()
    fullname = data.get("user_fullname")
    user_id = message.from_user.id
    username = message.from_user.username
    money = users_db.get(user_id, {}).get("money", 0)
    
    users_db[user_id]["withdrawn"] = users_db[user_id].get("withdrawn", 0) + money
    withdrawn_amount = money
    users_db[user_id]["money"] = 0
    
    await state.clear()
    
    admin_text = (
        f"🔔 **Yangi Pul Yechish So'rovi!**\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{username or 'yoq'}, ID: `{user_id}`)\n"
        f"🔤 Ism Familiya: **{fullname}**\n"
        f"💳 Karta raqami: **{card_info}**\n"
        f"💰 Summa: **{withdrawn_amount:,} so'm**"
    )
    
    try:
        await message.bot.send_message(f"@{ADMIN_USERNAME}", admin_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
        
    await message.answer(
        f"🎉 **So'rovingiz muvaffaqiyatli qabul qilindi!**\n\n"
        f"Ism: {fullname}\n"
        f"Karta: {card_info}\n"
        f"Summa: {withdrawn_amount:,} so'm\n\n"
        f"⏳ Adminlar tez orada ma'lumotlarni tekshirib, mablag'ni kartangizga o'tkazib berishadi!",
        reply_markup=get_main_menu(user_id)
    )


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
    total_money = sum(u.get("money", 0) + u.get("withdrawn", 0) for u in users_db.values())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ / ➖ Balansni O'zgartirish", callback_data="admin_change_score")],
        [InlineKeyboardButton(text="🏠 Asosiy Menyuga Qaytish", callback_data="back_to_menu")]
    ])
    
    text = (
        f"👑 **Admin Panelga Xush Kelibsiz!**\n\n"
        f"📊 **Statistika:**\n"
        f"👥 Haqiqiy foydalanuvchilar: **{real_users_count} ta**\n"
        f"💰 Jami aylanma pul: **{total_money:,} so'm**\n\n"
        f"Kerakli amalni tanlang:"
    )
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "admin_change_score")
async def admin_change_score_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username
    is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower())
    if not is_admin:
        return
        
    await state.set_state(AdminScoreStates.waiting_for_user_id)
    text = "🆔 Balansini o'zgartirmoqchi bo'lgan foydalanuvchining **Telegram ID** raqamini yuboring:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]])
    await callback.message.edit_text(text, reply_markup=keyboard)


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
    await callback.answer()
    user_id = callback.from_user.id
