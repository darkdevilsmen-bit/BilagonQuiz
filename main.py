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
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)

# ============================================================
# BOT SOZLAMALARI
# ============================================================

# Tokenni kodga yozmang.
# Render/Replit Secrets/Environment Variables ichida:
# BOT_TOKEN = BotFather bergan yangi token
BOT_TOKEN = os.getenv("8963661833:AAGGL_SPYda_dWR3zlHU5_5XnWCE7nupXRw", "").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Render/Replit Secrets ichiga BOT_TOKEN qo'ying."
    )

# Foydalanuvchi JOIN REQUEST yuborishi kerak bo'lgan kanal.
# Bot bu requestni AVTOMATIK TASDIQLAMAYDI.
REQUIRED_CHANNEL = "@Auto_Captions"
CHANNEL_ID = -1004317372728
CHANNEL_LINK = "https://t.me/+llFGqeWBsuZlMGYy"

ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 0  # O'zingizning Telegram raqamli ID'ingizni yozishingiz mumkin.

dp = Dispatcher()

# ============================================================
# BAZA
# ============================================================

users_db = {
    1001: {
        "score": 156,
        "money": 450000,
        "withdrawn": 150000,
        "name": "Bekzod To'rayev",
        "referrals_count": 52,
        "referred_users": [],
        "is_contestant": True,
        "last_quiz_time": None,
    },
    1002: {
        "score": 141,
        "money": 400000,
        "withdrawn": 100000,
        "name": "Jasurbek Karimov",
        "referrals_count": 47,
        "referred_users": [],
        "is_contestant": True,
        "last_quiz_time": None,
    },
    1003: {
        "score": 120,
        "money": 350000,
        "withdrawn": 100000,
        "name": "Dilshod Olimov",
        "referrals_count": 40,
        "referred_users": [],
        "is_contestant": True,
        "last_quiz_time": None,
    },
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
        "last_quiz_time": None,
    }

# pending_referrals: /start?start=ref_ID orqali kelgan referral
pending_referrals = {}

# Faqat JOIN REQUEST kelgan foydalanuvchilar.
# Bu set "request yuborgan, lekin hali kanalga kiritilmagan" userlarni ham saqlaydi.
join_request_users = set()

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


# ============================================================
# DTM SAVOLLARI
# ============================================================

