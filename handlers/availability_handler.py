from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import find_films_by_title, search_film_availability_by_id
from db.mongo import log_search

AVAILABILITY_INPUT = 40
AVAILABILITY_SELECT_FILM = 41
MAIN_MENU = 0

async def availability_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
    await update.callback_query.edit_message_text(
        "Введите название фильма, чтобы проверить его доступность:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return AVAILABILITY_INPUT

async def availability_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    if not title or len(title) < 2:
        await update.message.reply_text("❗ Введите корректное название фильма.")
        return AVAILABILITY_INPUT

    films = find_films_by_title(title)

    if not films:
        await update.message.reply_text("🔍 Фильм не найден.")
        return AVAILABILITY_INPUT

    context.user_data["availability_title"] = title

    if len(films) == 1:
        film = films[0]
        return await show_availability(update, context, film["film_id"], film["title"])

    buttons = [
        [InlineKeyboardButton(f"🎬 {film['title']}", callback_data=f"selectfilm_{film['film_id']}")]
        for film in films
    ]
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    await update.message.reply_text(
        "🔎 Найдено несколько фильмов. Выберите нужный:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return AVAILABILITY_SELECT_FILM

async def availability_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    if not data.startswith("selectfilm_"):
        await update.callback_query.edit_message_text("❗ Некорректный выбор фильма.")
        return MAIN_MENU

    film_id = int(data.replace("selectfilm_", ""))
    user_input = context.user_data.get("availability_title", "")
    films = find_films_by_title(user_input)
    film = next((f for f in films if f["film_id"] == film_id), None)
    title = film["title"] if film else "Неизвестно"

    return await show_availability(update, context, film_id, title)

async def show_availability(update: Update, context: ContextTypes.DEFAULT_TYPE, film_id: int, title: str):
    stores = search_film_availability_by_id(film_id)

    if not stores:
        message = f"🔍 Нет доступных копий для «{title}»."
    else:
        message = f"📦 Доступность для «{title}»:\n\n"
        for s in stores:
            message += (
                f"🏬 Магазин #{s['store_id']}\n"
                f"📍 {s['address']}, {s['district']}, {s['city']}, {s['country']}\n"
                f"📞 {s['phone']}\n"
                f"🎞️ Кол-во копий: {s['count']}\n\n"
            )

    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]

    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(buttons))

    log_search("availability", {
        "title": title,
        "film_id": film_id,
        "user_id": update.effective_user.id,
        "stores": stores
    }, len(stores))

    return MAIN_MENU

# 🔁 Повтор из истории
async def repeat_availability(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    title = data.get("title", "Неизвестно")
    stores = data.get("stores", [])

    if not stores:
        message = f"🔍 Нет доступных копий для «{title}»."
    else:
        message = f"🔁 Доступность для «{title}»:\n\n"
        for s in stores:
            message += (
                f"🏬 Магазин #{s['store_id']}\n"
                f"📍 {s['address']}, {s['district']}, {s['city']}, {s['country']}\n"
                f"📞 {s['phone']}\n"
                f"🎞️ Кол-во копий: {s['count']}\n\n"
            )

    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]

    await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(buttons))
    return MAIN_MENU
