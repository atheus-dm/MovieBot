from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.mongo import get_recent_logs, get_top_queries
from db.mysql import (
    search_by_keyword,
    search_by_genre_year,
    search_actors_by_name,
    search_by_language,
    get_genres,
    get_language_map
)
from handlers.recent_handler import repeat_recent
from handlers.special_handler import repeat_special
from handlers.genre_handler import repeat_genre_year
from handlers.availability_handler import repeat_availability
from handlers.language_handler import repeat_language
from utils import validate_year_input

MAIN_MENU = 0
HISTORY_REPEAT = 50

genre_map = {g["category_id"]: g["name"] for g in get_genres()}
language_map = get_language_map()

def format_query_label(params: dict, search_type: str | None = None) -> str:
    if search_type == "recent_films":
        return "Недавно добавленные фильмы"
    elif search_type == "special_films":
        return "Длинные(более 120 мин.) или 18+ фильмы"
    elif "language_id" in params:
        lang_id = params["language_id"]
        lang_name = language_map.get(lang_id, f"ID {lang_id}")
        return f"Поиск по языку: {lang_name}"
    elif "genre_ids" in params and "year_from" in params and "year_to" in params:
        genre_names = [genre_map.get(gid, str(gid)) for gid in params["genre_ids"]]
        genres = ", ".join(genre_names)
        return f"Жанры: [{genres}], Годы: {params['year_from']}–{params['year_to']}"
    elif search_type == "actor_search":
        return f"Поиск по актёру: «{params.get('query', '')}»"
    elif "query" in params:
        return f"По ключевому слову: «{params['query']}»"
    elif "title" in params:
        return f"Доступность: «{params['title']}»"
    else:
        return "Нестандартный запрос"

async def history_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id

    logs = get_recent_logs(user_id)
    top_queries = get_top_queries()

    text_parts = []

    if top_queries:
        text_parts.append("<b>📊 Топ 5 запросов:</b>")
        for i, entry in enumerate(top_queries, 1):
            params = entry["_id"]
            search_type = entry.get("search_type")
            label = format_query_label(params, search_type)
            count = entry["count"]
            time = entry["last_used"].strftime("%Y-%m-%d %H:%M")
            text_parts.append(f"{i}. 🔎 {label}\n   📈 {count} раз · 🕓 {time}")
    else:
        text_parts.append("📊 Нет популярных запросов.")

    if logs:
        text_parts.append("<b>🕰️ Мои последние запросы:</b>")
        for i, log in enumerate(logs[:5], 1):  # ⛔ Ограничение до 5
            label = format_query_label(log["params"], log.get("search_type"))
            time = log["timestamp"].strftime("%Y-%m-%d %H:%M")
            text_parts.append(f"{i}. 🔎 {label} · 🕓 {time}")

    else:
        text_parts.append("❌ У вас пока нет истории запросов.")

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔚 Выйти", callback_data="exit")]
    ])

    await update.callback_query.edit_message_text("\n\n".join(text_parts), reply_markup=markup, parse_mode="HTML")
    return MAIN_MENU


async def history_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    index = int(update.callback_query.data.split("_")[1])
    logs = context.user_data.get("history_logs", [])
    if index >= len(logs):
        await update.callback_query.edit_message_text("⚠️ Запрос не найден.")
        return MAIN_MENU

    log = logs[index]
    search_type = log.get("search_type")
    params = log["params"]

    if search_type == "recent_films":
        films = params.get("films", [])
        return await repeat_recent(update, context, films)
    elif search_type == "special_films":
        films = params.get("films", [])
        return await repeat_special(update, context, films)
    elif search_type == "genre_year":
        return await repeat_genre_year(update, context, params)
    elif search_type == "availability":
        return await repeat_availability(update, context, params)
    elif search_type == "language":
        return await repeat_language(update, context, params)

    results = []

    if search_type == "keyword":
        results = search_by_keyword(params.get("query", ""))
    elif search_type == "actor_search":
        query = params.get("query", "")
        actors = search_actors_by_name(query)
        results = [f"🎭 {a['first_name']} {a['last_name']}" for a in actors]
    elif search_type == "language":
        language_id = params.get("language_id")
        if language_id:
            results = search_by_language(language_id)

    if not results:
        await update.callback_query.edit_message_text("🔁 Повтор: ничего не найдено.")
    else:
        buttons = [[InlineKeyboardButton("🔚 Выйти", callback_data="exit")]]
        await update.callback_query.edit_message_text(
            "🔁 Повторный результат:\n\n" + "\n".join(results),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    return MAIN_MENU