CATEGORIES_DB = {
    "logic": {
        "title": "🧠 Mantiqiy Fikrlash (DTM)",
        "questions": [
            (
                "Ketma-ketlikdagi qonuniyatni aniqlang va keyingi sonni toping:\n2, 6, 12, 20, 30, 42, ?",
                ["56", "54", "64", "48"],
                0,
            ),
            (
                "Soat 15:40 bo'lganda soat va daqiqa millari orasidagi kichik burchak necha gradus bo'ladi?",
                ["130°", "140°", "125°", "135°"],
                0,
            ),
            (
                "Agar barcha A lar B bo'lsa va ayrim B lar C bo'lsa, qaysi xulosa mutlaqo to'g'ri?",
                [
                    "A va C o'rtasida qat'iy bog'liqlik mavjud emas",
                    "Barcha A lar C dir",
                    "Hech qanday A C emas",
                    "Ba'zi A lar C dir",
                ],
                0,
            ),
            (
                "80 litr 25% li tuz eritmasidan 40% li eritma hosil qilish uchun qancha suv bug'latilishi kerak?",
                ["30 litr", "25 litr", "20 litr", "35 litr"],
                0,
            ),
            (
                "Bir poyezd 120 km/soat tezlikda 300 m tunneldan 15 sekundda to'liq o'tdi. Poyezd uzunligi qancha?",
                ["200 m", "250 m", "150 m", "180 m"],
                0,
            ),
            (
                "Hovuz 1-quvurdan 6 soatda, 2-quvurdan 8 soatda to'ladi, 3-quvurdan 12 soatda bo'shaydi. Uchtasi birgalikda ochilsa, necha soatda to'ladi?",
                ["4.8 soat", "4 soat", "5.2 soat", "3.6 soat"],
                0,
            ),
            (
                "Qutida 6 ta oq, 8 ta qora, 10 ta qizil shar bor. Tavakkal olingan 2 ta sharning ikkalasi ham qora bo'lish ehtimoli?",
                ["7/69", "4/23", "2/15", "8/69"],
                0,
            ),
            (
                "Kitob sahifalari 1 dan boshlab raqamlanganda 687 ta raqam ishlatilgan bo'lsa, kitob necha sahifali?",
                ["265", "250", "280", "275"],
                0,
            ),
            (
                "Agar 5 ta mushuk 5 ta sichqonni 5 minutda tutsa, 100 ta mushuk 100 ta sichqonni necha minutda tutadi?",
                ["5 minut", "100 minut", "20 minut", "50 minut"],
                0,
            ),
            (
                "Uch xonali sonning raqamlari yig'indisi 14 ga teng. O'nliklar xonasi birlikdan 2 barobar katta. Yuzliklar xonasi raqami o'nlikdan 1 ga kam. Bu qaysi son?",
                ["563", "642", "743", "581"],
                0,
            ),
            (
                "Bir oilada 5 aka-ukaning har birining bittadan singlisi bor. Oila a'zolari ota-onani hisobga olmaganda kamida necha kishidan iborat?",
                ["6 kishi", "10 kishi", "7 kishi", "8 kishi"],
                0,
            ),
            (
                "        (
            "Idishdagi bakteriyalar har daqiqada 2 barobarga ko'payadi. Agar idish 60 daqiqada to'lsa, yarmi necha daqiqada to'lgan bo'ladi?",
            ["59 daqiqa", "30 daqiqa", "45 daqiqa", "58 daqiqa"],
            0,
        ),
    ],
},
"it": {
    "title": "💻 IT, Dasturlash & Algoritmlar",
    "questions": [

            (
                "QuickSort algoritmida eng yomon holatdagi (worst-case) asimptotik vaqt murakkabligi qanday?",
                ["O(n²)", "O(n log n)", "O(n)", "O(log n)"],
                0,
            ),
            (
                "IPv6 protokoli bo'yicha tarmoq manzillari necha bitdan iborat bo'ladi?",
                ["128 bit", "64 bit", "32 bit", "256 bit"],
                0,
            ),
            (
                "Relyatsion ma'lumotlar bazasida 3-Normal Forma (3NF) nimani istisno qiladi?",
                [
                    "Tranzitiv bog'liqlikni",
                    "Qisman bog'liqlikni",
                    "Birlamchi kalitni",
                    "Bog'lanishsiz yozuvlarni",
                ],
                0,
            ),
            (
                "Python tilida bool('False') == False ifodasi qanday natija qaytaradi?",
                ["False", "True", "TypeError", "None"],
                0,
            ),
            (
                "OSI tarmoq modelining qaysi pog'onasi IP marshrutlash (routing) uchun javobgar?",
                [
                    "Tarmoq pog'onasi (Network)",
                    "Kanal pog'onasi (Data Link)",
                    "Transport pog'onasi",
                    "Sessiya pog'onasi",
                ],
                0,
            ),
            (
                "Operatsion tizimlarda Deadlock sodir bo'lishining zaruriy shartlariga kirmaydigan omil qaysi?",
                [
                    "Majburiy resurs tortib olish (Preemption)",
                    "O'zaro istisno (Mutual Exclusion)",
                    "Ushlab turish va kutish",
                    "Doiraviy kutish",
                ],
                0,
            ),
            (
                "Git tizimida git rebase ning git merge dan asosiy farqi nimada?",
                [
                    "Commitlar tarixini chiziqli ko'rinishga keltiradi",
                    "Barcha o'zgarishlarni o'chiradi",
                    "Faqat yangi branch yaratadi",
                    "Fayllarni siqadi",
                ],
                0,
            ),
            (
                "B-Daraxti (B-Tree) ma'lumotlar tuzilmasi asosan qayerda samarali qo'llaniladi?",
                [
                    "Diskdagi katta hajmli indekslarda va DB larda",
                    "Operativ xotirani kesh qilishda",
                    "Matnlarni siqishda",
                    "Faqat tarmoq marshrutida",
                ],
                0,
            ),
            (
                "TCP protokoli UDP dan farqli o'laroq nimani ta'minlaydi?",
                [
                    "Paketlar yetkazilishi kafolati va tartibini",
                    "Tezroq videoshaffoflikni",
                    "Faqat mahalliy ulanishni",
                    "Faqat bir tomonlama aloqani",
                ],
                0,
            ),
            (
                "Asinxron dasturlashda Event Loop ning vazifasi nima?",
                [
                    "Kallback va I/O topshiriqlari navbatini boshqarish",
                    "Kodni mashina tiliga o'girish",
                    "Xotirani tozalash",
                    "Shifrlash algoritmlarini yechish",
                ],
                0,
            ),
            (
                "OOP tamoyillariga kirmaydigan jarayonni toping:",
                ["Kompilyatsiya", "Inkapsulyatsiya", "Polimorfizm", "Abstraksiya"],
                0,
            ),
            (
                "1 GiB (Gibibayt) necha Baytdan iborat?",
                ["1024³ Bayt", "1000³ Bayt", "1024² Bayt", "8 * 1024² Bayt"],
                0,
            ),
        ],
    },
    "biology": {
        "title": "🧬 Biologiya & Tibbiyot (DTM)",
        "questions": [
            (
                "Eukariot hujayrada ATF sintezining asosiy qismi qaysi jarayonda amalga oshadi?",
                [
                    "Oksidlanishli fosforillanish (Mitoxondriya kristalarida)",
                    "Glikoliz bosqichida",
                    "Yadro ichida transkripsiyada",
                    "Ribosomada oqsil sintezida",
                ],
                0,
            ),
            (
                "DNK molekulasida timin va adenin o'rtasida nechta vodorod bog'i hosil bo'ladi?",
                ["2 ta", "3 ta", "1 ta", "4 ta"],
                0,
            ),
            (
                "Odamda simpatik nerv tizimi qo'zg'alganda quyidagilardan qaysi biri yuz beradi?",
                [
                    "Qorachiq kengayadi va yurak urishi tezlashadi",
                    "Oshqozon shirasining ajralishi kuchayadi",
                    "Qon bosimi pasayadi",
                    "Bronxlar torayadi",
                ],
                0,
            ),
            (
                "Meyoz bo'linishning qaysi fazasida krossingover (genlar almashinuvi) sodir bo'ladi?",
                ["Profaza I", "Metafaza I", "Anafaza II", "Profaza II"],
                0,
            ),
            (
                "Odam organizmida qon hosil qilishda qatnashuvchi qizil ilik qayerda joylashgan?",
                [
                    "Kemik (g'ovak) suyaklar ichida",
                    "Nerv naychasida",
                    "Faqat bosh chanog'ida",
                    "Jigar to'qimasida",
                ],
                0,
            ),
            (
                "Fotosintezning yorug'lik bosqichida suvning fotolizi natijasida nima ajralib chiqadi?",
                ["Molekulyar kislorod (O2)", "Glyukoza", "Uglerod angidrid", "Azot"],
                0,
            ),
            (
                "Odam organizmidagi eng yirik ichki sekretsiya bezi qaysi?",
                ["Qalqonsimon bez", "Gipofiz", "Buyrak usti bezi", "Epifiz"],
                0,
            ),
            (
                "Oqsillarning birlamchi tuzilishini qanday bog'lar ta'minlaydi?",
                ["Peptid bog'lar", "Vodorod bog'lar", "Disulfid ko'priklari", "Gidrofob bog'lar"],
                0,
            ),
            (
                "Odamda nechta juft somatik xromosoma (autosoma) mavjud?",
                ["22 juft", "23 juft", "46 juft", "44 juft"],
                0,
            ),
            (
                "Gemoglobin tarkibidagi temir ioni qaysi oksidlanish darajasida kislorodni bog'laydi?",
                ["Fe²⁺", "Fe³⁺", "Fe⁴⁺", "Fe⁰"],
                0,
            ),
            (
                "Odam organizmida siydikchil (mochevina) qaysi organda sintezlanadi?",
                ["Jigarda", "Buyrakda", "Talokda", "Oshqozon osti bezida"],
                0,
            ),
            (
                "Bosh miya qismlaridan qaysi biri muvozanat va harakat koordinatsiyasi uchun javobgar?",
                ["Miyacha", "Uzunchoq miya", "O'rta miya", "Gipotalamus"],
                0,
            ),
        ],
    },
    "chemistry": {
        "title": "🧪 Kimyo & Moddalar Tuzilishi (DTM)",
        "questions": [
            (
                "Oddiy sharoitda suyuq holatda bo'ladigan yagona metallmas element qaysi?",
                ["Brom (Br2)", "Simob (Hg)", "Xlor (Cl2)", "Yod (I2)"],
                0,
            ),
            (
                "H₂SO₄ molekulasida oltingugurtning oksidlanish darajasi va valentligi qanday?",
                ["+6 va IV", "+6 va VI", "+4 va IV", "+4 va VI"],
                0,
            ),
            (
                "Quyidagi moddalardan qaysi biri amfoter xossaga ega?",
                ["Al(OH)3", "NaOH", "H2SO4", "BaO"],
                0,
            ),
            (
                "Alkanlarning umumiy gomologik formulasi qaysi?",
                ["CnH2n+2", "CnH2n", "CnH2n-2", "CnH2n-6"],
                0,
            ),
            (
                "Vodorod ko'rsatkichi pH = 3 bo'lgan eritmadagi vodorod ionlari [H+] konsentratsiyasi qancha (mol/l)?",
                ["10⁻³ mol/l", "10⁻¹¹ mol/l", "3 mol/l", "10³ mol/l"],
                0,
            ),
            (
                "Oddiy sharoitda eng yuqori elektr o'tkazuvchanlikka ega bo'lgan metall qaysi?",
                ["Kumush (Ag)", "Mis (Cu)", "Oltin (Au)", "Alyuminiy (Al)"],
                0,
            ),
            (
                "Qaysi gaz havoda kislotali yomg'irlar hosil bo'lishining asosiy sababchisi hisoblanadi?",
                ["SO2", "CH4", "CO", "N2"],
                0,
            ),
            (
                "Mendeleyev davriy sistemasida elektrmanfiyligi eng yuqori bo'lgan element qaysi?",
                ["Ftor (F)", "Kislorod (O)", "Xlor (Cl)", "Fransiy (Fr)"],
                0,
            ),
            (
                "Uglerodning eng qattiq tabiiy allotropik shakl o'zgarishi qaysi?",
                ["Olmos", "Grafit", "Karbin", "Fulleren"],
                0,
            ),
            (
                "Kaliy permanganat (KMnO4) parchalanganda laboratoriyada qaysi gaz olinadi?",
                ["O2", "H2", "Cl2", "N2"],
                0,
            ),
            (
                "Oddiy sharoitda suvda erimaydigan tuzni toping:",
                ["BaSO4", "NaCl", "KNO3", "CaCl2"],
                0,
            ),
            (
                "Eritmada lakmus qog'ozi ishqoriy muhitda qanday rangga kiradi?",
                ["Ko'k", "Qizil", "Sariq", "Rangsiz"],
                0,
            ),
        ],
    },
    "history": {
        "title": "🏛 Tarix & Geografiya (DTM)",
        "questions": [
            (
                "Amir Temur va Boyazid Yildirim o'rtasidagi Anqara jangi qachon sodir bo'lgan?",
                ["1402-yil 20-iyul", "1395-yil 15-aprel", "1399-yil 12-sentyabr", "1405-yil 18-fevral"],
                0,
            ),
            (
                "Qadimgi Baqtriya davlatining poytaxti qaysi shahar bo'lgan?",
                ["Zariaspa (Baqtra)", "Marokanda", "Afrosiyob", "Dovon"],
                0,
            ),
            (
                "Birinchi jahon urushini rasman yakunlagan Versal tinchlik shartnomasi qaysi yili imzolangan?",
                ["1919-yil", "1918-yil", "1920-yil", "1921-yil"],
                0,
            ),
            (
                "Qoraxoniylar davlatida Islom dini davlat dini sifatida qaysi hukmdor davrida e'lon qilingan?",
                ["Sotuq Bug'roxon", "Nasr ibn Ali", "Ibrohim Bo'ritegin", "Yusuf Qodirxon"],
                0,
            ),
            (
                "1868-yilgi Zirabuloq jangida qaysi ikki tomon qo'shinlari to'qnashgan?",
                ["Rossiya imperiyasi va Buxoro amirligi", "Rossiya va Qo'qon xonligi", "Xiva xonligi va Eron", "Buxoro va Afg'oniston"],
                0,
            ),
            (
                "Miloddan avvalgi 530-yilda To'maris qaysi Eron podshohini mag'lub etgan?",
                ["Kir II", "Doro I", "Kserks", "Kambiz"],
                0,
            ),
            (
                "Mirzo Ulug'bek Samarqand rasadxonasida osmon jismlarini kuzatish uchun o'rnatgan asosiy ulkan asbob nima?",
                ["Sekstant (Kvadrant)", "Asturlob", "Optik teleskop", "Kompas"],
                0,
            ),
            (
                "O'rta asr turkiy adabiyotining durdonasi hisoblangan 'Qutadg'u bilig' asari muallifi kim?",
                ["Yusuf Xos Hojib", "Mahmud Qoshg'ariy", "Ahmad Yugnakiy", "Xo'ja Ahmad Yassaviy"],
                0,
            ),
            (
                "Buxoro Xalq Sovet Respublikasi (BXSR) qachon tashkil etilgan?",
                ["1920-yil oktyabr", "1917-yil noyabr", "1924-yil may", "1918-yil mart"],
                0,
            ),
            (
                "O'zbekiston Respublikasining mustaqilligi qaysi anjumanda e'lon qilingan?",
                ["Oliy Kengashning navbatdan tashqari sessiyasida", "Vazirlar Mahkamasida", "Umumxalq referendumida", "Markaziy Kengashda"],
                0,
            ),
            (
                "Dunyodagi eng chuqur chuchuk suvli ko'l qaysi?",
                ["Baykal ko'li", "Viktoriya", "Tanganika", "Yuqori ko'l"],
                0,
            ),
            (
                "Yer sharidagi eng uzun tog' tizmasi qaysi?",
                ["And tog'lari", "Himolay", "Kordilyera", "Ural"],
                0,
            ),
        ],
    },
}


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def get_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎯 Viktorinani Boshlash")],
        [KeyboardButton(text="💳 Balans & Kabinet"), KeyboardButton(text="🎁 Kunlik Bonus")],
        [KeyboardButton(text="🏆 Top Reyting"), KeyboardButton(text="🔗 Do'stlarni Taklif Qilish")],
        [KeyboardButton(text="🎖 Katta Konkurs"), KeyboardButton(text="📜 Qoidalar va Shartlar")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ So'rov yubordim", callback_data="check_join_request")],
        ]
    )


