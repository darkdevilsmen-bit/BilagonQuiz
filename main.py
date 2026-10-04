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
from aiogram.types import CallbackQuery, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, KeyboardButton, BotCommand
import os

# Token Railway muhit o'zgaruvchisidan olinadi
BOT_TOKEN = os.getenv("BOT")

# 🛑 O'ZINGizning KANALINGIZ MA'LUMOTLARINI SHU YERGA YOZING:
CHANNEL_ID = -100xxxxxxxxxx  # O'z kanalingizning ID raqami (masalan: -1001234567890)
CHANNEL_LINK = "https://t.me/SizningKanalingiz"  # O'z kanalingiz havolasi

ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 000000000

dp = Dispatcher()

# Dastlabki ishtirokchilar bazasi
users_db = {
    1001: {"score": 156, "money": 450000, "withdrawn": 150000, "name": "Bekzod To'rayev", "referrals_count": 52, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
    1002: {"score": 141, "money": 400000, "withdrawn": 100000, "name": "Jasurbek Karimov", "referrals_count": 47, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
    1003: {"score": 120, "money": 350000, "withdrawn": 100000, "name": "Dilshod Olimov", "referrals_count": 40, "referred_users": [], "is_contestant": True, "last_quiz_time": None},
}

for i in range(4, 34):
    users_db[1000 + i] = {
        "score": random.randint(10, 90),
        "money": random.randint(20000, 180000),
        "withdrawn": 0,
        "name": f"Ishtirokchi {i}-Ism",
        "referrals_count": random.randint(1, 15),
        "referred_users": [],
        "is_contestant": True,
        "last_quiz_time": None
    }

pending_referrals = {}
approved_users = set()


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
        "title": "🧠 Mantiqiy Savollar (DTM)",
        "questions": [
            ("Qaysi oyda 28 kun bor?", ["Hamma oylarda", "Faqat fevralda", "Faqat iyunda", "Fevral va martda"], 0, "easy"),
            ("O'choqqa o'tin qablasangiz, birinchi bo'lib nimani yoqasiz?", ["O'tinni", "Gugurtni", "Kül ni", "Qog'ozni"], 1, "easy"),
            ("Yerdan ko'tarish oson, lekin uzoqqa otib bo'lmaydi. Bu nima?", ["Tosh", "Tuk", "Qum", "Suv"], 1, "easy"),
            ("5 ta olma bor edi, 3 tasini olib qo'yishdi. Sizda nechta olma bor?", ["2 ta", "3 ta", "5 ta", "1 ta"], 1, "easy"),
            ("O'z egasidan qochib ketmaydigan, lekin doim ergashadigan narsa nima?", ["Soyaboni", "Soya", "Etik", "Do'ppi"], 1, "medium"),
            ("Ikki kishi shaxmat o'ynashdi. Ular 5 ta partiya o'ynashdi va har biri 3 tadan g'alaba qozondi. Bu qanday mumkin?", ["Durang bo'lgan", "Ular birga o'ynashmagan", "Boshqalar bilan o'ynagan", "Xato savol"], 1, "medium"),
            ("Besh aka-ukaning bittadan singlisi bor. Hammasi bo'lib uylar nechta kishi yashaydi?", ["6 kishi", "10 kishi", "5 kishi", "7 kishi"], 0, "medium"),
            ("Qaysi dengizda suv yo'q?", ["Qora dengizda", "Xaritadagi dengizda", "Orol dengizida", "Qizil dengizda"], 1, "medium"),
            ("Qaysi narsa qanchalik ko'p tozalasangiz, shunchalik qorayib boradi?", ["Doska", "Kiyim", "Oyna", "Gilam"], 0, "hard"),
            ("Dunyodagi eng tez harakatlanadigan narsa nima?", ["Ovoz", "Nur (Yorug'lik)", "Shamolsiz havo", "Raketa"], 1, "hard"),
            ("Soat 15:00 da soatning soat mili bilan minut mili orasidagi burchak necha gradus bo'ladi?", ["90 gradus", "75 gradus", "60 gradus", "120 gradus"], 0, "hard"),
            ("Bir kishi o'rmonda yurib, 3 ta olma topdi va ularni yeb qo'ydi. Uning qornida nechta olma qoldi?", ["3 ta", "0 ta", "1 ta", "Ma'lum emas"], 1, "hard"),
            ("Agar 5 ta mushuk 5 ta sichqonni 5 minutda tutsa, 100 ta mushuk 100 ta sichqonni necha minutda tutadi?", ["100 minut", "5 minut", "20 minut", "10 minut"], 1, "hard")
        ]
    },
    "it": {
        "title": "💻 IT & Texnologiyalar (DTM)",
        "questions": [
            ("Python dasturlash tilining asoschisi kim?", ["Guido van Rossum", "Livan Torvalds", "Bill Geyts", "Stiv Jobs"], 0, "easy"),
            ("Kompyuterning 'miyasi' nima deb ataladi?", ["RAM", "Protsessor (CPU)", "Videokarta", "Qattiq disk"], 1, "easy"),
            ("WWW qisqartmasi nimani anglatadi?", ["World Wide Web", "World Web Wide", "Web Wide World", "Wide World Web"], 0, "easy"),
            ("Qaysi biri operatsion tizim emas?", ["Linux", "Windows", "Google Chrome", "macOS"], 2, "easy"),
            ("1 Bayt necha Bitdan iborat?", ["8", "1024", "16", "32"], 0, "medium"),
            ("Internetning otasi deb kim hisoblanadi?", ["Tim Berners-Li", "Vint Cerf", "Mark Zukerberg", "Ilon Mask"], 1, "medium"),
            ("HTML bu nima?", ["Dasturlash tili", "Belgilash tili", "Ma'lumotlar bazasi", "Antivirus"], 1, "medium"),
            ("Eng mashhur ma'lumotlar bazasini boshqarish tizimlaridan biri?", ["SQL Server", "Photoshop", "Notepad", "Word"], 0, "hard"),
            ("Kibernetika fanining asoschisi kim?", ["Norbert Winner", "Alan Turing", "Blez Paskal", "Albert Eynshteyn"], 0, "hard"),
            ("Sun'iy intellekt qisqartmasi qaysi?", ["AI", "IT", "CPU", "UI"], 0, "hard"),
            ("Obyektga yo'naltirilgan dasturlash (OOP) tamoyillariga kirmaydigan tushunchani toping?", ["Inkapsulyatsiya", "Polimorfizm", "Kompilyatsiya", "Merosxo'rlik"], 2, "hard"),
            ("Tarmoqdagi har bir qurilmaning unikal IP manzili necha bitdan iborat (IPv4)?", ["32 bit", "64 bit", "128 bit", "16 bit"], 0, "hard")
        ]
    },
    "biology": {
        "title": "🧬 Biologiya (DTM)",
        "questions": [
            ("Hujayraning energetik markazi qaysi organoid?", ["Ribosoma", "Mitoxondriya", "Lizosoma", "Yadro"], 1, "easy"),
            ("Odam organizmida nechta juft qovurg'a bor?", ["10 ta", "11 ta", "12 ta", "14 ta"], 2, "easy"),
            ("Fotosintez jarayoni qaysi organoidda sodir bo'ladi?", ["Xloroplast", "Vakuola", "Ribosoma", "Sitoplazma"], 0, "easy"),
            ("Odamda qon qaysi a'zoda tozalanadi?", ["Yurak", "Buyrak", "O'pka", "Jigar"], 1, "medium"),
            ("DNK molekulasining tuzilishini kim kashf etgan?", ["Uotson va Krik", "Darvin va Mendel", "Lister va Paster", "Guk va Xuk"], 0, "medium"),
            ("Odam organizmidagi eng yirik bez qaysi?", ["Oshqozon osti bezi", "Jigar", "Qalqonsimon bez", "Buyrak usti bezi"], 1, "medium"),
            ("Achitqi zamburug'lari qaysi guruhga kiradi?", ["Bakteriyalar", "Zamburug'lar", "Viruslar", "Tuban o'simliklar"], 1, "medium"),
            ("Oqsillar monomeri nima?", ["Nukleotid", "Aminokislota", "Glyukoza", "Gliserin"], 1, "hard"),
            ("Odamda necha juft bosh miya nervlari mavjud?", ["10 juft", "12 juft", "24 juft", "31 juft"], 1, "hard"),
            ("Mendel qonunlari qaysi fanga tegishli?", ["Genetika", "Anatomiya", "Ekologiya", "Sitologiya"], 0, "hard"),
            ("Odam skeletida nechta suyak mavjud?", ["206 ta", "210 ta", "198 ta", "220 ta"], 0, "medium"),
            ("Mitoxondriyada qanday jarayon kechadi?", ["Oqsillar sintezi", "ATF sintezi (energiya hosil bo'lishi)", "Lipidlar parchalanishi", "RNK transkripsiyasi"], 1, "hard")
        ]
    },
    "chemistry": {
        "title": "🧪 Kimyo (DTM)",
        "questions": [
            ("Suvning kimyoviy formulasi qanday?", ["H2O", "CO2", "NaCl", "NH3"], 0, "easy"),
            ("Mendeleyev jadvalidagi 1-element qaysi?", ["Geliy", "Vodorod", "Kislorod", "Azot"], 1, "easy"),
            ("Osh tuzining kimyoviy nomi nima?", ["Natriy xlorid", "Kaliy permanganat", "Kalsiy karbonat", "Mis sulfat"], 0, "easy"),
            ("Atmosferada eng ko'p tarqalgan gaz qaysi?", ["Kislorod", "Azot", "Argon", "Uglerod angidrid"], 1, "medium"),
            ("Kislota va ishqor reaksiyaga kirishganda nima hosil bo'ladi?", ["Tuz va suv", "Faqat tuz", "Faqat suv", "Gaz"], 0, "medium"),
            ("Oddiy sharoitda suyuq holatda bo'ladigan yagona metall qaysi?", ["Temir", "Simob", "Oltin", "Rux"], 1, "medium"),
            ("Sulfat kislotaning formulasi qanday?", ["HCl", "H2SO4", "HNO3", "H3PO4"], 1, "medium"),
            ("Uglerodning allotropik shakl o'zgarishi qaysi?", ["Olmos va grafit", "Oltin va kumush", "Temir va cho'yan", "Kislorod va ozon"], 0, "hard"),
            ("Kislotali yomg'irlarning paydo bo'lishiga asosiy sababchi qaysi gaz?", ["Azot oksid", "Oltingugurt dioksidi", "Metan", "Neon"], 1, "hard"),
            ("Elektrolitik dissosilanish nazariyasini kim yaratgan?", ["Arrhenius", "Mendeleyev", "Lomonosov", "Butlerov"], 0, "hard"),
            ("Natriy gidroksidning trivial (oddiy) nomi nima?", ["Kustik soda", "Söndirilgan ohak", "osh tuzi", "Choy soda"], 0, "hard"),
            ("Alkanlarning umumiy formulasi qaysi?", ["CnH2n", "CnH2n+2", "CnH2n-2", "CnH2n-6"], 1, "hard")
        ]
    },
    "history": {
        "title": "🏛 Tarix & Geografiya (DTM)",
        "questions": [
            ("Amir Temur qaysi yilda tavallud topgan?", ["1336-yil", "1365-yil", "1405-yil", "1219-yil"], 0, "easy"),
            ("O'zbekistonning poytaxti qaysi shahar?", ["Samarqand", "Buxoro", "Toshkent", "Xiva"], 2, "easy"),
            ("Dunyodagi eng katta okean qaysi?", ["Tinch okeani", "Atlantika okeani", "Hind okeani", "Shimoliy Muz okeani"], 0, "easy"),
            ("Buyuk Ipak yo'li qaysi qit'alarni bog'lagan?", ["Osiyo va Yevropa", "Afrika va Amerika", "Avstraliya va Antarktida", "Faqat Osiyo"], 0, "medium"),
            ("Yer yuzidagi eng uzun daryo qaysi?", ["Nil", "Amazonka", "Sirdaryo", "Amudaryo"], 0, "medium"),
            ("Alisher Navoiy qaysi asrda yashab ijod qilgan?", ["XV asr", "XIV asr", "XVI asr", "XII asr"], 0, "medium"),
            ("Fransiyaning poytaxti qaysi shahar?", ["Berlin", "Parij", "Madrid", "Rim"], 1, "medium"),
            ("Dunyodagi eng baland tog' cho'qqisi qaysi?", ["Everest", "Elbrus", "Kilimanjaro", "Chimyon"], 0, "hard"),
            ("Boburiylar sulolasining asoschisi kim?", ["Zahiriddin Muhammad Bobur", "Amir Temur", "Mirzo Ulug'bek", "Temur Malik"], 0, "hard"),
            ("Yer yuzida nechta okean bor?", ["4 ta", "5 ta", "6 ta", "3 ta"], 1, "hard"),
            ("Qaysi sulola davrida O'zbekiston hududida Islom dini davlat dini deb e'lon qilindi?", ["Somoniylar", "Qoraxoniylar", "G'aznaviylar", "Temuriylar"], 0, "hard"),
            ("Dunyodagi eng chuqur ko'l qaysi?", ["Baykal", "Viktoriya", "Kaspiskiy", "Tanganika"], 0, "medium")
        ]
    }
}


