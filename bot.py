Airaiki, [23.11.2025 17:20]
# Infinity Flow 2025 — 12 уровней 1-2-4 — ФИНАЛЬНАЯ ВЕРСИЯ
import telebot
from telebot import types
import sqlite3

TOKEN = "8517714019:AAFn-clTB2lIJsViyFXnJaAChqkFBSvvPg8"
ADMIN_ID = 969399365
WINNERS_CHAT = -1002438176538  # ← потом заменишь на свой чат победителей

bot = telebot.TeleBot(TOKEN)
db = sqlite3.connect("infinity.db", check_same_thread=False)
c = db.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (
    tg INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    level INTEGER DEFAULT 1,
    position TEXT DEFAULT 'inv',  -- inv / partner_left / partner_right / leader
    invited INTEGER DEFAULT 0,
    paid INTEGER DEFAULT 0        -- 0=нет, 1=отметил, 2=подтверждено
);
CREATE TABLE IF NOT EXISTS boards (
    level INTEGER PRIMARY KEY,
    leader_tg INTEGER,
    partner_l INTEGER,
    partner_r INTEGER
);
''')
db.commit()

# Ты — стартовый лидер всех 12 уровней
for lvl in range(1, 13):
    c.execute("INSERT OR IGNORE INTO boards (level, leader_tg) VALUES (?, ?)", (lvl, ADMIN_ID))
db.commit()

def amount(level): return 500 * (2 ** (level - 1))
def commission(level): return 0 if level < 5 else min(10 + (level - 5) * 2, 20)

def draw_board(tg):
    level = c.execute("SELECT level FROM users WHERE tg=?", (tg,)).fetchone()[0]
    amt = amount(level)

    leader_tg = c.execute("SELECT leader_tg FROM boards WHERE level=?", (level,)).fetchone()[0]
    leader_name = "ТЫ (Админ)" if leader_tg == tg else c.execute("SELECT name FROM users WHERE tg=?", (leader_tg,)).fetchone()[0].split()[0]

    pl = c.execute("SELECT name FROM users WHERE tg=(SELECT partner_l FROM boards WHERE level=?)", (level,)).fetchone()
    pr = c.execute("SELECT name FROM users WHERE tg=(SELECT partner_r FROM boards WHERE level=?)", (level,)).fetchone()
    partner_l = pl[0].split()[0] + " ✅" if pl else "—"
    partner_r = pr[0].split()[0] + " ✅" if pr else "—"

    inv = c.execute("SELECT name, paid FROM users WHERE level=? AND position='inv'", (level,)).fetchall()[:4]
    invs = ""
    for i, (name, paid) in enumerate(inv, 1):
        status = "✅" if paid == 2 else "⏳"
        invs += f"{i}. {name.split()[0]} {status}\n"
    while len(invs.splitlines()) < 4:
        invs += f"{len(invs.splitlines())+1}. —\n"

    text = f'''
УРОВЕНЬ {level} — ВХОД {amt:,} сом
{"Комиссия админу: " + str(commission(level)) + "%" if commission(level)>0 else ""}

          👑 ЛИДЕР 👑
            {leader_name}

    Партнёр Лево        Партнёр Право
       {partner_l}          {partner_r}

    Инвесторы:
{invs}
Переводи {amt:,} сом ЛИДЕРУ прямо сейчас!
    '''.strip()
    return text

@bot.message_handler(commands=['start'])
def start(m):
    tg = m.from_user.id
    if c.execute("SELECT tg FROM users WHERE tg=?", (tg,)).fetchone():
        bot.send_message(tg, "Ты уже в системе!", reply_markup=menu())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Поделиться номером", request_contact=True))
    bot.send_message(tg, "Добро пожаловать в Infinity Flow\n12 уровней роста ×2\nПоделись номером →", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def reg(m):
    tg = m.from_user.id
    phone = m.contact.phone_number
    name = f"{m.from_user.first_name} {m.from_user.last_name or ''}".strip()
    c.execute("INSERT INTO users (tg, name, phone) VALUES (?,?,?)", (tg, name, phone))
    db.commit()
    link = f"https://t.me/{bot.get_me().username}?start={tg}"
    bot.send_message(tg, f"Готово! Ты на УРОВНЕ 1\n\n{draw_board(tg)}\n\nТвоя ссылка:\n{link}", reply_markup=menu())

def menu():
    k = types.ReplyKeyboardMarkup(resize_keyboard=True)
    k.add("Моя доска", "Я перевёл")
    return k

@bot.message_handler(func=lambda m: m.text == "Моя доска")
def board_cmd(m):
    bot.send_message(m.chat.id, draw_board(m.from_user.id), reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == "Я перевёл")
def paid(m):
    tg = m.from_user.id
    level = c.execute("SELECT level FROM users WHERE tg=?", (tg,)).fetchone()[0]
    c.execute("UPDATE users SET paid=1 WHERE tg=?", (tg,))

Airaiki, [23.11.2025 17:20]
db.commit()
    bot.send_message(tg, "Отмечено! Жду подтверждения лидера.")
    leader = c.execute("SELECT leader_tg FROM boards WHERE level=?", (level,)).fetchone()[0]
    bot.send_message(leader, f"Уровень {level}: {m.from_user.first_name} отметил перевод {amount(level):,} сом",
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("Подтвердить", callback_data=f"ok_{tg}")))

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def confirm(c):
    tg = int(c.data.split("_")[1])
    level = c.execute("SELECT level FROM users WHERE tg=?", (tg,)).fetchone()[0]
    c.execute("UPDATE users SET paid=2 WHERE tg=?", (tg,))
    db.commit()
    bot.send_message(tg, "Перевод подтверждён!")
    check_board_close(level)

def check_board_close(level):
    paid_count = c.execute("SELECT COUNT(*) FROM users WHERE level=? AND paid=2 AND position='inv'", (level,)).fetchone()[0]
    if paid_count != 4: return

    leader_tg = c.execute("SELECT leader_tg FROM boards WHERE level=?", (level,)).fetchone()[0]
    leader_name = c.execute("SELECT name FROM users WHERE tg=?", (leader_tg,)).fetchone()[0].split()[0]
    bot.send_message(WINNERS_CHAT, f"УРОВЕНЬ {level} ЗАКРЫТ!\nЛидер {leader_name} получил 4 × {amount(level):,} = {amount(level)*4:,} сом\nПоздравляем!")

    next_level = level + 1 if level < 12 else 1
    users_to_move = c.execute("SELECT tg FROM users WHERE level=? AND position!='leader'", (level,)).fetchall()[:6]
    new_leader = c.execute("SELECT tg FROM users WHERE level=? AND position='partner_left'", (level,)).fetchone()
    new_leader = new_leader[0] if new_leader else users_to_move[0][0]

    c.execute("UPDATE boards SET leader_tg=? WHERE level=?", (new_leader, next_level))
    for (tg,) in users_to_move:
        c.execute("UPDATE users SET level=?, paid=0, position='inv' WHERE tg=?", (next_level, tg))
    db.commit()

    if level >= 5:
        comm = amount(level) * 4 * commission(level) // 100
        bot.send_message(ADMIN_ID, f"Комиссия с уровня {level}: {comm:,} сом — жди переводов от участников")

    for (tg,) in users_to_move:
        bot.send_message(tg, f"УРОВЕНЬ {level} ЗАКРЫТ!\nТы перешёл на уровень {next_level}\nВход: {amount(next_level):,} сом\n\n{draw_board(tg)}")

print("Infinity Flow 2025 запущен!")
bot.infinity_polling()
