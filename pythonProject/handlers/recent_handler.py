from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import get_recent_films
from db.mongo import log_search

MAIN_MENU = 0

async def recent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["recent_offset"] = 0

    # 🧠 Логируем запрос + сохраняем фильмы
    all_films = get_recent_films()
    log_search("recent_films", {
        "user_id": update.effective_user.id,
        "films": all_films
    }, len(all_films))

    return await show_recent_films(update, context)

async def show_recent_films(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offset = context.user_data.get("recent_offset", 0)
    films = get_recent_films()
    page = films[offset:offset+10]

    if not page:
        await update.callback_query.edit_message_text("😢 Недавние фильмы не найдены.")
        return MAIN_MENU

    text = "🎦 <b>Последние добавленные фильмы:</b>\n\n" + "\n\n".join(page)
    buttons = []

    if offset + 10 < len(films):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="recent_next")])

    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    return MAIN_MENU

async def recent_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["recent_offset"] += 10
    return await show_recent_films(update, context)

# 🔁 Повтор из истории
async def repeat_recent(update: Update, context: ContextTypes.DEFAULT_TYPE, films: list):
    context.user_data["recent_offset"] = 0
    context.user_data["recent_repeat_data"] = films
    return await show_recent_repeat(update, context)

async def show_recent_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offset = context.user_data.get("recent_offset", 0)
    films = context.user_data.get("recent_repeat_data", [])
    page = films[offset:offset+10]

    if not page:
        await update.callback_query.edit_message_text("😢 Повтор не удался, фильмы не найдены.")
        return MAIN_MENU

    text = "🔁 <b>Ваш прошлый запрос — Последние фильмы:</b>\n\n" + "\n\n".join(page)
    buttons = []

    if offset + 10 < len(films):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="recent_next")])

    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    return MAIN_MENU