def get_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🚀 Viktorinani Boshlash")],
        [KeyboardButton(text="💳 Balans"), KeyboardButton(text="🎁 Kunlik Bonus")],
        [KeyboardButton(text="🏆 Top Reyting"), KeyboardButton(text="🔗 Referal Tizimi")],
        [KeyboardButton(text="🏆 Konkurs"), KeyboardButton(text="📜 O'yin Qoidalari")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def process_referral_reward(bot: Bot, user_id: int, user_name: str):
    if user_id in pending_referrals:
        referrer_id = pending_referrals[user_id]
        if referrer_id in users_db and referrer_id != user_id:
            if not any(u.get("id") == user_id for u in users_db[referrer_id].get("referred_users", [])):
                users_db[referrer_id]["referred_users"].append({"id": user_id, "name": user_name})
                users_db[referrer_id]["referrals_count"] += 3
                users_db[referrer_id]["score"] += 3
                users_db[referrer_id]["money"] += 10000
                
                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 **Ajoyib yangilik!** Siz orqali foydalanuvchi (**{user_name}**) qo'shildi!\n"
                        f"🎁 Sizga **+3 ball** va **+10,000 so'm** qo'shildi! 🚀"
                    )
                except:
                    pass
        pending_referrals.pop(user_id, None)


