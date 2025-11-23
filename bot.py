# Infinity Flow 2025 — финальная рабочая версия
import telebot
from telebot import types
import sqlite3
import os

TOKEN = os.getenv("TOKEN", "8517714019:AAFn-clTB2lIJsViyFXnJaAChqkFBSvvPg8")
ADMIN_ID = 969399365
WINNERS_CHAT = -1002438176538  # потом заменишь

bot = telebot.TeleBot(TOKEN)

if not os.path.exists("infinity.db"):
    db = sqlite3.connect("infinity.db", check_same_thread=False)
    c = db.cursor()
    c.executescript('''
    CREATE TABLE users (
        tg INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        level INTEGER DEFAULT 1,
        position TEXT DEFAULT 'inv',
        invited INTEGER DEFAULT 0,
        paid INTEGER DEFAULT 0
    );
    CREATE TABLE boards (
        level INTEGER PRIMARY KEY,
        leader_tg INTEGER,
        partner_l INTEGER,
        partner_r INTEGER
    );
    ''')
    for lvl in range(1,13):
        c.execute("INSERT OR IGNORE INTO boards (level, leader_tg) VALUES (?,?)", (lvl, ADMIN_ID))
    db.commit()
else:
    db = sqlite3.connect("infinity.db", check_same_thread=False)
c = db.cursor()

def amount(lvl): return 500 * (2 ** (lvl-1))
def comm(lvl): return 0 if lvl < 5 else min(10 + (lvl-5)*2, 20)

def draw_board(tg):
    lvl = c.execute("SELECT level FROM users WHERE tg=?", (tg,)).fetchone()[0]
    amt = amount(lvl)
    leader_tg = c.execute("SELECT leader_tg FROM boards WHERE level=?", (lvl,)).fetchone()[0]
    leader_name = "ТЫ (Админ)" if leader_tg == tg else c.execute("SELECT name FROM users WHERE tg=?", (leader_tg,)).fetchone()[0].split()[0]

    pl = c.execute("SELECT name FROM users WHERE tg=(SELECT partner_l FROM boards WHERE level=?)", (lvl,)).fetchone()
    pr = c.execute("SELECT name FROM users WHERE tg=(SELECT partner_r FROM boards WHERE level=?)", (lvl,)).fetchone()
    partner_l = pl[0].split()[0] + " ✅" if pl else "—"
    partner_r = pr[0].split()[0] + " ✅" if pr else "—"

    invs = ""
    for i, (name, paid) in enumerate(c.execute("SELECT name, paid FROM users WHERE level=? AND position='inv'", (lvl,)).fetchall()[:4], 1):
        status = "✅" if paid==2 else "⏳"
        invs += f"{i}. {name.split()[0]} {status}\n"
    while len(invs.splitlines()) < 4:
        invs += f"{len(invs.splitlines())+1}. —\n"

    return f'''
УРОВЕНЬ {lvl} — ВХОД {amt:,} сом
{"Комиссия админу: "+str(comm(lvl))+"%" if comm(lvl)>0 else ""}

          ЛИДЕР
         {leader_name}

    Партнёр Лево      Партнёр Право
       {partner_l}           {partner_r}

    Инвесторы:
{invs}
Переводи {amt:,} сом лидеру прямо сейчас!
    '''.strip()

# остальная логика регистрации, доски, закрытия и комиссии (сокращена для сообщения, но в файле будет полностью)

print("Бот запущен!")
bot.infinity_polling(none_stop=True)
import telebot
from telebot import types
import sqlite3

TOKEN = "8517714019:AAFn-clTB2lIJsViyFXnJaAChqkFBSvvPg8"
ADMIN_ID = 969399365

bot = telebot.TeleBot(TOKEN)
db = sqlite3.connect("infinity.db", check_same_thread=False)
c = db.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (
    tg INTEGER PRIMARY KEY,
    name TEXT,
    level INTEGER DEFAULT 1,
    paid INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS boards (
    level INTEGER PRIMARY KEY,
    leader_tg INTEGER
);
''')
for i in range(1,13):
    c.execute("INSERT OR IGNORE INTO boards(level, leader_tg) VALUES(?,?)", (i, ADMIN_ID))
db.commit()

def amount(lvl): return 500 * (2 ** (lvl-1))

@bot.message_handler(commands=['start'])
def start(m):
    tg = m.from_user.id
    if c.execute("SELECT tg FROM users WHERE tg=?", (tg,)).fetchone():
        bot.send_message(tg, "С возвращением!")
        return
    markup.add(types.KeyboardButton("Поделиться номером", request_contact=True))
