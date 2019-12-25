import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode



############################ TODOs #########################################

def todo_member_keyboard(chat_id, bot, todolist):

    # Get user IDs members from database
    users = db.getUsersIdFromChat(chat_id)
    inline_array = []
    for user in users:
        usr = bot.getChatMember(chat_id=int(chat_id), user_id=user['user_id'])
        inline_array.append(InlineKeyboardButton(usr['user']['first_name'], callback_data=usr['user']['id']))

    if todolist:
        inline_array.append(InlineKeyboardButton("Todos los usuarios", callback_data=-1))

    keyboard_elements = [[element] for element in inline_array]

    return InlineKeyboardMarkup(keyboard_elements)

def todo_category_keyboard(chat_id, todolist):
    # Get categories IDs from database for a chat
    categories = db.getCategoriesIdFromChat(chat_id)
    inline_array = []
    for category in categories:
        inline_array.append(InlineKeyboardButton(category['name'], callback_data=category['id']))
    if todolist:
        inline_array.append(InlineKeyboardButton('Todas las categorias', callback_data=-1))
    else:
        inline_array.append(InlineKeyboardButton('Crea una categoria', callback_data=-1))
    keyboard_elements = [[element] for element in inline_array]
    return InlineKeyboardMarkup(keyboard_elements)



def binary_keyboard():
    keyboard = [[InlineKeyboardButton('Yes', callback_data='1')],
               [InlineKeyboardButton('No', callback_data='0')]]

    return InlineKeyboardMarkup(keyboard)