@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    user_id = request.from_user.id
    approved_users.add(user_id)
    user_name = request.from_user.full_name
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


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    if user_id not in users_db:
        users_db[user_id] = {
            "score": 0, "money": 0, "withdrawn": 0, "question_num": 1,
            "game_questions": [], "wrong_answers": [], "referrals_count": 0,
            "referred_users": [], "last_bonus": None, "category": "logic",
            "name": user_name, "timer_task": None, "combo": 0,
            "in_game": False, "is_contestant": False, "last_quiz_time": None
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
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check_joined")]
        ])
        text = (
            f"✨ **Salom, {html.bold(user_name)}!**\n\n"
            f"📢 Botdan foydalanish uchun avval kanalimizga a'zo bo'ling:\n\n"
            f"👇 Tugmani bosing, so'ngra **'Obunani Tekshirish'** tugmasini bosing:"
        )
        await message.answer(text, reply_markup=keyboard)
        return

    await process_referral_reward(message.bot, user_id, user_name)

    text = (
        f"✨ **Salom, {html.bold(user_name)}!**\n\n"
        f"🎯 **«Bilag'on Quiz»** botiga xush kelibsiz!\n\n"
        f"⬇ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_reply_keyboard())


@dp.callback_query(F.data == "check_joined")
async def check_joined_callback(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    
    is_member = await check_user_subscription(callback.bot, user_id)
    if not is_member:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
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
        f"⬇️ Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await callback.message.answer(text, reply_markup=get_reply_keyboard())


async def verify_access_middleware_msg(message: Message) -> bool:
    user_id = message.from_user.id
    is_member = await check_user_subscription(message.bot, user_id)
    if not is_member:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check_joined")]
        ])
        await message.answer(
            "📢 Botdan foydalanish uchun avval kanalimizga a'zo bo'ling:\n\n👇 Tugmani bosing:",
            reply_markup=keyboard
        )
        return False
    return True


