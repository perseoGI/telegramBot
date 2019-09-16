from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import requests
import re
import logging
import database

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

DESCRIPTION, CATEGORY = range(2)
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

############################ Keyboards #########################################

def todo_menu_keyboard():
    group_members = ["Cesar", "Daniel", "Perseo"]

    # button_list = [[KeyboardButton(s)] for s in group_members]
    # ReplyKeyboardMarkup(button_list)

    # keyboard = [[KeyboardButton('Cesar', callback_data='1')],
    #            [KeyboardButton('Daniel', callback_data='2')],
    #            [KeyboardButton('Perseo', callback_data='3')]
    #             ]
    # return ReplyKeyboardMarkup(keyboard)

    keyboard = [[InlineKeyboardButton('Cesar', callback_data='1')],
               [InlineKeyboardButton('Daniel', callback_data='2')],
               [InlineKeyboardButton('Perseo', callback_data='3')]
                ]
    return InlineKeyboardMarkup(keyboard)

def todo_start(update, context):
    update.message.reply_text(text="En que consiste la tarea?")
    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user
    logger.info("Description of %s: %s", user.first_name, update.message.text)
    update.message.reply_text(text="En que categoria lo incluirias?")

    return CATEGORY

def todo_category(update, context):
    user = update.message.from_user
    logger.info("Description of %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Thank you! I hope we can talk again some day.')

    return ConversationHandler.END


def todo_(update, context):
    # context.bot.edit_message_text(chat_id=update.message.chat_id,
    #                         text="En que consiste la tarea?",
    #                         reply_markup=todo_menu_keyboard()
    #                         )

    context.bot.send_message(chat_id=update.message.chat_id,
                            text="En que consiste la tarea?",
                            reply_markup=todo_menu_keyboard()
                            )

def todo_actions(update, context):
    query = update.callback_query
    query.edit_message_text(text="Selected option: {}".format(query.data))






def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',)
                            #  reply_markup=InlReplyKeyboardRemove())

    return ConversationHandler.END



def main():
    print("Setting up bot")
    updater = Updater('867661842:AAGr-zhF5UNvbvGl1hvT_l6Pacj2OYwDEY8',  use_context=True)
    dp = updater.dispatcher

    bop_handler = CommandHandler('bop',bop)
    dp.add_handler(bop_handler)

    start_handler = CommandHandler('start', start)
    dp.add_handler(start_handler)

    # dp.add_handler(MessageHandler(Filters.text, echo))

    caps_handler = CommandHandler('caps', caps)
    dp.add_handler(caps_handler)


    # dp.add_handler(CallbackQueryHandler(todo_actions))

    todo_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('todo', todo_start)],

        states={
            DESCRIPTION: [MessageHandler(Filters.text, todo_description)],
            CATEGORY: [MessageHandler(Filters.text, todo_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(todo_conv_handler)





    updater.start_polling()
    print("Starting bot")
    updater.idle()


if __name__ == '__main__':
    main()