def ensure_user(user_id: int, name: str):
    if user_id not in users_db:
        users_db[user_id] = {
            "score": 0,
            "money": 0,
            "withdrawn": 0,
            "question_num": 0,
            "game_questions": [],
            "referrals_count": 0,
            "referred_users": [],
            "last_bonus": None,
            "category": "logic",
            "name": name,
            "in_game": False,
            "is_contestant": False,
            "last_quiz_time": None,
        }
    else:
        users_db[user_id]["name"] = name


async def process_referral_reward(bot: Bot, user_id: int, user_name: str):
    if user_id in pending_referrals:
        referrer_id = pending_referrals[user_id]

        if referrer_id in users_db and referrer_id != user_id:
            already_referred = any(
                u.get("id") == user_id
                for u in users_db[referrer_id].get("referred_users", [])
            )

            if not already_referred:
                users_db[referrer_id]["referred_users"].append(
                    {"id": user_id, "name": user_name}
                )
                users_db[referrer_id]["referrals_count"] += 1
                users_db[referrer_id]["score"] += 3
                users_db[referrer_id]["money"] += 10000

                try:
                    await bot.send_message(
                        referrer_id,
                        f"🎉 <b>Yangi do'stingiz qo'shildi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 Do'stingiz: <b>{html.escape(user_name)}</b>\n"
                        f"🎁 Sizga: <b>+3 Ball</b> va <b>+10,000 so'm</b> hisobingizga o'tkazildi!",
                    )
                except Exception:
                    pass

        pending_referrals.pop(user_id, None)