@dp.message(F.text == "🚀 Viktorinani Boshlash")
async def text_select_category(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})
    
    if u_data.get("in_game", False):
        await message.answer("⚠ Sizda hozir faol o'yin ketmoqda! Avval uni oxirigacha tugating 🛑")
        return

    last_time = u_data.get("last_quiz_time")
    if last_time:
        diff_hours = (datetime.datetime.now() - last_time).total_seconds() / 3600
        if diff_hours < 24:
            await message.answer(
                f"⏳ Siz oxirgi testni 24 soat ichida yechgansiz!\n"
                f"🔄 Testni qaytadan boshlash uchun **3 ta do'st** qo'shishingiz kerak yoki 24 soat kutishingiz lozim."
            )
            return

    keyboard_buttons = []
    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard_buttons.append([InlineKeyboardButton(text=cat_val["title"], callback_data=f"cat_{cat_key}")])
    
    text = "📚 **DTM test yo'nalishini tanlang:**"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))


@dp.callback_query(F.data.startswith("cat_"))
async def start_quiz_game(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    cat_key = callback.data.split("_")[1]
    
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": callback.from_user.full_name, "combo": 0, "in_game": False}
        
    questions = random.sample(CATEGORIES_DB[cat_key]["questions"], 10)
    users_db[user_id]["game_questions"] = questions
    users_db[user_id]["question_num"] = 0
    users_db[user_id]["correct_count"] = 0
    users_db[user_id]["in_game"] = True
    users_db[user_id]["category"] = cat_key
    
    await callback.answer()
    await send_quiz_question(callback.message, user_id)


async def send_quiz_question(message: Message, user_id: int):
    u_data = users_db[user_id]
    q_idx = u_data["question_num"]
    questions = u_data["game_questions"]
    
    if q_idx >= len(questions):
        corrects = u_data.get("correct_count", 0)
        u_data["in_game"] = False
        u_data["last_quiz_time"] = datetime.datetime.now()
        
        if corrects >= 10:
            u_data["score"] += 5
            await message.answer(
                f"🎉 **Tabriklaymiz! Siz 10 ta DTM testining barchasiga to'g'ri javob berdingiz!**\n"
                f"🎁 Hisobingizga **+5 ball** qo'shildi! 🚀"
            )
        else:
            await message.answer(
                f"🏁 **Test yakunlandi!**\n"
                f"📊 To'g'ri javoblar: {corrects}/10\n"
                f"💡 5 ball olish uchun 10 ta savolning barchasiga to'g'ri topishingiz kerak."
            )
        return

    q_text, options, correct_opt, level = questions[q_idx]
    level_icon = "🟢 Easy" if level == "easy" else ("🟡 Medium" if level == "medium" else "🔴 Hard")
    
    keyboard_buttons = []
    for idx, opt in enumerate(options):
        keyboard_buttons.append([InlineKeyboardButton(text=opt, callback_data=f"ans_{idx}_{correct_opt}")])
        
    await message.answer(
        f"📝 **Savol {q_idx + 1}/10** | Daraja: {level_icon}\n\n{q_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )


@dp.callback_query(F.data.startswith("ans_"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    if user_id not in users_db or not users_db[user_id].get("in_game", False):
        await callback.answer("⚠️ Faol o'yin topilmadi!", show_alert=True)
        return
        
    _, chosen, correct = callback.data.split("_")
    if int(chosen) == int(correct):
        users_db[user_id]["correct_count"] = users_db[user_id].get("correct_count", 0) + 1
        await callback.answer("✅ To'g'ri!")
    else:
        await callback.answer("❌ Noto'g'ri!")
        
    users_db[user_id]["question_num"] += 1
    try:
        await callback.message.delete()
    except:
        pass
        
    await send_quiz_question(callback.message, user_id)


@dp.message(F.text == "💳 Balans")
async def text_show_balance(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "name": message.from_user.full_name, "combo": 0, "in_game": False, "is_contestant": False}
        
    u_data = users_db[user_id]
    score = u_data.get("score", 0)
    money = u_data.get("money", 0)
    withdrawn = u_data.get("withdrawn", 0)
    refs = u_data.get("referrals_count", 0)
    
    bot_username = (await message.bot.get_me()).username
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Pulni Yechib Olish", callback_data="withdraw_money")]
    ])
    await message.answer(text, reply_markup=keyboard)


@dp.message(F.text == "🎁 Kunlik Bonus")
async def text_daily_bonus(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "name": message.from_user.full_name, "combo": 0, "in_game": False, "is_contestant": False}
        
    now = datetime.datetime.now()
    last_bonus = users_db[user_id].get("last_bonus")
    
    if last_bonus and (now - last_bonus).total_seconds() < 86400:
        remaining_hours = int((86400 - (now - last_bonus).total_seconds()) // 3600)
        await message.answer(f"⏳ Siz kunlik bonusni allaqachon olgansiz! Keyingi bonus {remaining_hours} soatdan keyin ochiladi.")
        return
        
    bonus_score = random.randint(1, 3)
    bonus_money = bonus_score * 2000
    users_db[user_id]["score"] += bonus_score
    users_db[user_id]["money"] += bonus_money
    users_db[user_id]["last_bonus"] = now
    
    await message.answer(f"🎉 Tabriklaymiz! Kunlik bonus: +{bonus_score} ball va +{bonus_money:,} so'm! 🎁")


@dp.message(F.text == "🏆 Top Reyting")
async def text_top_board(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    sorted_users = sorted(
        users_db.values(), 
        key=lambda x: (x.get("score", 0), x.get("money", 0) + x.get("withdrawn", 0)), 
        reverse=True
    )[:10]
    
    text = "🏆 **Top 10 Liderlar Reytingi**\n📊 *(Ballar va umumiy balans bo'yicha)*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, u_data in enumerate(sorted_users, 1):
        name = u_data.get("name", "Foydalanuvchi")
        score = u_data.get("score", 0)
        money = u_data.get("money", 0)
        withdrawn = u_data.get("withdrawn", 0)
        total_earned = money + withdrawn
        
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"{idx}."))
        text += f"{medal} **{name}**\n   🏆 Ball: {score} | 💰 Pul: {total_earned:,} so'm\n\n"
        
    await message.answer(text)


@dp.message(F.text == "🔗 Referal Tizimi")
async def text_referral_info(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    user_id = message.from_user.id
    bot_username = (await message.bot.get_me()).username
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
        f"🎁 Har bir do'st uchun: **+3 ball va +10,000 so'm** beriladi!\n"
        f"{list_text}\n"
        f"📋 **Sizning taklif havolangiz:**\n`{ref_link}`\n"
    )
    await message.answer(text)


@dp.message(F.text == "🏆 Konkurs")
async def text_contest_info(message: Message, state: FSMContext) -> None:
    if not await verify_access_middleware_msg(message):
        return
    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})
    is_contestant = u_data.get("is_contestant", False)
    
    keyboard_buttons = []
    if not is_contestant:
        keyboard_buttons.append([InlineKeyboardButton(text="✍️ Konkursga qo'shilish", callback_data="join_contest")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = (
        f"🏆 **Katta Konkurs!**\n\n"
        f"🎁 Konkurs sovrini: **300,000 so'm!**\n"
        f"📌 **Shartlar:** Eng ko'p odam taklif qilgan ishtirokchi konkurs g'olibi bo'ladi va 300,000 so'm pul mukofotini qo'lga kiritadi!\n\n"
    )
    
    if is_contestant:
        contestants = sorted(
            [u for u in users_db.values() if u.get("is_contestant", False)],
            key=lambda x: x.get("referrals_count", 0),
            reverse=True
        )
        
        total_contestants = len(contestants)
        user_rank = 33
        for idx, c in enumerate(contestants, 1):
            if c.get("name") == u_data.get("name"):
                user_rank = idx
                break
        
        top_1_name = contestants[0].get("name", "Bekzod To'rayev") if contestants else "Bekzod To'rayev"
        top_1_refs = contestants[0].get("referrals_count", 52) if contestants else 52
        
        text += (
            f"🎉 **Tabriklaymiz, {u_data.get('name')}! Siz konkurs a'zosisiz!**\n\n"
            f"👥 Jami konkurs a'zolari: **{total_contestants} ta**\n"
            f"📊 Sizning o'rningiz: **{user_rank}-o'rin**\n"
            f"🥇 1-o'rinda: **{top_1_name}** ({top_1_refs} ta referal / ball)\n"
        )
    else:
        text += "❌ **Siz hali konkursga qo'shilmagansiz!** Qo'shilish uchun pastdagi tugmani bosing:"
        
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "join_contest")
async def join_contest_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ContestStates.waiting_for_name)
    await callback.message.answer("1️⃣ Iltimos, konkurs uchun **Ismingizni** yuboring:")


