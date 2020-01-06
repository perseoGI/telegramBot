import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from enum import Enum
from . import callbacks as Callback

############################ TODOs #########################################

# def todo_member_keyboard(chat_id, bot, todolist):
#
#     # Get user IDs members from database
#     users = db.getUsersIdFromChat(chat_id)
#     inline_array = []
#     db.connectDB()
#     for user in users:
#         usr = bot.getChatMember(chat_id=int(chat_id), user_id=user['user_id'])
#         inline_array.append(InlineKeyboardButton(usr['user']['first_name'], callback_data=usr['user']['id']))
#     db.closeDB()
#
#     if todolist:
#         inline_array.append(InlineKeyboardButton("Todos los usuarios", callback_data=-1))
#
#     keyboard_elements = [[element] for element in inline_array]
#
#     return InlineKeyboardMarkup(keyboard_elements)



def todo_member_keyboard(users_id, chat_id, bot, todolist=False):

    # Get user IDs members from database

    inline_array = []
    # db.connectDB()
    for user_id in users_id:
        usr = bot.getChatMember(chat_id=int(chat_id), user_id=user_id)
        inline_array.append(InlineKeyboardButton(usr['user']['first_name'], callback_data=usr['user']['id']))
    # db.closeDB()

    if todolist:
        inline_array.append(InlineKeyboardButton("Todos los usuarios", callback_data=-1))

    keyboard_elements = [[element] for element in inline_array]

    return InlineKeyboardMarkup(keyboard_elements)



def todo_category_keyboard(chat_id, todolist):
    # Get categories IDs from database for a chat
    categories = db.getCategoriesIdFromChat(chat_id)
    inline_array = []
    db.connectDB()
    for category in categories:
        inline_array.append(InlineKeyboardButton(category['name'], callback_data=category['id']))
    if todolist:
        inline_array.append(InlineKeyboardButton('Todas las categorias', callback_data=-1))
    else:
        inline_array.append(InlineKeyboardButton('Crea una categoria', callback_data=-1))

    db.closeDB()
    keyboard_elements = [[element] for element in inline_array]
    return InlineKeyboardMarkup(keyboard_elements)



def binary_keyboard():
    keyboard = [[InlineKeyboardButton('Yes', callback_data='1')],
               [InlineKeyboardButton('No', callback_data='0')]]

    return InlineKeyboardMarkup(keyboard)



def todolist_item_keyboard(limit=None, completed=None):
    keyboard = [None] * 4
    keyboard[0] = [InlineKeyboardButton("Un-complete", callback_data=str(Callback.ACTION_UNCOMPLETE)) if completed else
                   InlineKeyboardButton("Complete", callback_data=str(Callback.ACTION_COMPLETE))]
    keyboard[1] = [InlineKeyboardButton("Postpone", callback_data=str(Callback.ACTION_POSTPONE))]

    keyboard[2] = [InlineKeyboardButton("Edit", callback_data=str(Callback.ACTION_EDIT))]

    keyboard[3] = [InlineKeyboardButton(" ", callback_data=str(Callback.ACTION_NONE)) if limit in ('L', 'B') else
                   InlineKeyboardButton("←", callback_data=str(Callback.ACTION_BACK)),

                   InlineKeyboardButton("Finish", callback_data=str(Callback.ACTION_FINISH)),

                   InlineKeyboardButton(" ", callback_data=str(Callback.ACTION_NONE)) if limit in ('R', 'B') else
                   InlineKeyboardButton("→", callback_data=str(Callback.ACTION_NEXT))]

    return InlineKeyboardMarkup(keyboard)



def todocategory_options_keyboard():
    keyboard = []
    keyboard.append(InlineKeyboardButton("Create category", callback_data=Callback.CREATE_CATEGORY))
    keyboard.append(InlineKeyboardButton("Delete category", callback_data=Callback.DELETE_CATEGORY))
    keyboard.append(InlineKeyboardButton("Edit category", callback_data=Callback.EDIT_CATEGORY))

    return InlineKeyboardMarkup([button] for button in keyboard)