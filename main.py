from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

import requests
import re
import logging
import database as db
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from calendarBot import telegramcalendar

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

########################### Miscelanea ###########################################

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


def general_check(update, context):
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user_id)
    print("Incoming msg: ", update.message.text)


def test(update, context):
    chat_id = update.message.chat_id
    for i in range(10):
        context.bot.send_message(chat_id=chat_id, text="pruebaaa de spam "+ str(i))





############################ TODOS ##################################

DESCRIPTION, CATEGORY, CREATE_CATEGORY, ANOTHER_ASSIGNMENT, ASSIGNMENT, TODO_DEADLINE, TODO_END = range(7)


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
        reply_markup=todo_category_keyboard(chat_id, todolist=False))

    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user.id)

    # Update model
    db.setPendingTodosDescription(
        chat_id=chat_id,
        user_id=update.message.from_user.id,
        description=update.message.text)

    return CATEGORY


def todo_category(update, context):
    user_id = update.effective_user.id
   # logger.info("Category of %s: %s", user.first_name, update.message.text)
    chat_id =update.callback_query.message.chat_id
    category = update.callback_query.data
    if category < '0':    # Create a new category
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Escriba el nombre de la nueva categoria",
                                      )
        return CREATE_CATEGORY

    else:
        # Update model
        db.setPendingTodosCategory(
            chat_id=chat_id,
            user_id=user_id,
            category=category)

        if chat_id < 0:       # It is a group
            context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    text="Asigne la tarea",
                                    reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))

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

    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    assigned_user_id = update.callback_query.data
    #logger.info("Assignment of %s: %s", user.first_name, assigned_user_id)

    context.bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Desea asignar tarea a otro miembro mas?",
                                  reply_markup=binary_keyboard())

    # Store info in the database
    db.setPendingTodoAssingment(chat_id=chat_id, user_id=user_id, assigned_user_id=assigned_user_id)
    return ASSIGNMENT


def todo_assignment(update, context):

    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    print(answer)
    if answer == '1':     # Continue asking for assignments
        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Asigne la tarea",
                                        reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))
        return ANOTHER_ASSIGNMENT

    else:               # Next step
        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Asigne un deadline",
                                        reply_markup=telegramcalendar.create_calendar())
        return TODO_DEADLINE

# update la tabla TODO para aceptar el deadline!
def todo_deadline(update, context):
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id
    selected, date = telegramcalendar.process_calendar_selection(context.bot, update)
    print("Selected ", selected, " date: ", date )
    if selected:

        if date:    # Day selected
            db.setPendingTodoDeadline(chat_id=chat_id, user_id=user_id, deadline=date)
            context.bot.edit_message_text(chat_id=chat_id,
                                          message_id=update.callback_query.message.message_id,

                                          text="You selected %s\nDesea guardar la tarea?" % (date.strftime("%d/%m/%Y")),
                                          reply_markup=binary_keyboard())
                                         #reply_markup=ReplyKeyboardRemove())
        else: # no deadline selected
            context.bot.edit_message_text(chat_id=chat_id,
                                          message_id=update.callback_query.message.message_id,
                                          text="Desea guardar la tarea?",
                                          reply_markup=binary_keyboard())

    return TODO_END


def todo_end(update, context):
    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    print(chat_id, user_id)
    if answer == '1':
        db.storePendingTodo(
            chat_id=chat_id,
            user_id=user_id)

        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Tarea guardada"
                                        )
    else:
        db.clear_pending_todo(
            chat_id=chat_id,
            user_id=user_id)

        context.bot.edit_message_text(  chat_id=chat_id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Tarea descartada"
                                        )

    return ConversationHandler.END



def todo_cancel(update, context):
    #context.bot.get_chat()

    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tarea descartada!',
                              reply_markup=InlineKeyboardMarkup([])
                              )

    return ConversationHandler.END





########################### Category ###########################################

