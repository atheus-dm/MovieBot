from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import get_genres, search_by_genre_year
from db.mongo import log_search
from utils import validate_year_input

GENRE_SELECT, YEAR_FROM, YEAR_TO = range(10, 13)
MAIN_MENU = 0

async def genre_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    genres = get_genres()
    buttons = [
        [InlineKeyboardButton(g['name'], callback_data=f"genre_{g['category_id']}")]
        for g in genres
    ]
    buttons.append([InlineKeyboardButton("✅ Готово", callback_data="genre_done")])
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])

    context.user_data["selected_genres"] = []

    await update.callback_query.edit_message_text(
        "Выберите жанры (нажимайте по одному, потом ✅ Готово):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return GENRE_SELECT

async def genre_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    if data == "genre_done":
        if not context.user_data.get("selected_genres"):
            await update.callback_query.edit_message_text("❗ Вы не выбрали ни одного жанра.")
            return GENRE_SELECT

        buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
        await update.callback_query.edit_message_text("Введите начальный год (от 1990 до 2025):", reply_markup=InlineKeyboardMarkup(buttons))
        return YEAR_FROM

    try:
        genre_id = int(data.split("_")[1])
        selected = context.user_data.get("selected_genres", [])
        if genre_id not in selected:
            selected.append(genre_id)
            context.user_data["selected_genres"] = selected
    except (IndexError, ValueError):
        await update.callback_query.edit_message_text("❗ Ошибка при выборе жанра.")
        return GENRE_SELECT

    return GENRE_SELECT

async def year_from_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year = validate_year_input(update.message.text)
    if not year:
        await update.message.reply_text("❗ Некорректный год. Введите число от 1990 до 2025.")
        return YEAR_FROM

    context.user_data["year_from"] = year
    await update.message.reply_text("Введите конечный год:")
    return YEAR_TO

async def year_to_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year_to = validate_year_input(update.message.text)
    if not year_to:
        await update.message.reply_text("❗ Некорректный год. Введите число от 1990 до 2025.")
        return YEAR_TO

    year_from = context.user_data["year_from"]
    genre_ids = context.user_data["selected_genres"]

    full_results = search_by_genre_year(
        genre_ids=genre_ids,
        year_from=year_from,
        year_to=year_to,
        offset=0,
        limit=1000
    )

    context.user_data["genre_params"] = {
        "genre_ids": genre_ids,
        "year_from": year_from,
        "year_to": year_to,
        "offset": 0,
        "films": full_results
    }

    log_search("genre_year", {
        "genre_ids": genre_ids,
        "year_from": year_from,
        "year_to": year_to,
        "user_id": update.effective_user.id,
        "films": full_results
    }, len(full_results))

    return await show_genre_results(update, context)

async def show_genre_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = context.user_data.get("genre_params", {})
    offset = params.get("offset", 0)
    films = params.get("films", [])

    page = films[offset:offset+10]

    if not page:
        if update.message:
            await update.message.reply_text("😢 Ничего не найдено.")
        else:
            await update.callback_query.edit_message_text("😢 Ничего не найдено.")
        return MAIN_MENU

    text = f"🎬 <b>Найденные фильмы ({len(films)}):</b>\n\n" + "\n\n".join(page)
    buttons = []
    if offset + 10 < len(films):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="genre_next")])
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

    return MAIN_MENU

async def genre_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["genre_params"]["offset"] += 10
    return await show_genre_results(update, context)

# 🔁 Повтор из истории
async def repeat_genre_year(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    context.user_data["genre_params"] = {
        "genre_ids": data.get("genre_ids", []),
        "year_from": data.get("year_from", 2000),
        "year_to": data.get("year_to", 2025),
        "offset": 0,
        "films": data.get("films", [])
    }
    return await show_genre_results(update, context)
