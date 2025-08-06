from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import get_languages, search_by_language
from db.mongo import log_search

LANGUAGE_SELECT = 30
MAIN_MENU = 0

async def language_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    languages = get_languages()
    buttons = [
        [InlineKeyboardButton(lang['name'], callback_data=f"language_{lang['language_id']}")]
        for lang in languages
    ]
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text("Выберите язык:", reply_markup=markup)
    return LANGUAGE_SELECT

async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    try:
        language_id = int(data.split("_")[1])
    except (IndexError, ValueError):
        await update.callback_query.edit_message_text("❗ Ошибка при выборе языка.")
        return MAIN_MENU

    context.user_data["language_params"] = {
        "language_id": language_id,
        "offset": 0
    }

    all_results = search_by_language(language_id)
    log_search("language", {
        "language_id": language_id,
        "user_id": update.effective_user.id
    }, len(all_results))

    return await show_language_results(update, context)

async def show_language_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = context.user_data.get("language_params", {})
    offset = params.get("offset", 0)
    language_id = params.get("language_id")

    results = search_by_language(language_id)
    page = results[offset:offset+10]

    if not page:
        await update.callback_query.edit_message_text("😢 По выбранному языку фильмы не найдены.")
        return MAIN_MENU

    text = f"🌍 <b>Фильмы на выбранном языке ({len(results)}):</b>\n\n" + "\n\n".join(page)

    buttons = []
    if offset + 10 < len(results):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="language_next")])

    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    return MAIN_MENU

async def language_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["language_params"]["offset"] += 10
    return await show_language_results(update, context)

# 🔁 Повтор языка из истории
async def repeat_language(update: Update, context: ContextTypes.DEFAULT_TYPE, params: dict):
    language_id = params.get("language_id")
    if not language_id:
        await update.callback_query.edit_message_text("⚠️ Невозможно повторить поиск по языку.")
        return MAIN_MENU

    context.user_data["language_params"] = {
        "language_id": language_id,
        "offset": 0
    }

    return await show_language_results(update, context)