# ============================================================
# KANAL JOIN REQUEST
# ============================================================

@dp.chat_join_request()
async def handle_join_request(request: ChatJoinRequest) -> None:
    # Requestni QABUL QILMAYMIZ. Faqat userga botdan foydalanish huquqini beramiz.
    user_id = request.from_user.id
    user_name = request.from_user.full_name or "Foydalanuvchi"
    request_chat_id = getattr(request.chat, "id", None)

    logging.info(
        f"JOIN REQUEST: user={user_id}, chat={request_chat_id}, required={CHANNEL_ID}"
    )

    if request_chat_id != CHANNEL_ID:
        return

    join_request_users.add(user_id)
    ensure_user(user_id, user_name)
    await process_referral_reward(request.bot, user_id, user_name)

    try:
        await request.bot.send_message(
            user_id,
            "✅ <b>So'rov qabul qilindi!</b>\n\n"
            "🎉 Endi botdan foydalanishingiz mumkin.",
            reply_markup=get_reply_keyboard(),
        )
    except Exception as e:
        logging.warning(f"JOIN REQUEST userga xabar yuborilmadi: {e}")


# ============================================================
# ACCESS CHECK
# ============================================================

async def has_bot_access(user_id: int) -> bool:
    """
    Botdan foydalanish uchun user JOIN REQUEST yuborgan bo'lishi kerak.

    Muhim:
    get_chat_member() orqali "member"ni talab qilmaymiz,
    chunki user request yuborgandan keyin kanal admini approve
    qilmaguncha u kanal a'zosi hisoblanmaydi.

    Shuning uchun access = bot olgan ChatJoinRequest.
    """
    return user_id in join_request_users


async def send_join_required(message: Message):
    await message.answer(
        "📢 <b>Kanalimizga a'zo bo'lish uchun so'rov yuboring.</b>\n\n"
        "So'rov yuborgach, pastdagi tugmani bosing.",
        reply_markup=get_join_keyboard(),
    )


async def require_access(message: Message) -> bool:
    user_id = message.from_user.id

    if await has_bot_access(user_id):
        return True

    await send_join_required(message)
    return False


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    logging.info(f"Start buyrug'i keldi: {message.from_user.id}")

    await state.clear()

    user_id = message.from_user.id
    raw_name = message.from_user.full_name or "Foydalanuvchi"

    ensure_user(user_id, raw_name)

    # Referral linkni start argumentidan olish
    if message.text:
        args = message.text.split()

        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                ref_id = int(args[1].split("_")[1])

                if ref_id != user_id and ref_id in users_db:
                    pending_referrals[user_id] = ref_id

            except Exception:
                pass

    # Agar user hali request yubormagan bo'lsa, bot funksiyalari yopiq.
    if not await has_bot_access(user_id):
        await send_join_required(message)
        return

    await process_referral_reward(message.bot, user_id, raw_name)

    safe_name = html.escape(raw_name)

    welcome_text = (
        f"🌟 <b>Assalomu alaykum, {safe_name}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>«Bilag'on Quiz»</b> platformasiga xush kelibsiz!\n\n"
        f"💡 Qiyin DTM savollarini yeching, ball to'plang "
        f"va pul mukofotlarini yutib oling!\n\n"
        f"👇 Quyidagi menyudan kerakli bo'limni tanlang:"
    )

    try:
        await message.answer(
            welcome_text,
            reply_markup=get_reply_keyboard(),
        )
    except Exception as e:
        logging.error(f"Start xabari yuborishda xatolik: {e}")


# ============================================================
# REQUEST TEKSHIRISH
# ============================================================

@dp.callback_query(F.data == "check_join_request")
async def check_join_request_callback(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or "Foydalanuvchi"

    if await has_bot_access(user_id):
        ensure_user(user_id, user_name)
        await process_referral_reward(callback.bot, user_id, user_name)
        await callback.answer("✅ So'rov topildi!", show_alert=True)

        try:
            await callback.message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "🎉 <b>Xush kelibsiz!</b>\n\n"
            "Botdan foydalanishingiz mumkin.",
            reply_markup=get_reply_keyboard(),
        )
        return

    await callback.answer(
        "⏳ So'rov topilmadi. Avval kanalga so'rov yuboring.",
        show_alert=True,
    )


# ============================================================
# VIKTORINA
# ============================================================

@dp.message(F.text == "🎯 Viktorinani Boshlash")
async def quiz_category_selection(message: Message) -> None:
    if not await require_access(message):
        return

    user_id = message.from_user.id
    u_data = users_db.get(user_id, {})

    if u_data.get("in_game", False):
        await message.answer(
            "⚠️ Sizda hozir faol test davom etmoqda! "
            "Uni yakunlang yoki bekor qiling."
        )
        return

    last_time = u_data.get("last_quiz_time")

    if last_time:
        diff_hours = (
            datetime.datetime.now() - last_time
        ).total_seconds() / 3600

        if diff_hours < 24:
            rem_h = int(24 - diff_hours)

            await message.answer(
                f"⏳ <b>Kunlik limit!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Siz oxirgi testni topshirgansiz.\n"
                f"Yangi urinish <b>{rem_h} soatdan</b> keyin ochiladi."
            )
            return

    keyboard = []

    for cat_key, cat_val in CATEGORIES_DB.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=cat_val["title"],
                    callback_data=f"cat_{cat_key}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Bosh Menyu",
                callback_data="cancel_quiz",
            )
        ]
    )

    text = (
        "📚 <b>DTM Test Yo'nalishini Tanlang</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏱ <b>Vaqt chegarasi:</b> Har bir savolga <b>30 soniya</b>.\n\n"
        "🎯 10 ta savoldan barchasini to'g'ri topsangiz "
        "qo'shimcha ball va mukofot beriladi."
    )

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
    )


