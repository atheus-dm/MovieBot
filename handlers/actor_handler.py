from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mysql import search_actors_by_name, get_actor_info
from db.mongo import log_search

ACTOR_INPUT, ACTOR_SELECT = range(20, 22)
MAIN_MENU = 0

async def actor_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
    await update.callback_query.edit_message_text(
        "Введите имя или фамилию актёра для поиска:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ACTOR_INPUT

async def actor_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name or len(name) < 2:
        await update.message.reply_text("❗ Введите корректное имя или фамилию актёра.")
        return ACTOR_INPUT

    actors = search_actors_by_name(name)
    if not actors:
        await update.message.reply_text("🔍 Актёры не найдены.")
        return MAIN_MENU

    context.user_data["actor_query"] = name

    buttons = [
        [InlineKeyboardButton(f"{a['first_name']} {a['last_name']}", callback_data=f"actor_{a['actor_id']}")]
        for a in actors
    ]
    buttons.append([InlineKeyboardButton("🔚 Выйти", callback_data="exit")])
    markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("Выберите актёра:", reply_markup=markup)
    return ACTOR_SELECT

async def actor_info_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    try:
        actor_id = int(data.split("_")[1])
    except (IndexError, ValueError):
        await update.callback_query.edit_message_text("❗ Невозможно определить актёра.")
        return MAIN_MENU

    info = get_actor_info(actor_id)
    if not info or not info.get("films"):
        await update.callback_query.edit_message_text("❌ Информация об актёре не найдена.")
        return MAIN_MENU

    films = info["films"]
    film_list = "\n".join([
        f"– <b>{f['title']}</b> ({f['genre']}, {f['year']}, {f['rating']})"
        for f in films
    ])

    first_name = info.get("first_name", "")
    last_name = info.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    user_id = update.effective_user.id

    text = (
        f"🎭 <b>{full_name}</b>\n\n"
        f"🎬 Фильмы ({len(films)}):\n"
        f"{film_list}"
    )

    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    log_search("actor_search", {
        "user_id": user_id,
        "actor_id": actor_id,
        "query": full_name,
        "films": films
    }, len(films))

    return MAIN_MENU


# 🔁 Повтор из истории
async def repeat_actor_search(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    films = data.get("films", [])
    actor_name = data.get("query", "Актёр")

    if not films:
        await update.callback_query.edit_message_text("❌ Повтор не удался, фильмы не найдены.")
        return MAIN_MENU

    film_list = "\n".join([
        f"– <b>{f['title']}</b> ({f['genre']}, {f['year']}, {f['rating']})"
        for f in films
    ])

    text = (
        f"🔁 <b>Повтор: фильмы актёра «{actor_name}» ({len(films)}):</b>\n\n"
        f"{film_list}"
    )

    buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    return MAIN_MENU
