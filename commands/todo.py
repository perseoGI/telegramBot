import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard
from .common import send_message
from i18n import _

logging.basicConfig(
    filename="bot.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

############################ TODOS ##################################

(
    DESCRIPTION,
    CATEGORY,
    CREATE_CATEGORY,
    ANOTHER_ASSIGNMENT,
    ASSIGNMENT,
    TODO_DEADLINE,
    TODO_END,
) = range(7)


def todo_start(update, context):
    logger.info(
        _("New todo from: %s, cat: %d, user: %d"),
        update.message.from_user.name,
        update.message.chat_id,
        update.message.from_user.id,
    )
    send_message(
        bot=context.bot, text=_("What is the task?"), chat_id=update.message.chat_id
    )

    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user

    #  logger.info("Description of %s: %s", user.name, update.message.text)
    chat_id = update.message.chat_id

    send_message(
        bot=context.bot,
        chat_id=chat_id,
        text=_("In which category will you include it?"),
        reply_markup=todo_category_keyboard(chat_id, todolist=False),
    )

    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user.id)

    # Update model
    db.setPendingTodosDescription(
        chat_id=chat_id,
        user_id=update.message.from_user.id,
        description=update.message.text,
    )

    return CATEGORY


def todo_category(update, context):
    user_id = update.effective_user.id
    message_id = update.callback_query.message.message_id
    user = update.effective_user
    logger.info("Category of %s: %s", user.name, update.callback_query.data)
    chat_id = update.callback_query.message.chat_id
    category = update.callback_query.data
    if category < "0":  # Create a new category
        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Type the neme for the new category"),
        )
        return CREATE_CATEGORY

    else:
        # Update model
        db.setPendingTodosCategory(chat_id=chat_id, user_id=user_id, category=category)

        if chat_id < 0:  # It is a group
            return check_and_ask_assignation(
                context.bot, chat_id, user_id, message_id, ask_for_continuing=False
            )

        else:
            send_message(
                bot=context.bot,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Assing a dadline to the task"),
                reply_markup=telegramcalendar.create_calendar(),
            )
            return TODO_DEADLINE


def check_and_ask_assignation(bot, chat_id, user_id, message_id, ask_for_continuing):
    # Check users in group
    users_not_assigned = db.getPendingTodoNotAssigned(chat_id, user_id)
    if users_not_assigned:
        if not ask_for_continuing:
            send_message(
                bot=bot,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Assign the task"),
                reply_markup=todo_member_keyboard(users_not_assigned, chat_id, bot),
            )
            return ANOTHER_ASSIGNMENT
        else:
            send_message(
                bot=bot,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Do you want to assign a task to another member?"),
                reply_markup=binary_keyboard(),
            )
            return ASSIGNMENT

    else:
        send_message(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar(),
        )
        return TODO_DEADLINE


def todo_another_assignment(update, context):

    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    assigned_user_id = update.callback_query.data
    user = update.effective_user
    logger.info(_("Assignment of %s: %s"), user.name, assigned_user_id)
    # Store info in the database
    db.setPendingTodoAssingment(
        chat_id=chat_id, user_id=user_id, assigned_user_id=assigned_user_id
    )

    return check_and_ask_assignation(
        context.bot, chat_id, user_id, message_id, ask_for_continuing=True
    )

    # send_message(bot=context.bot,
    #              chat_id=chat_id,
    #               message_id=update.callback_query.message.message_id,
    #               text="Desea asignar tarea a otro miembro mas?",
    #               reply_markup=binary_keyboard())


def todo_assignment(update, context):

    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id
    message_id = update.callback_query.message.message_id

    if answer == "1":  # Continue asking for assignments
        return check_and_ask_assignation(
            context.bot, chat_id, user_id, message_id, ask_for_continuing=False
        )

        # send_message(bot=context.bot,
        #              chat_id=chat_id,
        #              message_id=update.callback_query.message.message_id,
        #              text="Asigne la tarea",
        #              reply_markup=todo_member_keyboard(chat_id, user_id, context.bot, todolist=False))
        # return ANOTHER_ASSIGNMENT

    else:  # Next step
        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar(),
        )
        return TODO_DEADLINE


def todo_deadline(update, context):
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    date = telegramcalendar.process_calendar_selection(context.bot, update)
    if not date:
        return TODO_DEADLINE

    if date != "0":  # Day selected
        db.setPendingTodoDeadline(chat_id=chat_id, user_id=user_id, deadline=date)
        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_(
                "You selected %s\nDo you want to save the task?"
                % (date.strftime("%d/%m/%Y"))
            ),
            reply_markup=binary_keyboard(),
        )
        # reply_markup=ReplyKeyboardRemove())
    else:  # no deadline selected
        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Do you want to save the task?"),
            reply_markup=binary_keyboard(),
        )

    return TODO_END


def todo_end(update, context):
    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    if answer == "1":
        db.storePendingTodo(chat_id=chat_id, user_id=user_id)

        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Task saved"),
        )
    else:
        db.clear_pending_todo(chat_id=chat_id, user_id=user_id)

        send_message(
            bot=context.bot,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Task has been discarted"),
        )

    return ConversationHandler.END


def todo_cancel(update, context):
    # context.bot.get_chat()

    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Task has been discarted!", reply_markup=InlineKeyboardMarkup([])
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
    db.setPendingTodosCategory(chat_id=chat_id, user_id=user_id, category=category_id)

    if chat_id < 0:  # It is a group

        return check_and_ask_assignation(
            context.bot, chat_id, user_id, message_id=None, ask_for_continuing=False
        )

    # edit_message_text

    else:
        send_message(
            bot=context.bot,
            chat_id=chat_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar(),
        )
        return TODO_DEADLINE


# TODOS
todo_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("todo", todo_start)],
    states={
        DESCRIPTION: [MessageHandler(Filters.text, todo_description)],
        CATEGORY: [CallbackQueryHandler(todo_category)],
        CREATE_CATEGORY: [MessageHandler(Filters.text, create_category)],
        ANOTHER_ASSIGNMENT: [CallbackQueryHandler(todo_another_assignment)],
        ASSIGNMENT: [CallbackQueryHandler(todo_assignment)],
        TODO_DEADLINE: [CallbackQueryHandler(todo_deadline)],
        TODO_END: [CallbackQueryHandler(todo_end)],
    },
    fallbacks=[CommandHandler("todo_cancel", todo_cancel)],
)