def create_category(update, context):
    chat_id = update.message.chat_id
    category_name = update.message.text
    category_id = db.createCategory(chat_id=chat_id, name=category_name)

    user_id = update.effective_user.id

    # TODO: refactorizar
    # Update model
    db.setPendingTodosCategory(
        chat_id=chat_id,
        user_id=user_id,
        category=category_id)

    if chat_id < 0:  # It is a group
        context.bot.send_message(
            chat_id=chat_id,
            text="Asigne la tarea",
            reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))

        return ANOTHER_ASSIGNMENT
    # edit_message_text

    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="Desea guardar la tarea?",
            reply_markup=binary_keyboard())
        return TODO_END

########################### TODOLIST ###########################################

TODOLIST_CATEGORY, TODOLIST_ASSINGNED, TODOLIST_EDIT = range(3)

TODOLIST_COMPLETE = 1
TODOLIST_POSTPONE = 2
TODOLIST_FINISH = 3
TODOLIST_CANCEL = 4

def todolist_start(update, context):
    chat_id = update.message.chat_id

    context.bot.send_message(
        chat_id=chat_id,
        text="Filtrar tareas por categoria",
        reply_markup=todo_category_keyboard(chat_id, todolist=True))

    return TODOLIST_CATEGORY

def todolist_category(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    category = update.callback_query.data

    db.set_todolist_filter_category(chat_id=chat_id, user_id=user_id, category=category)

    context.bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Filtrar tareas por usuario asignado",
                                  reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=True))

    return TODOLIST_ASSINGNED

def get_username_from_id(bot, chat_id, user_id):
    return bot.getChatMember(chat_id=int(chat_id), user_id=user_id)['user']['first_name']



def todolist_comlete_postpone_keyboard(todo_id):
    keyboard = []
    row = []
    row.append(InlineKeyboardButton("Complete", callback_data=str(TODOLIST_COMPLETE) + "," + str(todo_id)))
    row.append(InlineKeyboardButton("Postpone", callback_data=str(TODOLIST_POSTPONE) + "," + str(todo_id)))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def todolist_assigned(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    user_assigned = update.callback_query.data

    db.set_todolist_filter_assigned(chat_id=chat_id, user_id=user_id, user_assigned=user_assigned)

    # Obtain list of todos
    todos = db.get_todo_list(chat_id=chat_id, user_id=user_id)
    text = ""
    if todos:
        iter = 0
        for todo in todos:
            if chat_id < 0:  # group
                # TODO: en general_check, pasarle el nombre del usuario que hable para no tener que revisarlo aqui
                creator_name = get_username_from_id(context.bot, chat_id, todo['creator_id'])
                assignment_users_id = db.get_assigned_users(todo['id'])
                assignment_users_names = ""
                for i in range(len(assignment_users_id)):
                    assignment_users_names += get_username_from_id(context.bot, chat_id, assignment_users_id[i].id)
                    if i < len(assignment_users_id) - 2:
                        assignment_users_names += ", "
                    elif i == len(assignment_users_id) - 2:
                        assignment_users_names += " and "

                text = "*{0}* \n``` {1} ```\n  _Created by {2}\n  Assigned to _{3}\n\n"\
                    .format(db.get_category_name(todo['category_id']), todo['description'], creator_name, assignment_users_names)

            else: # individual chat, no need creator and assigned name
                text += "*{0}* \n``` {1} ```\n\n".format(db.get_category_name(todo['category_id']),
                                                         todo['description'])
            if iter == 0:
                message_id = context.bot.edit_message_text(chat_id=chat_id,
                                                            message_id=update.callback_query.message.message_id,
                                                            text=text,
                                                            parse_mode=ParseMode.MARKDOWN,
                                                            reply_markup=todolist_comlete_postpone_keyboard(todo_id=todo['id'])).message_id
                print("id", message_id)
            else:
                message_id = context.bot.send_message(chat_id=chat_id,
                                         text=text,
                                         parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=todolist_comlete_postpone_keyboard(todo_id=todo['id'])).message_id
            iter += 1

            db.add_messages_to_clear(chat_id, user_id, message_id) # Add message_id to clear them later


        # End
        context.bot.send_message(chat_id=chat_id,
                                 text="Press FINISH to complete\nCANCEL to undo any operations",
                                 parse_mode=ParseMode.MARKDOWN,
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("FINISH", callback_data=TODOLIST_FINISH),
                                                                     InlineKeyboardButton("CANCEL", callback_data=TODOLIST_CANCEL)]]))

        return TODOLIST_EDIT

    else: # no todos available
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="There is no pending todos :)\n*Now you are free!*",
                                      parse_mode=ParseMode.MARKDOWN)

        return ConversationHandler.END


