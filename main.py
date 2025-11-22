import json
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "BOT_TOKEN"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ------------------------------
# ФАЙЛ ХРАНЕНИЯ РАСПИСАНИЙ ПОЛЬЗОВАТЕЛЕЙ
# ------------------------------
try:
    with open("user_schedules.json", "r", encoding="utf-8") as f:
        SCHEDULES = json.load(f)
except:
    SCHEDULES = {}

def save_schedules():
    with open("user_schedules.json", "w", encoding="utf-8") as f:
        json.dump(SCHEDULES, f, ensure_ascii=False, indent=4)

# ------------------------------
# ФАЙЛ ЗАМЕТОК
# ------------------------------
try:
    with open("notes.json", "r", encoding="utf-8") as f:
        NOTES = json.load(f)
except:
    NOTES = {}

def save_notes():
    with open("notes.json", "w", encoding="utf-8") as f:
        json.dump(NOTES, f, ensure_ascii=False, indent=4)

# ------------------------------
# КЛАВИАТУРЫ
# ------------------------------
def main_menu():
    kb = [
        [KeyboardButton(text="Создать расписание")],
        [KeyboardButton(text="Расписание")],
        [KeyboardButton(text="Добавить заметку"), KeyboardButton(text="Мои заметки")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ------------------------------
# ДНИ НЕДЕЛИ
# ------------------------------
DAYS = [
    "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота"
]

# ------------------------------
# ХРАНЕНИЕ СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ
# ------------------------------
USER_STATE = {}  # {user_id: {"day_index": 0}}

# ------------------------------
# СТАРТ
# ------------------------------
@dp.message(CommandStart())
async def start(msg: types.Message):
    user_id = str(msg.from_user.id)

    if user_id not in SCHEDULES:
        SCHEDULES[user_id] = {
            day: "" for day in DAYS
        }
        save_schedules()

    await msg.answer(
        "Привет! Я бот расписания и заметок.\nВыбери действие:",
        reply_markup=main_menu()
    )

# ------------------------------
# СОЗДАНИЕ РАСПИСАНИЯ
# ------------------------------
@dp.message()
async def handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    text = msg.text

    # Если пользователь в процессе ввода расписания
    if user_id in USER_STATE:
        day_index = USER_STATE[user_id]["day_index"]
        day = DAYS[day_index]

        # Сохраняем расписание дня
        SCHEDULES[user_id][day] = text
        save_schedules()

        day_index += 1

        if day_index >= len(DAYS):
            del USER_STATE[user_id]
            await msg.answer("✔ Расписание сохранено!", reply_markup=main_menu())
        else:
            USER_STATE[user_id]["day_index"] = day_index
            next_day = DAYS[day_index]
            await msg.answer(f"Введите расписание на день: {next_day}")
        return

    # Создать расписание
    if text == "Создать расписание":
        USER_STATE[user_id] = {"day_index": 0}
        await msg.answer("Введите расписание на день: Понедельник")
        return

    # Показать расписание
    if text == "Расписание":
        schedule = SCHEDULES.get(user_id, {})
        out = "📘 Ваше расписание:\n\n"
        for day in DAYS:
            out += f" {day}:\n{schedule.get(day, '—')}\n\n"
        await msg.answer(out)
        return

    # Добавить заметку (кнопка)
    if text == "Добавить заметку":
        await msg.answer("Используйте:\n/addnote YYYY-MM-DD текст заметки")
        return

    # Мои заметки
    if text == "Мои заметки":
        if user_id not in NOTES or len(NOTES[user_id]) == 0:
            await msg.answer("У вас пока нет заметок.")
        else:
            t = "📌 Ваши заметки:\n\n"
            for note in NOTES[user_id]:
                t += f"📅 {note['date']}\n📝 {note['text']}\n\n"
            await msg.answer(t)
        return

    await msg.answer("Не понимаю команду.")

# ------------------------------
# ДОБАВЛЕНИЕ ЗАМЕТКИ
# ------------------------------
@dp.message(Command("addnote"))
async def add_note_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    text = msg.text.replace("/addnote", "").strip()

    try:
        date_str, note_text = text.split(" ", 1)
    except:
        await msg.answer("Использование:\n/addnote YYYY-MM-DD текст")
        return

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except:
        await msg.answer("Дата должна быть в формате YYYY-MM-DD")
        return

    if user_id not in NOTES:
        NOTES[user_id] = []

    NOTES[user_id].append({
        "date": date_str,
        "text": note_text
    })

    save_notes()
    await msg.answer(f"Заметка сохранена!\n📅 {date_str}\n📝 {note_text}")

# ------------------------------
# НАПОМИНАНИЯ ЗА ДЕНЬ
# ------------------------------
async def reminder_task():
    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        for user_id, notes in NOTES.items():
            for note in notes:
                if note["date"] == tomorrow:
                    try:
                        await bot.send_message(
                            int(user_id),
                            f"⚠️ Напоминание!\nЗавтра: {note['text']}"
                        )
                    except:
                        pass

        await asyncio.sleep(3600)

# ------------------------------
# ЗАПУСК
# ------------------------------
async def main():
    asyncio.create_task(reminder_task())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
