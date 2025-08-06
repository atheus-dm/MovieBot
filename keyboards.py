from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    buttons = [
        [InlineKeyboardButton("🔎 Поиск по ключевому слову", callback_data="search_keyword")],
        [InlineKeyboardButton("🎬 Поиск по жанрам и диапазону годов", callback_data="search_genre")],
        [InlineKeyboardButton("🔎 Поиск по актёру", callback_data="search_actor")],
        [InlineKeyboardButton("🌍 Фильмы по языку", callback_data="search_language")],
        [InlineKeyboardButton("🛒 Доступность фильма", callback_data="availability")],
        [InlineKeyboardButton("🎦 Недавно добавленные фильмы", callback_data="recent")],
        [InlineKeyboardButton("📈 Длинные(более 120 мин.) или 18+ фильмы", callback_data="special")],
        [InlineKeyboardButton("👤 Моя история запросов", callback_data="history")]
    ]
    return InlineKeyboardMarkup(buttons)