@dp.callback_query(F.data.startswith("cat_"))
async def start_quiz_session(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id

    if not await has_bot_access(user_id):
        await callback.answer(
            "🔐 Avval kanalga qo'shilish so'rovini yuboring!",
            show_alert=True,
        )
        return

    cat_key = callback.data.split("_", 1)[1]

    if user_id not in users_db:
        ensure_user(
            user_id,
            callback.from_user.full_name or "Foydalanuvchi",
        )

    questions_pool = CATEGORIES_DB.get(cat_key, {}).get(
        "questions",
        [],
    )

    if not questions_pool:
        await callback.answer(
            "Savollar bazasi topilmadi!",
            show_alert=True,
        )
        return

    selected_questions = random.sample(
        questions_pool,
        min(len(questions_pool), 10),
    )

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

    await send_quiz_step(
        callback.bot,
        callback.message.chat.id,
        user_id,
    )


async def quiz_timer_countdown(
    bot: Bot,
    chat_id: int,
    user_id: int,
    question_index: int,
    msg_id: int,
):
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
                    text=(
                        "⌛️ <b>Vaqt tugadi!</b>\n\n"
                        "30 soniya ichida javob berilmadi ❌"
                    ),
                )
            except Exception:
                pass

            u_data["question_num"] += 1

            await send_quiz_step(
                bot,
                chat_id,
                user_id,
            )

    except asyncio.CancelledError:
        pass


async def send_quiz_step(
    bot: Bot,
    chat_id: int,
    user_id: int,
):
    if user_id in active_timers:
        if not active_timers[user_id].done():
            active_timers[user_id].cancel()

    u_data = users_db.get(user_id)

    if not u_data:
        return

    q_idx = u_data["question_num"]
    questions = u_data["game_questions"]

    if q_idx >= len(questions):
        u_data["in_game"] = False
        u_data["last_quiz_time"] = datetime.datetime.now()

        corrects = u_data.get("correct_count", 0)

        if corrects >= len(questions):
            u_data["score"] += 5
            u_data["money"] += 15000

            res_text = (
                f"🎉 <b>MUKAMMAL NATIJA!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Barcha {len(questions)} ta savolga "
                f"to'g'ri javob berdingiz!\n\n"
                f"🎁 Mukofot: <b>+5 Ball</b>\n"
                f"💰 Mukofot: <b>+15,000 so'm</b>"
            )
        else:
            res_text = (
                f"🏁 <b>Test Yakunlandi!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 To'g'ri javoblar: "
                f"<b>{corrects} / {len(questions)}</b>\n\n"
                f"💡 Qo'shimcha 5 ball va 15,000 so'm "
                f"olish uchun barcha savollarni to'g'ri topish lozim."
            )

        await bot.send_message(
            chat_id,
            res_text,
            reply_markup=get_reply_keyboard(),
        )
        return

    q_text, options, correct_opt = questions[q_idx]

    total_q = len(questions)

    filled_blocks = int(
        ((q_idx + 1) / total_q) * 10
    )

    bar = (
        "█" * filled_blocks
        + "░" * (10 - filled_blocks)
    )

    keyboard_buttons = []
    option_letters = ["A", "B", "C", "D"]

    for idx, opt in enumerate(options):
        letter = (
            option_letters[idx]
            if idx < len(option_letters)
            else str(idx + 1)
        )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{letter}) {opt}",
                    callback_data=(
                        f"ans_{idx}_{correct_opt}_{q_idx}"
                    ),
                )
            ]
        )

    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text="🛑 Testdan Chiqish",
                callback_data="cancel_quiz",
            )
        ]
    )

    msg_body = (
        f"📝 <b>Savol {q_idx + 1} / {total_q}</b>\n"
        f"📊 Progress: [{bar}]\n"
        f"⏱ <b>Qolgan vaqt: 30 soniya</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{q_text}</b>"
    )

    sent_msg = await bot.send_message(
        chat_id,
        msg_body,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_buttons
        ),
    )

    timer_task = asyncio.create_task(
        quiz_timer_countdown(
            bot,
            chat_id,
            user_id,
            q_idx,
            sent_msg.message_id,
        )
    )

    active_timers[user_id] = timer_task


