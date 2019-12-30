import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatAction
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard

import time
from .common import send_message



def todocategory_start(update, context):

    chat_id = update.message.chat_id
    send_message(context.bot, chat_id, "Choose a category")
    return ConversationHandler.END

def todocategory_cancel(update, context):
    pass

todocategory_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('todocategory', todocategory_start)],
    states={
       # TODOLIST_CATEGORY: [CallbackQueryHandler(todolist_category)],

    },
    fallbacks=[CommandHandler('todolist_cancel', todocategory_cancel)]
)