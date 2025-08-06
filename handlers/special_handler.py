from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import get_special_films
from db.mongo import log_search

MAIN_MENU = 0

async def special_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["special_offset"] = 0

    all_results = get_special_films()
    log_search("special_films", {
        "user_id": update.effective_user.id,
        "films": all_results
    }, len(all_results))

    return await show_special_page(update, context, all_results)

async def show_special_page(update: Update, context: ContextTypes.DEFAULT_TYPE, all_results: list[str]):
    offset = context.user_data.get("special_offset", 0)
    page = all_results[offset:offset+10]

    if not page:
        buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
        await update.callback_query.edit_message_text(
            "❌ Длинные (более 120 мин.) или 18+ фильмы не найдены.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return MAIN_MENU

    text = f"📈 <b>Длинные (более 120 мин.) или 18+ фильмы ({len(all_results)}):</b>\n\n" + "\n\n".join(page)
    buttons = []
    if offset + 10 < len(all_results):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="special_next")])
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    return MAIN_MENU

async def special_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["special_offset"] += 10
    all_results = get_special_films()
    return await show_special_page(update, context, all_results)

# 🔁 Повтор из истории
async def repeat_special(update: Update, context: ContextTypes.DEFAULT_TYPE, films: list):
    context.user_data["special_offset"] = 0
    context.user_data["special_repeat_data"] = films
    return await show_special_repeat(update, context)

async def show_special_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offset = context.user_data.get("special_offset", 0)
    films = context.user_data.get("special_repeat_data", [])
    page = films[offset:offset+10]

    if not page:
        buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
        await update.callback_query.edit_message_text(
            "❌ Повтор не удался, фильмы не найдены.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return MAIN_MENU

    text = f"🔁 <b>Ваш прошлый запрос — Длинные или 18+ ({len(films)}):</b>\n\n" + "\n\n".join(page)
    buttons = []
    if offset + 10 < len(films):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="special_next")])
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    return MAIN_MENU
