from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import get_main_menu  # 👈 если ты используешь эту функцию

async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🔙 Вы вернулись в главное меню. Чем займёмся?",
        reply_markup=get_main_menu()  # 👈 это покажет главное меню снова
    )
    return 0  # MAIN_MENU