@dp.message(ContestStates.waiting_for_name)
async def process_contest_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(contest_name=name)
    await state.set_state(ContestStates.waiting_for_surname)
    await message.answer("2️⃣ Endi **Familiyangizni** yuboring:")


@dp.message(ContestStates.waiting_for_surname)
async def process_contest_surname(message: Message, state: FSMContext) -> None:
    surname = message.text.strip()
    data = await state.get_data()
    name = data.get("contest_name")
    full_contestant_name = f"{name} {surname}"
    
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"score": 0, "money": 0, "withdrawn": 0, "question_num": 1, "game_questions": [], "wrong_answers": [], "referrals_count": 0, "referred_users": [], "last_bonus": None, "combo": 0, "in_game": False}
        
    users_db[user_id]["name"] = full_contestant_name
    users_db[user_id]["is_contestant"] = True
    
    await state.clear()
    
    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    contestants = sorted(
        [u for u in users_db.values() if u.get("is_contestant", False)],
        key=lambda x: x.get("referrals_count", 0),
        reverse=True
    )
    total_contestants = len(contestants)
    
    user_rank = 33
    for idx, c in enumerate(contestants, 1):
        if c.get("name") == full_contestant_name:
            user_rank = idx
            break
            
    top_1_name = contestants[0].get("name", "Bekzod To'rayev") if contestants else "Bekzod To'rayev"
    top_1_refs = contestants[0].get("referrals_count", 52) if contestants else 52
    
    success_text = (
        f"🎉 **Tabriklaymiz, {full_contestant_name}! Siz konkursga qo'shildingiz!**\n\n"
        f"👥 Jami konkurs a'zolari: **{total_contestants} ta**\n"
        f"📊 Sizning hozirgi o'rningiz: **{user_rank}-o'rin**\n"
        f"🥇 1-o'rinda: **{top_1_name}** ({top_1_refs} ta referal)\n\n"
        f"🔗 **Sizning shaxsiy referal havolangiz:**\n`{ref_link}`\n"
    )
    await message.answer(success_text, reply_markup=get_reply_keyboard())