@dp.callback_query(F.data.startswith("ans_"))
async def handle_user_answer(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if not await has_bot_access(user_id):
        await callback.answer(
            "🔐 Avval kanalga qo'shilish so'rovini yuboring!",
            show_alert=True,
        )
        return

    if (
        user_id not in users_db
        or not users_db[user_id].get("in_game", False)
    ):
        await callback.answer(
            "⚠️ Faol test topilmadi!",
            show_alert=True,
        )
        return

    parts = callback.data.split("_")

    try:
        chosen_idx = int(parts[1])
        correct_idx = int(parts[2])
        q_idx = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer(
            "❌ Javob ma'lumotida xatolik.",
            show_alert=True,
        )
        return

    if users_db[user_id].get("question_num") != q_idx:
        await callback.answer(
            "⚠️ Bu savolning vaqti o'tib ketgan!"
        )
        return

    if user_id in active_timers:
        if not active_timers[user_id].done():
            active_timers[user_id].cancel()

    if chosen_idx == correct_idx:
        users_db[user_id]["correct_count"] = (
            users_db[user_id].get("correct_count", 0) + 1
        )
        await callback.answer("✅ To'g'ri!")
    else:
        await callback.answer("❌ Noto'g'ri!")

    users_db[user_id]["question_num"] += 1

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_quiz_step(
        callback.bot,
        callback.message.chat.id,
        user_id,
    )


@dp.callback_query(F.data == "cancel_quiz")
async def cancel_quiz_handler(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if user_id in active_timers:
        if not active_timers[user_id].done():
            active_timers[user_id].cancel()

    if user_id in users_db:
        users_db[user_id]["in_game"] = False

    await callback.answer("Jarayon bekor qilindi.")

    try:
        await callback.message.delete()
    except Exception:
        pass

    if await has_bot_access(user_id):
        await callback.message.answer(
            "🏠 <b>Asosiy menyu</b>\n\n"
            "Kerakli bo'limni tanlang:",
            reply_markup=get_reply_keyboard(),
        )
    else:
        await send_join_required(callback.message)


# ============================================================
# BALANS & KABINET
# ============================================================

@dp.message(F.text == "💳 Balans & Kabinet")
async def show_user_profile(message: Message) -> None:
    if not await require_access(message):
        return

    user_id = message.from_user.id

    ensure_user(
        user_id,
        message.from_user.full_name or "Foydalanuvchi",
    )

    u_data = users_db[user_id]

    score = u_data.get("score", 0)
    money = u_data.get("money", 0)
    withdrawn = u_data.get("withdrawn", 0)
    refs = u_data.get("referrals_count", 0)

    bot_info = await message.bot.get_me()

    ref_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{user_id}"
    )

    text = (
        f"💎 <b>Shaxsiy Kabinet & Moliyaviy Holat</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID raqam: <code>{user_id}</code>\n"
        f"👤 Foydalanuvchi: "
        f"<b>{html.escape(u_data.get('name', 'Ishtirokchi'))}</b>\n"
        f"👥 Taklif qilgan do'stlar: <b>{refs} ta</b>\n"
        f"🏆 Jami to'plangan ball: <b>{score} ball</b>\n"
        f"💰 Asosiy hisob: <b>{money:,} so'm</b>\n"
        f"💸 Yechib olingan jami: <b>{withdrawn:,} so'm</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💸 Pulni Yechib Olish",
                    callback_data="withdraw_funds",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga Qaytish",
                    callback_data="cancel_quiz",
                )
            ],
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "withdraw_funds")
async def start_withdrawal_flow(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    user_id = callback.from_user.id

    if not await has_bot_access(user_id):
        await callback.answer(
            "🔐 Avval kanalga qo'shilish so'rovini yuboring!",
            show_alert=True,
        )
        return

    u_data = users_db.get(user_id, {})

    score = u_data.get("score", 0)
    money = u_data.get("money", 0)

    if score < 50 or money <= 0:
        needed = max(0, 50 - score)

        text = (
            f"🚫 <b>Pul yechish imkonsiz!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Minimal talab: <b>50 ball</b> "
            f"va hisobda mablag' bo'lishi kerak.\n"
            f"📊 Sizning ballingiz: <b>{score} ball</b>\n"
            f"💰 Balansingiz: <b>{money:,} so'm</b>\n\n"
            f"Yana <b>{needed} ball</b> kerak."
        )

        await callback.answer(
            "Ball yetarli emas!",
            show_alert=True,
        )

        await callback.message.answer(text)
        return

    await callback.answer()

    await state.set_state(
        WithdrawStates.waiting_for_name
    )

    await callback.message.answer(
        "📝 <b>Pulni o'tkazish uchun</b>\n\n"
        "Ism va Familiyangizni kiriting:"
    )


@dp.message(WithdrawStates.waiting_for_name)
async def process_withdraw_name(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        user_fullname=message.text.strip()
    )

    await state.set_state(
        WithdrawStates.waiting_for_card
    )

    await message.answer(
        "💳 <b>Karta raqamingizni</b> kiriting:\n"
        "Masalan: <code>8600 0000 0000 0000</code>"
    )


@dp.message(WithdrawStates.waiting_for_card)
async def process_withdraw_card(
    message: Message,
    state: FSMContext,
) -> None:
    card_info = (
        message.text.strip()
        .replace(" ", "")
        .replace("-", "")
    )

    if not card_info.isdigit() or len(card_info) != 16:
        await message.answer(
            "❌ Karta raqami noto'g'ri.\n"
            "16 xonali karta raqamini kiriting:"
        )
        return

    user_id = message.from_user.id

    data = await state.get_data()
    fullname = data.get("user_fullname")

    money = users_db.get(user_id, {}).get(
        "money",
        0,
    )

    users_db[user_id]["withdrawn"] = (
        users_db[user_id].get("withdrawn", 0)
        + money
    )

    users_db[user_id]["money"] = 0
    users_db[user_id]["score"] = 0

    await state.clear()

    admin_notification = (
        f"🚨 <b>Yangi Pul Yechish So'rovi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Foydalanuvchi: "
        f"{html.escape(message.from_user.full_name)} "
        f"(@{html.escape(message.from_user.username or 'yoq')})\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📝 F.I.SH: <b>{html.escape(fullname)}</b>\n"
        f"💳 Karta: <code>{card_info}</code>\n"
        f"💰 Summa: <b>{money:,} so'm</b>"
    )

    if ADMIN_ID != 0:
        try:
            await message.bot.send_message(
                ADMIN_ID,
                admin_notification,
            )
        except Exception as e:
            logging.error(
                f"Adminga xabar yuborishda xatolik: {e}"
            )

    await message.answer(
        f"✅ <b>So'rovingiz qabul qilindi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Mablag': <b>{money:,} so'm</b>\n"
        f"⏳ To'lov tez orada amalga oshiriladi.",
        reply_markup=get_reply_keyboard(),
    )


# ============================================================
# BONUS & REFERAL
# ============================================================

@dp.message(F.text == "🎁 Kunlik Bonus")
async def claim_daily_bonus(message: Message) -> None:
    if not await require_access(message):
        return

    user_id = message.from_user.id

    ensure_user(
        user_id,
        message.from_user.full_name or "Foydalanuvchi",
    )

    now = datetime.datetime.now()

    last_bonus = users_db[user_id].get("last_bonus")

    if (
        last_bonus
        and (now - last_bonus).total_seconds() < 86400
    ):
        rem_sec = (
            86400
            - (now - last_bonus).total_seconds()
        )

        rem_h = int(rem_sec // 3600)

        await message.answer(
            f"⏳ <b>Kunlik bonus olingan!</b>\n\n"
            f"Keyingisi <b>{rem_h} soatdan</b> so'ng beriladi."
        )
        return

    b_score = random.randint(1, 3)
    b_money = b_score * 3000

    users_db[user_id]["score"] = (
        users_db[user_id].get("score", 0)
        + b_score
    )

    users_db[user_id]["money"] = (
        users_db[user_id].get("money", 0)
        + b_money
    )

    users_db[user_id]["last_bonus"] = now

    await message.answer(
        f"🎉 <b>Kunlik Sovg'angiz!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Ball: <b>+{b_score} ball</b>\n"
        f"💰 Balans: <b>+{b_money:,} so'm</b>\n\n"
        f"🔥 Ertaga yana bonus oling!"
    )


@dp.message(F.text == "🔗 Do'stlarni Taklif Qilish")
async def referral_program_info(message: Message) -> None:
    if not await require_access(message):
        return

    user_id = message.from_user.id

    bot_info = await message.bot.get_me()

    ref_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{user_id}"
    )

    u_data = users_db.get(
        user_id,
        {
            "referrals_count": 0,
            "referred_users": [],
        },
    )

    refs = u_data.get("referrals_count", 0)
    referred_list = u_data.get(
        "referred_users",
        [],
    )

    ref_items = ""

    if referred_list:
        for idx, item in enumerate(
            referred_list[-5:],
            1,
        ):
            ref_items += (
                f"{idx}. "
                f"{html.escape(item['name'])}\n"
            )
    else:
        ref_items = (
            "<i>Hozircha do'stlaringiz "
            "qo'shilmagan.</i>\n"
        )

    text = (
        f"👥 <b>Do'stlarni Taklif Qilish Tizimi</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Har bir yangi a'zo uchun:\n"
        f"🎁 <b>+3 Ball</b> va <b>+10,000 so'm</b>!\n\n"
        f"📊 Sizning referallaringiz: <b>{refs} ta</b>\n"
        f"📋 Oxirgi qo'shilganlar:\n{ref_items}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    await message.answer(text)


@dp.message(F.text == "🏆 Top Reyting")
async def show_leaderboard(message: Message) -> None:
    if not await require_access(message):
        return

    sorted_users = sorted(
        users_db.values(),
        key=lambda x: (
            x.get("score", 0),
            x.get("money", 0)
            + x.get("withdrawn", 0),
        ),
        reverse=True,
    )[:10]

    board = (
        "🏆 <b>Top-10 Liderlar Jadvali</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for idx, u in enumerate(
        sorted_users,
        1,
    ):
        name = u.get(
            "name",
            "Ishtirokchi",
        )

        score = u.get("score", 0)
        money = u.get("money", 0)
        withdrawn = u.get("withdrawn", 0)

        total_earned = money + withdrawn

        medal = (
            "🥇"
            if idx == 1
            else (
                "🥈"
                if idx == 2
                else (
                    "🥉"
                    if idx == 3
                    else f"{idx}."
                )
            )
        )

        board += (
            f"{medal} <b>{html.escape(name)}</b>\n"
            f"   └ Ball: <b>{score}</b> | "
            f"Jami: <b>{total_earned:,} so'm</b>\n\n"
        )

    await message.answer(board)


# ============================================================
# KATTA KONKURS
# ============================================================

@dp.message(F.text == "🎖 Katta Konkurs")
async def contest_screen(message: Message) -> None:
    if not await require_access(message):
        return

    user_id = message.from_user.id

    u_data = users_db.get(
        user_id,
        {},
    )

    is_contestant = u_data.get(
        "is_contestant",
        False,
    )

    contestants = sorted(
        [
            u
            for u in users_db.values()
            if u.get("is_contestant", False)
        ],
        key=lambda x: x.get(
            "referrals_count",
            0,
        ),
        reverse=True,
    )

    top_name = (
        contestants[0].get(
            "name",
            "Bekzod To'rayev",
        )
        if contestants
        else "Bekzod To'rayev"
    )

    top_refs = (
        contestants[0].get(
            "referrals_count",
            52,
        )
        if contestants
        else 52
    )

    text = (
        f"🎖 <b>Katta Pul Mukofoti Konkursi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Mukofot jamg'armasi: "
        f"<b>300,000 so'm naqd pul!</b>\n"
        f"📌 Shart: Eng ko'p do'st taklif qilgan "
        f"1-o'rin sohibi sovrinni oladi.\n\n"
        f"🥇 1-o'rindagi ishtirokchi: "
        f"<b>{html.escape(top_name)}</b> "
        f"({top_refs} ta taklif)\n"
    )

    keyboard_btns = []

    if not is_contestant:
        text += (
            "\n❌ <i>Siz hali konkursda "
            "ro'yxatdan o'tmagansiz!</i>"
        )

        keyboard_btns.append(
            [
                InlineKeyboardButton(
                    text="✍️ Konkursga Ro'yxatdan O'tish",
                    callback_data="register_contest",
                )
            ]
        )
    else:
        rank = 1

        for idx, c in enumerate(
            contestants,
            1,
        ):
            if c.get("name") == u_data.get(
                "name"
            ):
                rank = idx
                break

        text += (
            f"\n✅ Siz konkurs a'zosisiz! "
            f"O'rningiz: <b>{rank}-o'rin</b>"
        )

    keyboard_btns.append(
        [
            InlineKeyboardButton(
                text="🔙 Bosh Menyu",
                callback_data="cancel_quiz",
            )
        ]
    )

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_btns
        ),
    )


