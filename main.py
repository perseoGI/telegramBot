from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

import requests
import re
import logging
import database as db
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

DESCRIPTION, CATEGORY, CREATE_CATEGORY, ANOTHER_ASSIGNMENT, ASSIGNMENT, TODO_END = range(6)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Soy el bot para el equipo de Planeanding, dejame ayudarte!")

def echo(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)


def get_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url

def get_image_url():
    allowed_extension = ['jpg','jpeg','png']
    file_extension = ''
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$",url).group(1).lower()
    return url

def bop(update, context):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=get_image_url())


############################ TODOS ##################################

def todo_start(update, context):
    logger.info("New todo from: %s, cat: %d, user: %d", update.message.from_user.name, update.message.chat_id, update.message.from_user.id)
    context.bot.send_message(text="En que consiste la tarea?", chat_id=update.message.chat_id)

    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user

    logger.info("Description of %s: %s", user.name, update.message.text)
    chat_id = update.message.chat_id

    context.bot.send_message(
        chat_id=chat_id,
        text="En que categoria lo incluirias?",
        reply_markup=todo_category_keyboard(chat_id, context.bot))

    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user.id)

    # Update model
    db.setPendingTodosDescription(
        chat_id=chat_id,
        user_id=update.message.from_user.id,
        description=update.message.text)

    return CATEGORY





def todo_category(update, context):
    user = update.callback_query.message.from_user
   # logger.info("Category of %s: %s", user.first_name, update.message.text)
    chat_id =update.callback_query.message.chat_id
    category = update.callback_query.data
    if category < 0:    # Create a new category
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Escriba el nombre de la nueva categoria",
                                      )
        return CREATE_CATEGORY

    else:
        # Update model
        db.setPendingTodosCategory(
            chat_id=chat_id,
            user_id=user.id,
            category=category)

        if (chat_id < 0):       # It is a group
            context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    text="Asigne la tarea",
                                    reply_markup=todo_member_keyboard(chat_id, context.bot))

            return ANOTHER_ASSIGNMENT
        # edit_message_text

        else:
            context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    text="Desea guardar la tarea?",
                                    reply_markup=binary_keyboard())
            return TODO_END


def todo_another_assignment(update, context):
    print("____________")
    user = update.callback_query.message.from_user

    msg = update.message.reply_to_message
    chatid = msg.chat_id
    userid = msg.from_user.id

    print("user bot ::::::::::::", chatid , userid)
    print()
    chat_id = update.callback_query.message.chat_id
    assigned_user_id = update.callback_query.data
    logger.info("Assignment of %s: %s", user.first_name, assigned_user_id)

    context.bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Desea asignar tarea a otro miembro mas?",
                                  reply_markup=binary_keyboard())

    # Store info in the database
    db.setPendingTodoAssingment(chat_id=chat_id, user_id=user.id, assigned_user_id=assigned_user_id)
    return ASSIGNMENT


def todo_assignment(update, context):

    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    print(answer)
    if answer == '1':     # Continue asking for assignments
        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Asigne la tarea",
                                        reply_markup=todo_member_keyboard(chat_id, context.bot))
        return ANOTHER_ASSIGNMENT

    else:               # Next step
        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Desea guardar la tarea?",
                                        reply_markup=binary_keyboard())
        return TODO_END


def todo_end(update, context):
    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.callback_query.message.from_user
    print(chat_id, user_id)
    if answer == '1':
        db.storePendingTodo(
            chat_id=chat_id,
            user_id=user_id)

        update.callback_query.edit_message_text("Tarea guardada!",
                                                message_id=update.callback_query.message.message_id,)
    else:
        db.clearPendingTodo(
            chat_id=chat_id,
            user_id=user_id)

        update.callback_query.edit_message_text("Tarea descartada",
                                                message_id=update.callback_query.message.message_id)

    return ConversationHandler.END



def todo_cancel(update, context):
    context.bot.get_chat()

    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tarea descartada!',
                              reply_markup=InlineKeyboardMarkup([])
                              )

    return ConversationHandler.END

########################### Category ###########################################

def create_category(update, context):
    chat_id =  update.callback_query.message.chat_id
    category_name = update.message.text
    db.createCategory(chat_id=chat_id, name=category_name)

    user_id = update.callback_query.message.from_user
    # TODO: refactorizar
    # Update model
    db.setPendingTodosCategory(
        chat_id=chat_id,
        user_id=user.id,
        category=category)

    if (chat_id < 0):  # It is a group
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text="Asigne la tarea",
            reply_markup=todo_member_keyboard(chat_id, context.bot))

        return ANOTHER_ASSIGNMENT
    # edit_message_text

    else:
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text="Desea guardar la tarea?",
            reply_markup=binary_keyboard())
        return TODO_END


############################ Keyboards #########################################

def todo_member_keyboard(chat_id, bot):

    # Get user IDs members from database
    users = db.getUsersIdFromChat(chat_id)
    inline_array = []
    for user in users:
        usr = bot.getChatMember(chat_id=int(chat_id), user_id=user['user_id'])
        inline_array.append(InlineKeyboardButton(usr['user']['first_name'], callback_data=usr['user']['id']))

    keyboard_elements = [[element] for element in inline_array]

    return InlineKeyboardMarkup(keyboard_elements)

def todo_category_keyboard(chat_id, bot):
    # Get categories IDs from database for a chat
    categories = db.getCategoriesIdFromChat(chat_id)
    inline_array = []
    for category in categories:
        inline_array.append(InlineKeyboardButton(category['name'], callback_data=category['id']))

    inline_array.append(InlineKeyboardButton('Crea una categoria', callback_data=-1))
    keyboard_elements = [[element] for element in inline_array]
    return InlineKeyboardMarkup(keyboard_elements)



def binary_keyboard():
    keyboard = [[InlineKeyboardButton('Yes', callback_data='1')],
               [InlineKeyboardButton('No', callback_data='0')]]

    return InlineKeyboardMarkup(keyboard)






def main():
    # Create database
    db.init_db()

    print("Setting up bot")
    updater = Updater('867661842:AAGr-zhF5UNvbvGl1hvT_l6Pacj2OYwDEY8',  use_context=True)
    dp = updater.dispatcher


    dp.add_handler(CommandHandler('bop',bop))

    dp.add_handler( CommandHandler('start', start))

    # dp.add_handler(MessageHandler(Filters.text, echo))

    dp.add_handler(CommandHandler('caps', caps))

    ######3
    # dp.add_handler(CommandHandler('todo', todo_start))
    # dp.add_handler(MessageHandler(Filters.text, todo_description),group=0)

    todo_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('todo', todo_start)],

        states={
            DESCRIPTION: [MessageHandler(Filters.text, todo_description)],
            CATEGORY: [CallbackQueryHandler(todo_category)],
            CREATE_CATEGORY: [MessageHandler(Filters.text, create_category)],
            ANOTHER_ASSIGNMENT: [CallbackQueryHandler(todo_another_assignment)],
            ASSIGNMENT: [CallbackQueryHandler(todo_assignment)],
            TODO_END: [CallbackQueryHandler(todo_end)],

        },
        fallbacks=[CommandHandler('todo_cancel', todo_cancel)]
    )
    dp.add_handler(todo_conv_handler)

    updater.start_polling()

    print("Starting bot")
    updater.idle()


if __name__ == '__main__':
    main()