@dp.message(F.text == "📜 O'yin Qoidalari")
async def text_rules(message: Message, state: FSMContext) -> None:
    text = (
        f"📜 **O'yin Qoidalari:**\n\n"
        f"1. DTM testlariga to'g'ri javob bering (10 ta test to'g'ri topilsa +5 ball).\n"
        f"2. Testni qayta ishlash uchun 3 ta do'st qo'shish kerak yoki 24 soat kutish lozim.\n"
        f"3. Referal orqali har bir do'st uchun +3 ball va 10,000 so'm beriladi.\n"
        f"4. Konkursda g'olib bo'lish uchun eng ko'p odam taklif qiling!"
    )
    await message.answer(text)


@dp.callback_query(F.data == "withdraw_money")
async def withdraw_money_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    u_data = users_db.get(user_id, {"score": 0, "money": 0})
    score = u_data.get("score", 0)
    
    if score < 50:
        needed_more = 50 - score
        text = (
            f"❌ **Mablag'ni yechib olish imkonsiz!**\n\n"
            f"⚠️ Pulni yechib olish uchun hisobingizda kamida **50 ball** bo'lishi kerak!\n"
            f"📊 Hozirgi ballingiz: **{score} ta ball** (Yana {needed_more} ball kerak)\n"
        )
        await callback.message.answer(text)
        return

    await state.set_state(WithdrawStates.waiting_for_name)
    await callback.message.answer("📝 Pulni o'tkazib berishimiz uchun iltimos, **Ism va Familiyangizni** kiriting:")


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    await state.update_data(user_fullname=full_name)
    await state.set_state(WithdrawStates.waiting_for_card)
    await message.answer("💳 Endi 16 xonali **Karta raqamingizni** yuboring:")