@dp.callback_query(F.data == "register_contest")
async def register_contest_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await has_bot_access(
        callback.from_user.id
    ):
        await callback.answer(
            "🔐 Avval kanalga qo'shilish so'rovini yuboring!",
            show_alert=True,
        )
        return

    await callback.answer()

    await state.set_state(
        ContestStates.waiting_for_name
    )

    await callback.message.answer(
        "1️⃣ Konkurs uchun <b>Ismingizni</b> yozing:"
    )


@dp.message(ContestStates.waiting_for_name)
async def contest_step_name(
    message: Message,
    state: FSMContext,
) -> None:
    await state.update_data(
        c_name=message.text.strip()
    )

    await state.set_state(
        ContestStates.waiting_for_surname
    )

    await message.answer(
        "2️⃣ Endi <b>Familiyangizni</b> kiriting:"
    )


@dp.message(ContestStates.waiting_for_surname)
async def contest_step_surname(
    message: Message,
    state: FSMContext,
) -> None:
    surname = message.text.strip()

    data = await state.get_data()

    full_name = (
        f"{data.get('c_name')} {surname}"
    )

    user_id = message.from_user.id

    ensure_user(
        user_id,
        full_name,
    )

    users_db[user_id]["name"] = full_name
    users_db[user_id]["is_contestant"] = True

    await state.clear()

    await message.answer(
        f"🎉 <b>Tabriklaymiz, "
        f"{html.escape(full_name)}!</b>\n\n"
        f"Siz konkurs ishtirokchisisiz!",
        reply_markup=get_reply_keyboard(),
    )


# ============================================================
# QOIDALAR
# ============================================================

