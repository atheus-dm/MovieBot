from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import search_by_keyword
from db.mongo import log_search

KEYWORD_INPUT = 1
MAIN_MENU = 0

async def keyword_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["keyword_offset"] = 0
    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
    await update.callback_query.edit_message_text(
        "Введите ключевое слово для поиска:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return KEYWORD_INPUT

async def keyword_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()

    if not keyword or len(keyword) < 2:
        await update.message.reply_text("❗ Введите более осмысленное ключевое слово.")
        return KEYWORD_INPUT

    results = search_by_keyword(keyword)
    context.user_data["keyword_results"] = results
    context.user_data["keyword_offset"] = 0

    log_search("keyword", {
        "query": keyword,
        "user_id": update.effective_user.id
    }, len(results))

    return await keyword_show_page(update, context)

async def keyword_show_page(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data.get("keyword_results", [])
    offset = context.user_data.get("keyword_offset", 0)
    page = results[offset:offset+10]

    if not page:
        text = "🔍 По вашему запросу ничего не найдено."
    else:
        text = f"🎬 Найденные фильмы ({len(results)}):\n\n" + "\n\n".join(page)

    buttons = []
    if offset + 10 < len(results):
        buttons.append([InlineKeyboardButton("👉 Следующие 10", callback_data="keyword_next")])

    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=markup)
    elif hasattr(update_or_query, "callback_query") and update_or_query.callback_query:
        chat_id = update_or_query.callback_query.message.chat.id
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

    return MAIN_MENU

async def keyword_next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["keyword_offset"] += 10
    return await keyword_show_page(update, context)

# 🔁 Повтор из истории
async def repeat_keyword_search(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    query = data.get("query", "")
    results = search_by_keyword(query)
    context.user_data["keyword_results"] = results
    context.user_data["keyword_offset"] = 0
    return await keyword_show_page(update, context)