@dp.message(WithdrawStates.waiting_for_card)
async def process_withdraw_card(message: Message, state: FSMContext) -> None:
    card_info = message.text.strip()
    data = await state.get_data()
    fullname = data.get("user_fullname")
    user_id = message.from_user.id
    username = message.from_user.username
    money = users_db.get(user_id, {}).get("money", 0)
    
    users_db[user_id]["withdrawn"] = users_db[user_id].get("withdrawn", 0) + money
    withdrawn_amount = money
    users_db[user_id]["money"] = 0
    users_db[user_id]["score"] = 0
    
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
        
    await message.answer(f"🎉 **So'rovingiz qabul qilindi!** Adminlar tez orada ko'rib chiqishadi.")


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
        
    contestants = [u for u in users_db.values() if u.get("is_contestant", False)]
    contestants_list_text = ""
    for idx, c in enumerate(contestants[:15], 1):
        contestants_list_text += f"{idx}. {c.get('name')} — {c.get('referrals_count')} ball/referal\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Xabar Tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ / ➖ Balansni O'zgartirish", callback_data="admin_change_score")]
    ])
    
    text = (
        f"👑 **Admin Panel & Konkurs Ishtirokchilari**\n\n"
        f"👥 Jami ishtirokchilar: **{len(contestants)} ta**\n"
        f"📊 **Top Ishtirokchilar va Ballari:**\n{contestants_list_text}\n"
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
    await callback.message.answer("🆔 Balansini o'zgartirmoqchi bo'lgan foydalanuvchining **Telegram ID** raqamini yuboring:")


@dp.message(AdminScoreStates.waiting_for_user_id)
async def process_admin_user_id(message: Message, state: FSMContext) -> None:
    try:
        target_id = int(message.text.strip())
        if target_id not in users_db:
            await message.answer("❌ Foydalanuvchi topilmadi! Qaytadan ID yuboring:")
            return
        await state.update_data(target_user_id=target_id)
        await state.set_state(AdminScoreStates.waiting_for_score_amount)
        current_money = users_db[target_id]["money"]
        await message.answer(f"👤 Topildi. Hozirgi puli: **{current_money:,} so'm**\n\nQo'shiladigan pul miqdorini yuboring:")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID format!")


@dp.message(AdminScoreStates.waiting_for_score_amount)
async def process_admin_score_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_id = data.get("target_user_id")
        await state.clear()
        
        users_db[target_id]["money"] += amount
        new_money = users_db[target_id]["money"]
        
        await message.answer(f"✅ Muvaffaqiyatli! Yangi puli: **{new_money:,} so'm**")
    except ValueError:
        await message.answer("❌ Noto'g'ri qiymat!")


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username
    is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower())
    if not is_admin:
        return
        
    await state.set_state(BroadcastStates.waiting_for_broadcast_message)
    await callback.message.answer("📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:")


@dp.message(BroadcastStates.waiting_for_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    success = 0
    failed = 0
    
    status_msg = await message.answer("📤 Xabar tarqatish boshlandi...")
    
    for uid in users_db.keys():
        if isinstance(uid, str) or uid < 1000:
            continue
        try:
            await message.send_copy(chat_id=int(uid))
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
            
    await status_msg.edit_text(f"✅ Tarqatildi: {success} ta, Xatolik: {failed} ta")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Qaytadan ishga tushirish / Asosiy menyu")
    ])
    
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