def todolist_edit(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    data = update.callback_query.data.split(',')

    operation = int(data[0])
    print(operation)

    if operation == TODOLIST_COMPLETE:
        todo_id = int(data[1])
        print(todo_id)
        db.set_pending_complete_todo(chat_id=chat_id, user_id=user_id, todo_id=todo_id)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Todo completed!",
                                      parse_mode=ParseMode.MARKDOWN)
        return TODOLIST_EDIT

    # TODO
    elif operation == TODOLIST_POSTPONE:
        pass

    # Store changes!
    elif operation == TODOLIST_FINISH:
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Done!")
        db.set_complete_todo(chat_id=chat_id, user_id=user_id)
        delete_messages(context.bot, chat_id, user_id)
        return ConversationHandler.END

    elif operation == TODOLIST_CANCEL:
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="You have cancelled your operations!")
        db.clear_pending_complete_todo(chat_id=chat_id, user_id=user_id)
        delete_messages(context.bot, chat_id, user_id)



        return ConversationHandler.END

    return TODOLIST_EDIT #ConversationHandler.END

def delete_messages(bot, chat_id, user_id):
    for id in db.pop_messages_to_clear(chat_id, user_id):
        bot.delete_message(chat_id=chat_id,
                           message_id=id,
                           )  # TODO : check timeout option!

############################ Keyboards #########################################

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





def main():
    # Create database
    db.init_db()

    print("Setting up bot")
    updater = Updater('867661842:AAGr-zhF5UNvbvGl1hvT_l6Pacj2OYwDEY8',  use_context=True)
    dp = updater.dispatcher


    dp.add_handler(CommandHandler('bop',bop))

    dp.add_handler( CommandHandler('start', start))

    # dp.add_handler(MessageHandler(Filters.text, echo))

    dp.add_handler(MessageHandler(Filters.text, general_check), group=2)

    dp.add_handler(CommandHandler('caps', caps))
    dp.add_handler(CommandHandler('test', test))

    # TODOS
    todo_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('todo', todo_start)],
        states={
            DESCRIPTION: [MessageHandler(Filters.text, todo_description)],
            CATEGORY: [CallbackQueryHandler(todo_category)],
            CREATE_CATEGORY: [MessageHandler(Filters.text, create_category)],
            ANOTHER_ASSIGNMENT: [CallbackQueryHandler(todo_another_assignment)],
            ASSIGNMENT: [CallbackQueryHandler(todo_assignment)],
            TODO_DEADLINE: [CallbackQueryHandler(todo_deadline)],
            TODO_END: [CallbackQueryHandler(todo_end)],
        },
        fallbacks=[CommandHandler('todo_cancel', todo_cancel)]
    )
    dp.add_handler(todo_conv_handler)

    # TODOLIST
    todolist_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('todolist', todolist_start)],
        states={
            TODOLIST_CATEGORY: [CallbackQueryHandler(todolist_category)],
            TODOLIST_ASSINGNED: [CallbackQueryHandler(todolist_assigned)],
            TODOLIST_EDIT: [CallbackQueryHandler(todolist_edit)],
        },
        fallbacks=[CommandHandler('todo_cancel', todo_cancel)]
    )
    dp.add_handler(todolist_conv_handler)

    updater.start_polling()

    print("Starting bot")
    updater.idle()


if __name__ == '__main__':
    main()