@dp.message(F.text == "📜 Qoidalar va Shartlar")
async def show_rules_handler(message: Message) -> None:
    if not await require_access(message):
        return

    rules = (
        "📜 <b>Loyihaning Asosiy Qoidalari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1. <b>Kanal:</b> Botdan foydalanish uchun "
        "kanalga qo'shilish so'rovi yuborilishi kerak.\n\n"
        "2. <b>Request:</b> Bot foydalanuvchini kanalga "
        "avtomatik qabul qilmaydi. So'rov adminlar "
        "Requests bo'limida ko'rib chiqiladi.\n\n"
        "3. <b>Vaqt:</b> Har bir savolga 30 soniya.\n\n"
        "4. <b>Bonus:</b> 10 ta savolning barchasiga "
        "to'g'ri javob berilsa +5 ball va +15,000 so'm.\n\n"
        "5. <b>Referal:</b> Har bir yangi do'st uchun "
        "+3 ball va +10,000 so'm.\n\n"
        "6. <b>Mablag' yechish:</b> Kamida 50 ball "
        "to'plash lozim."
    )

    await message.answer(rules)


# ============================================================
# ADMIN PANEL
# ============================================================

def is_admin_user(message: Message) -> bool:
    user_id = message.from_user.id
    username = message.from_user.username

    return (
        (ADMIN_ID != 0 and user_id == ADMIN_ID)
        or (
            ADMIN_USERNAME
            and username
            and username.lower()
            == ADMIN_USERNAME.lower()
        )
    )


@dp.message(Command("admin"))
async def admin_dashboard(
    message: Message,
) -> None:
    if not is_admin_user(message):
        return

    contestants = [
        u
        for u in users_db.values()
        if u.get("is_contestant", False)
    ]

    contestants_list_text = ""

    for idx, c in enumerate(
        contestants[:10],
        1,
    ):
        contestants_list_text += (
            f"{idx}. "
            f"{html.escape(c.get('name', 'Noma' ))} — "
            f"{c.get('referrals_count', 0)} ta taklif\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Xabar Tarqatish",
                    callback_data="adm_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ / ➖ Balans O'zgartirish",
                    callback_data="adm_change_score",
                )
            ],
        ]
    )

    text = (
        f"👑 <b>Admin Boshqaruv Markazi</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Konkurs a'zolari: "
        f"<b>{len(contestants)} ta</b>\n\n"
        f"📊 <b>Top Ishtirokchilar:</b>\n"
        f"{contestants_list_text}"
    )

    await message.answer(
        text,
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "adm_change_score")
async def admin_change_score_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin_user(callback.message):
        return

    await callback.answer()

    await state.set_state(
        AdminScoreStates.waiting_for_user_id
    )

    await callback.message.answer(
        "🆔 Balansini o'zgartirmoqchi bo'lgan "
        "foydalanuvchining <b>Telegram ID</b> "
        "raqamini yuboring:"
    )


@dp.message(AdminScoreStates.waiting_for_user_id)
async def process_admin_user_id(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin_user(message):
        return

    try:
        target_id = int(
            message.text.strip()
        )

        if target_id not in users_db:
            await message.answer(
                "❌ Foydalanuvchi bazadan topilmadi!\n"
                "Qaytadan ID yuboring:"
            )
            return

        await state.update_data(
            target_user_id=target_id
        )

        await state.set_state(
            AdminScoreStates.waiting_for_score_amount
        )

        cur_money = users_db[target_id].get(
            "money",
            0,
        )

        await message.answer(
            f"👤 Topildi: "
            f"<b>{html.escape(users_db[target_id]['name'])}</b>\n"
            f"💰 Hozirgi balans: "
            f"<b>{cur_money:,} so'm</b>\n\n"
            f"Qo'shiladigan summani kiriting:\n"
            f"Masalan: <code>50000</code> yoki "
            f"<code>-20000</code>"
        )

    except ValueError:
        await message.answer(
            "❌ Noto'g'ri ID formati! Raqam kiriting:"
        )


@dp.message(AdminScoreStates.waiting_for_score_amount)
async def process_admin_score_amount(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin_user(message):
        return

    try:
        amount = int(
            message.text.strip()
        )

        data = await state.get_data()

        target_id = data.get(
            "target_user_id"
        )

        if target_id not in users_db:
            await state.clear()
            await message.answer(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        users_db[target_id]["money"] += amount

        new_money = users_db[target_id]["money"]

        await state.clear()

        await message.answer(
            f"✅ <b>Muvaffaqiyatli bajarildi!</b>\n\n"
            f"👤 {html.escape(users_db[target_id]['name'])}\n"
            f"💰 Yangi balans: "
            f"<b>{new_money:,} so'm</b>"
        )

    except ValueError:
        await message.answer(
            "❌ Summa noto'g'ri kiritildi!\n"
            "Raqam kiriting:"
        )


@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not is_admin_user(callback.message):
        return

    await callback.answer()

    await state.set_state(
        BroadcastStates.waiting_for_broadcast_message
    )

    await callback.message.answer(
        "📝 <b>Tarqatma xabar</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni "
        "shu yerga yuboring:"
    )


@dp.message(
    BroadcastStates.waiting_for_broadcast_message
)
async def process_broadcast_message(
    message: Message,
    state: FSMContext,
) -> None:
    if not is_admin_user(message):
        return

    await state.clear()

    sent_count = 0

    status_msg = await message.answer(
        "🚀 <b>Xabar yuborilmoqda...</b>"
    )

    for uid in list(users_db.keys()):
        if isinstance(uid, str) or uid < 10000:
            continue

        try:
            await message.send_copy(
                chat_id=uid
            )

            sent_count += 1

            await asyncio.sleep(0.04)

        except Exception:
            pass

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"👥 Yuborilganlar: <b>{sent_count} ta</b>"
    )


# ============================================================
# MAIN
# ============================================================

async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    try:
        await bot.delete_webhook(
            drop_pending_updates=True
        )
    except Exception as e:
        logging.warning(
            f"Webhook tozalashda ogohlantirish: {e}"
        )

    # Bot menyusida faqat /start
    try:
        await bot.set_my_commands(
            [
                BotCommand(
                    command="start",
                    description="Bosh menyuni ochish",
                )
            ],
            scope=BotCommandScopeDefault(),
        )
    except Exception as e:
        logging.warning(
            f"Menyuni sozlashda ogohlantirish: {e}"
        )

    me = await bot.get_me()

    print(
        "=================================================="
    )
    print(
        f"BOT ISHLADI: @{me.username}"
    )
    print(
        f"REQUEST KANALI ID: {CHANNEL_ID}"
    )
    print(
        "JOIN REQUEST avtomatik tasdiqlanmaydi."
    )
    print(
        "=================================================="
    )

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (
        KeyboardInterrupt,
        SystemExit,
    ):
        print("Bot to'xtatildi.")
