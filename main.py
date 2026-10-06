import asyncio
import datetime
import logging
import random
import sys
import os
import html

from aiogram import Bot, Dispatcher, F
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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8963661833:AAGGL_SPYda_dWR3zlHU5_5XnWCE7nupXRw").strip()

REQUIRED_CHANNEL = "@Auto_Captions"
CHANNEL_ID = -1004317372728
CHANNEL_LINK = "https://t.me/+llFGqeWBsuZlMGYy"

ADMIN_USERNAME = "manmode_admin2"
ADMIN_ID = 0  # O'zingizning Telegram raqamli ID'ingizni yozishingiz mumkin

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

pending_referrals = {}
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
            ("Ketma-ketlikdagi qonuniyatni aniqlang va keyingi sonni toping:\n2, 6, 12, 20, 30, 42, ?", ["56", "54", "64", "48"], 0),
            ("Soat 15:40 bo'lganda soat va daqiqa millari orasidagi kichik burchak necha gradus bo'ladi?", ["130°", "140°", "125°", "135°"], 0),
            ("Agar barcha A lar B bo'lsa va ayrim B lar C bo'lsa, qaysi xulosa mutlaqo to'g'ri?", ["A va C o'rtasida qat'iy bog'liqlik mavjud emas", "Barcha A lar C dir", "Hech qanday A C emas", "Ba'zi A lar C dir"], 0),
            ("80 litr 25% li tuz eritmasidan 40% li eritma hosil qilish uchun qancha suv bug'latilishi kerak?", ["30 litr", "25 litr", "20 litr", "35 litr"], 0),
            ("Bir poyezd 120 km/soat tezlikda 300 m tunneldan 15 sekundda to'liq o'tdi. Poyezd uzunligi qancha?", ["200 m", "250 m", "150 m", "180 m"], 0),
            ("Hovuz 1-quvurdan 6 soatda, 2-quvurdan 8 soatda to'ladi, 3-quvurdan 12 soatda bo'shaydi. Uchtasi birgalikda ochilsa, necha soatda to'ladi?", ["4.8 soat", "4 soat", "5.2 soat", "3.6 soat"], 0),
            ("Qutida 6 ta oq, 8 ta qora, 10 ta qizil shar bor. Tavakkal olingan 2 ta sharning ikkalasi ham qora bo'lish ehtimoli?", ["7/69", "4/23", "2/15", "8/69"], 0),
            ("Kitob sahifalari 1 dan boshlab raqamlanganda 687 ta raqam ishlatilgan bo'lsa, kitob necha sahifali?", ["265", "250", "280", "275"], 0),
            ("Agar 5 ta mushuk 5 ta sichqonni 5 minutda tutsa, 100 ta mushuk 100 ta sichqonni necha minutda tutadi?", ["5 minut", "100 minut", "20 minut", "50 minut"], 0),
            ("Uch xonali sonning raqamlari yig'indisi 14 ga teng. O'nliklar xonasi birlikdan 2 barobar katta. Yuzliklar xonasi raqami o'nlikdan 1 ga kam. Bu qaysi son?", ["563", "642", "743", "581"], 0),
            ("Bir oilada 5 aka-ukaning har birining bittadan singlisi bor. Oila a'zolari ota-onani hisobga olmaganda kamida necha kishidan iborat?", ["6 kishi", "10 kishi", "7 kishi", "8 kishi"], 0),
            ("Idishdagi bakteriyalar har daqiqada 2 barobarga ko'payadi. Agar idish 60 daqiqada to'lsa, yarmi necha daqiqada to'lgan bo'ladi?", ["59 daqiqa", "30 daqiqa", "45 daqiqa", "58 daqiqa"], 0),
        ],
    },
    "it": {
        "title": "💻 IT, Dasturlash & Algoritmlar",
        "questions": [
            ("QuickSort algoritmida eng yomon holatdagi (worst-case) asimptotik vaqt murakkabligi qanday?", ["O(n²)", "O(n log n)", "O(n)", "O(log n)"], 0),
            ("IPv6 protokoli bo'yicha tarmoq manzillari necha bitdan iborat bo'ladi?", ["128 bit", "64 bit", "32 bit", "256 bit"], 0),
            ("Relyatsion ma'lumotlar bazasida 3-Normal Forma (3NF) nimani istisno qiladi?", ["Tranzitiv bog'liqlikni", "Qisman bog'liqlikni", "Birlamchi kalitni", "Bog'lanishsiz yozuvlarni"], 0),
            ("Python tilida bool('False') == False ifodasi qanday natija qaytaradi?", ["False", "True", "TypeError", "None"], 0),
            ("OSI tarmoq modelining qaysi pog'onasi IP marshrutlash (routing) uchun javobgar?", ["Tarmoq pog'onasi (Network)", "Kanal pog'onasi (Data Link)", "Transport pog'onasi", "Sessiya pog'onasi"], 0),
            ("Operatsion tizimlarda Deadlock sodir bo'lishining zaruriy shartlariga kirmaydigan omil qaysi?", ["Majburiy resurs tortib olish (Preemption)", "O'zaro istisno (Mutual Exclusion)", "Ushlab turish va kutish", "Doiraviy kutish"], 0),
            ("Git tizimida git rebase ning git merge dan asosiy farqi nimada?", ["Commitlar tarixini chiziqli ko'rinishga keltiradi", "Barcha o'zgarishlarni o'chiradi", "Faqat yangi branch yaratadi", "Fayllarni siqadi"], 0),
            ("B-Daraxti (B-Tree) ma'lumotlar tuzilmasi asosan qayerda samarali qo'llaniladi?", ["Diskdagi katta hajmli indekslarda va DB larda", "Operativ xotirani kesh qilishda", "Matnlarni siqishda", "Faqat tarmoq marshrutida"], 0),
            ("TCP protokoli UDP dan farqli o'laroq nimani ta'minlaydi?", ["Paketlar yetkazilishi kafolati va tartibini", "Tezroq videoshaffoflikni", "Faqat mahalliy ulanishni", "Faqat bir tomonlama aloqani"], 0),
            ("Asinxron dasturlashda Event Loop ning vazifasi nima?", ["Kallback va I/O topshiriqlari navbatini boshqarish", "Kodni mashina tiliga o'girish", "Xotirani tozalash", "Shifrlash algoritmlarini yechish"], 0),
            ("OOP tamoyillariga kirmaydigan jarayonni toping:", ["Kompilyatsiya", "Inkapsulyatsiya", "Polimorfizm", "Abstraksiya"], 0),
            ("1 GiB (Gibibayt) necha Baytdan iborat?", ["1024³ Bayt", "1000³ Bayt", "1024² Bayt", "8 * 1024² Bayt"], 0),
        ],
    },
    "biology": {
        "title": "🧬 Biologiya & Tibbiyot (DTM)",
        "questions": [
            ("Eukariot hujayrada ATF sintezining asosiy qismi qaysi jarayonda amalga oshadi?", ["Oksidlanishli fosforillanish (Mitoxondriya kristalarida)", "Glikoliz bosqichida", "Yadro ichida transkripsiyada", "Ribosomada oqsil sintezida"], 0),
            ("DNK molekulasida timin va adenin o'rtasida nechta vodorod bog'i hosil bo'ladi?", ["2 ta", "3 ta", "1 ta", "4 ta"], 0),
            ("Odamda simpatik nerv tizimi qo'zg'alganda quyidagilardan qaysi biri yuz beradi?", ["Qorachiq kengayadi va yurak urishi tezlashadi", "Oshqozon shirasining ajralishi kuchayadi", "Qon bosimi pasayadi", "Bronxlar torayadi"], 0),
            ("Meyoz bo'linishning qaysi fazasida krossingover (genlar almashinuvi) sodir bo'ladi?", ["Profaza I", "Metafaza I", "Anafaza II", "Profaza II"], 0),
            ("Odam organizmida qon hosil qilishda qatnashuvchi qizil ilik qayerda joylashgan?", ["Kemik (g'ovak) suyaklar ichida", "Nerv naychasida", "Faqat bosh chanog'ida", "Jigar to'qimasida"], 0),
            ("Fotosintezning yorug'lik bosqichida suvning fotolizi natijasida nima ajralib chiqadi?", ["Molekulyar kislorod (O2)", "Glyukoza", "Uglerod angidrid", "Azot"], 0),
            ("Odam organizmidagi eng yirik ichki sekretsiya bezi qaysi?", ["Qalqonsimon bez", "Gipofiz", "Buyrak usti bezi", "Epifiz"], 0),
            ("Oqsillarning birlamchi tuzilishini qanday bog'lar ta'minlaydi?", ["Peptid bog'lar", "Vodorod bog'lar", "Disulfid ko'priklari", "Gidrofob bog'lar"], 0),
            ("Odamda nechta juft somatik xromosoma (autosoma) mavjud?", ["22 juft", "23 juft", "46 juft", "44 juft"], 0),
            ("Gemoglobin tarkibidagi temir ioni qaysi oksidlanish darajasida kislorodni bog'laydi?", ["Fe²⁺", "Fe³⁺", "Fe⁴⁺", "Fe⁰"], 0),
            ("Odam organizmida siydikchil (mochevina) qaysi organda sintezlanadi?", ["Jigarda", "Buyrakda", "Talokda", "Oshqozon osti bezida"], 0),
            ("Bosh miya qismlaridan qaysi biri muvozanat va harakat koordinatsiyasi uchun javobgar?", ["Miyacha", "Uzunchoq miya", "O'rta miya", "Gipotalamus"], 0),
        ],
    },
    "chemistry": {
        "title": "🧪 Kimyo & Moddalar Tuzilishi (DTM)",
        "questions": [
            ("Oddiy sharoitda suyuq holatda bo'ladigan yagona metallmas element qaysi?", ["Brom (Br2)", "Simob (Hg)", "Xlor (Cl2)", "Yod (I2)"], 0),
            ("H₂SO₄ molekulasida oltingugurtning oksidlanish darajasi va valentligi qanday?", ["+6 va IV", "+6 va VI", "+4 va IV", "+4 va VI"], 0),
            ("Quyidagi moddalardan qaysi biri amfoter xossaga ega?", ["Al(OH)3", "NaOH", "H2SO4", "BaO"], 0),
            ("Alkanlarning umumiy gomologik formulasi qaysi?", ["CnH2n+2", "CnH2n", "CnH2n-2", "CnH2n-6"], 0),
            ("Vodorod ko'rsatkichi pH = 3 bo'lgan eritmadagi vodorod ionlari [H+] konsentratsiyasi qancha (mol/l)?", ["10⁻³ mol/l", "10⁻¹¹ mol/l", "3 mol/l", "10³ mol/l"], 0),
            ("Oddiy sharoitda eng yuqori elektr o'tkazuvchanlikka ega bo'lgan metall qaysi?", ["Kumush (Ag)", "Mis (Cu)", "Oltin (Au)", "Alyuminiy (Al)"], 0),
            ("Qaysi gaz havoda kislotali yomg'irlar hosil bo'lishining asosiy sababchisi hisoblanadi?", ["SO2", "CH4", "CO", "N2"], 0),
            ("Mendeleyev davriy sistemasida elektrmanfiyligi eng yuqori bo'lgan element qaysi?", ["Ftor (F)", "Kislorod (O)", "Xlor (Cl)", "Fransiy (Fr)"], 0),
            ("Uglerodning eng qattiq tabiiy allotropik shakl o'zgarishi qaysi?", ["Olmos", "Grafit", "Karbin", "Fulleren"], 0),
            ("Kaliy permanganat (KMnO4) parchalanganda laboratoriyada qaysi gaz olinadi?", ["O2", "H2", "Cl2", "N2"], 0),
            ("Oddiy sharoitda suvda erimaydigan tuzni toping:", ["BaSO4", "NaCl", "KNO3", "CaCl2"], 0),
            ("Eritmada lakmus qog'ozi ishqoriy muhitda qanday rangga kiradi?", ["Ko'k", "Qizil", "Sariq", "Rangsiz"], 0),
        ],
    },
    "history": {
        "title": "🏛 Tarix & Geografiya (DTM)",
        "questions": [
            ("Amir Temur va Boyazid Yildirim o'rtasidagi Anqara jangi qachon sodir bo'lgan?", ["1402-yil 20-iyul", "1395-yil 15-aprel", "1399-yil 12-sentyabr", "1405-yil 18-fevral"], 0),
            ("Qadimgi Baqtriya davlatining poytaxti qaysi shahar bo'lgan?", ["Zariaspa (Baqtra)", "Marokanda", "Afrosiyob", "Dovon"], 0),
            ("Birinchi jahon urushini rasman yakunlagan Versal tinchlik shartnomasi qaysi yili imzolangan?", ["1919-yil", "1918-yil", "1920-yil", "1921-yil"], 0),
            ("Qoraxoniylar davlatida Islom dini davlat dini sifatida qaysi hukmdor davrida e'lon qilingan?", ["Sotuq Bug'roxon", "Nasr ibn Ali", "Ibrohim Bo'ritegin", "Yusuf Qodirxon"], 0),
            ("1868-yilgi Zirabuloq jangida qaysi ikki tomon qo'shinlari to'qnashgan?", ["Rossiya imperiyasi va Buxoro amirligi", "Rossiya va Qo'qon xonligi", "Xiva xonligi va Eron", "Buxoro va Afg'oniston"], 0),
            ("Miloddan avvalgi 530-yilda To'maris qaysi Eron podshohini mag'lub etgan?", ["Kir II", "Doro I", "Kserks", "Kambiz"], 0),
            ("Mirzo Ulug'bek Samarqand rasadxonasida osmon jismlarini kuzatish uchun o'rnatgan asosiy ulkan asbob nima?", ["Sekstant (Kvadrant)", "Asturlob", "Optik teleskop", "Kompas"], 0),
            ("O'rta asr turkiy adabiyotining durdonasi hisoblangan 'Qutadg'u bilig' asari muallifi kim?", ["Yusuf Xos Hojib", "Mahmud Qoshg'ariy", "Ahmad Yugnakiy", "Xo'ja Ahmad Yassaviy"], 0),
            ("Buxoro Xalq Sovet Respublikasi (BXSR) qachon tashkil etilgan?", ["1920-yil oktyabr", "1917-yil noyabr", "1924-yil may", "1918-yil mart"], 0),
            ("O'zbekiston Respublikasining mustaqilligi qaysi anjumanda e'lon qilingan?", ["Oliy Kengashning navbatdan tashqari sessiyasida", "Vazirlar Mahkamasida", "Umumxalq referendumida", "Markaziy Kengashda"], 0),
            ("Dunyodagi eng chuqur chuchuk suvli ko'l qaysi?", ["Baykal ko'li", "Viktoriya", "Tanganika", "Yuqori ko'l"], 0),
            ("Yer sharidagi eng uzun tog' tizmasi qaysi?", ["And tog'lari", "Himolay", "Kordilyera", "Ural"], 0),
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
            [InlineKeyboardButton(text="📢 Kanalga so'rov yuborish", url=CHANNEL_LINK)],
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


async def process_referral_reward(bot:
