import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
)
from calendarBot import telegramcalendar
from .keyboards import binary_keyboard, todocategory_options_keyboard

import time
from .common import send_message
from i18n import _


def todocategory_start(update, context):
    chat_id = update.message.chat_id
    send_message(
        context.bot,
        chat_id,
        _("Choose an option"),
        reply_markup=todocategory_options_keyboard(),
    )
    return ConversationHandler.END


def todocategory_cancel(update, context):
    pass


todocategory_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("todocategory", todocategory_start)],
    states={
        # TODOLIST_CATEGORY: [CallbackQueryHandler(todolist_category)],
    },
    fallbacks=[CommandHandler("todolist_cancel", todocategory_cancel)],
)
