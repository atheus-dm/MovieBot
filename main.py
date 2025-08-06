import os
from dotenv import load_dotenv
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
# 🔐 Загружаем .env
load_dotenv()

# 👇 Импорты из проекта
from keyboards import get_main_menu
from handlers.keyword_handler import keyword_start, keyword_search, keyword_next_handler  # ✅ добавлен
from handlers.genre_handler import genre_start, genre_select, year_from_input, year_to_input, genre_next_handler
from handlers.actor_handler import actor_search_start, actor_search_input, actor_info_select
from handlers.language_handler import language_start, language_select, language_next_handler
from handlers.availability_handler import availability_start, availability_input
from handlers.recent_handler import recent_start, recent_next_handler
from handlers.special_handler import special_start, special_next_handler
from handlers.history_handler import history_start, history_repeat
from handlers.exit_handler import exit_handler

# 🧠 Состояния диалогов
MAIN_MENU, KEYWORD_INPUT = range(2)
GENRE_SELECT, YEAR_FROM, YEAR_TO = range(10, 13)
ACTOR_INPUT, ACTOR_SELECT = range(20, 22)
LANGUAGE_SELECT = 30
AVAILABILITY_INPUT = 40
HISTORY_REPEAT = 50
AVAILABILITY_SELECT_FILM = 41

# 🟢 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Добро пожаловать в MovieBot!", reply_markup=get_main_menu())
    return MAIN_MENU

# 🔁 Обработка главного меню и всех кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "search_keyword":
        return await keyword_start(update, context)
    elif data == "search_genre":
        return await genre_start(update, context)
    elif data.startswith("genre_"):
        return await genre_select(update, context)
    elif data == "search_actor":
        return await actor_search_start(update, context)
    elif data.startswith("actor_"):
        return await actor_info_select(update, context)
    elif data == "search_language":
        return await language_start(update, context)
    elif data.startswith("language_"):
        return await language_select(update, context)
    elif data == "availability":
        return await availability_start(update, context)
    elif data == "recent":
        return await recent_start(update, context)
    elif data == "special":
        return await special_start(update, context)
    elif data == "history":
        return await history_start(update, context)
    elif data.startswith("repeat_"):
        return await history_repeat(update, context)
    elif data == "exit":
        return await exit_handler(update, context)

    return MAIN_MENU

from handlers.availability_handler import availability_start, availability_input, availability_select_handler  # ✅ добавлено

# 🚀 Запуск
def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(genre_next_handler, pattern="^genre_next$"),
                CallbackQueryHandler(language_next_handler, pattern="^language_next$"),
                CallbackQueryHandler(recent_next_handler, pattern="^recent_next$"),
                CallbackQueryHandler(special_next_handler, pattern="^special_next$"),
                CallbackQueryHandler(keyword_next_handler, pattern="^keyword_next$"),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
                CallbackQueryHandler(handle_menu),
            ],
            KEYWORD_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_search),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            GENRE_SELECT: [
                CallbackQueryHandler(handle_menu, pattern="^genre_\\d+$"),
                CallbackQueryHandler(handle_menu, pattern="^genre_done$"),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            YEAR_FROM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, year_from_input),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            YEAR_TO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, year_to_input),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            ACTOR_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, actor_search_input),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            ACTOR_SELECT: [
                CallbackQueryHandler(handle_menu, pattern="^actor_\\d+$"),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            LANGUAGE_SELECT: [
                CallbackQueryHandler(handle_menu, pattern="^language_"),
                CallbackQueryHandler(language_next_handler, pattern="^language_next$"),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            AVAILABILITY_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, availability_input),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            AVAILABILITY_SELECT_FILM: [  # ✅ новый маршрут
                CallbackQueryHandler(availability_select_handler),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
            HISTORY_REPEAT: [
                CallbackQueryHandler(handle_menu, pattern="^repeat_"),
                CallbackQueryHandler(exit_handler, pattern="^exit$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv)
    application.run_polling()

if __name__ == "__main__":
    main()