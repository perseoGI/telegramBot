import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard
from .common import send_message

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

############################ TODOS ##################################

DESCRIPTION, CATEGORY, CREATE_CATEGORY, ANOTHER_ASSIGNMENT, ASSIGNMENT, TODO_DEADLINE, TODO_END = range(7)


def todo_start(update, context):
    logger.info("New todo from: %s, cat: %d, user: %d", update.message.from_user.name, update.message.chat_id, update.message.from_user.id)
    send_message(bot=context.bot,text="En que consiste la tarea?", chat_id=update.message.chat_id)

    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user

    logger.info("Description of %s: %s", user.name, update.message.text)
    chat_id = update.message.chat_id

    send_message(bot=context.bot,
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
        send_message( bot=context.bot,
                      chat_id=chat_id,
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
            send_message(bot=context.bot,
                        chat_id=chat_id,
                        message_id=update.callback_query.message.message_id,
                        text="Asigne la tarea",
                        reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))

            return ANOTHER_ASSIGNMENT
        # edit_message_text

        else:
            send_message(bot=context.bot,
                         chat_id=chat_id,
                         message_id=update.callback_query.message.message_id,
                         text="Asigne un deadline",
                         reply_markup=telegramcalendar.create_calendar())
            return TODO_DEADLINE


def todo_another_assignment(update, context):

    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    assigned_user_id = update.callback_query.data
    #logger.info("Assignment of %s: %s", user.first_name, assigned_user_id)

    send_message(bot=context.bot,
                 chat_id=chat_id,
                  message_id=update.callback_query.message.message_id,
                  text="Desea asignar tarea a otro miembro mas?",
                  reply_markup=binary_keyboard())

    # Store info in the database
    db.setPendingTodoAssingment(chat_id=chat_id, user_id=user_id, assigned_user_id=assigned_user_id)
    return ASSIGNMENT


def todo_assignment(update, context):

    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if answer == '1':     # Continue asking for assignments
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="Asigne la tarea",
                     reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))
        return ANOTHER_ASSIGNMENT

    else:               # Next step
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="Asigne un deadline",
                     reply_markup=telegramcalendar.create_calendar())
        return TODO_DEADLINE


def todo_deadline(update, context):
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    date = telegramcalendar.process_calendar_selection(context.bot, update)
    if not date:
        return TODO_DEADLINE

    if date != '0':    # Day selected
        db.setPendingTodoDeadline(chat_id=chat_id, user_id=user_id, deadline=date)
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="You selected %s\nDesea guardar la tarea?" % (date.strftime("%d/%m/%Y")),
                     reply_markup=binary_keyboard())
                                     #reply_markup=ReplyKeyboardRemove())
    else: # no deadline selected
        send_message(bot=context.bot,
                     chat_id=chat_id,
                      message_id=update.callback_query.message.message_id,
                      text="Desea guardar la tarea?",
                      reply_markup=binary_keyboard())

    return TODO_END


def todo_end(update, context):
    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    if answer == '1':
        db.storePendingTodo(
            chat_id=chat_id,
            user_id=user_id)

        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="Tarea guardada")
    else:
        db.clear_pending_todo(
            chat_id=chat_id,
            user_id=user_id)

        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="Tarea descartada")

    return ConversationHandler.END



def todo_cancel(update, context):
    #context.bot.get_chat()

    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tarea descartada!',
                              reply_markup=InlineKeyboardMarkup([]))

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
        send_message(bot=context.bot,
                    chat_id=chat_id,
                    text="Asigne la tarea",
                    reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=False))

        return ANOTHER_ASSIGNMENT
    # edit_message_text

    else:
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=update.callback_query.message.message_id,
                     text="Asigne un deadline",
                     reply_markup=telegramcalendar.create_calendar())
        return TODO_DEADLINE



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


