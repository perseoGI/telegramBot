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
from .keyboards import todo_member_keyboard_content, todo_category_keyboard_content, binary_keyboard_content

# from .common import send_message
from i18n import _
from utils.botinteractions import BotManager

logging.basicConfig(
    filename="bot.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

botManager = BotManager()

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
        ("New task from: %s, cat: %d, user: %d"),
        update.message.from_user.name,
        update.message.chat_id,
        update.message.from_user.id,
    )
    botManager.send_message(
        update=update, text=_("What is the task about?"), chat_id=update.message.chat_id
    )

    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user

    #  logger.info("Description of %s: %s", user.name, update.message.text)
    chat_id = update.message.chat_id

    botManager.send_message(
        update=update,
        chat_id=chat_id,
        text=_("In which category will you include it?"),
        reply_markup=todo_category_keyboard_content(chat_id, todolist=False),
    )

    print('after send')
    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user.id)

    print('after check')
    # Update model
    db.setPendingTodosDescription(
        chat_id=chat_id,
        user_id=update.message.from_user.id,
        description=update.message.text,
    )
    print('after set')

    return CATEGORY


def todo_category(update, context):
    user_id = update.effective_user.id
    message_id = update.callback_query.message.message_id
    user = update.effective_user
    logger.info("Category of %s: %s", user.name, update.callback_query.data)
    chat_id = update.callback_query.message.chat_id
    category = update.callback_query.data
    if category < "0":  # Create a new category
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=message_id,
            text=_("Type the name for the new category"),
        )
        return CREATE_CATEGORY

    else:
        # Update model
        db.setPendingTodosCategory(chat_id=chat_id, user_id=user_id, category=category)

        if chat_id < 0:  # It is a group
            return check_and_ask_assignation(
                context.bot,
                update,
                chat_id,
                user_id,
                message_id,
                ask_for_continuing=False,
            )

        else:
            botManager.send_message(
                update=update,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Assing a deadline to the task"),
                reply_markup=telegramcalendar.create_calendar_content(),
            )
            return TODO_DEADLINE


def check_and_ask_assignation(
    bot, update, chat_id, user_id, message_id, ask_for_continuing
):
    # Check users in group
    users_not_assigned = db.getPendingTodoNotAssigned(chat_id, user_id)
    if users_not_assigned:
        if not ask_for_continuing:
            botManager.send_message(
                update=update,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Assign the task"),
                reply_markup=todo_member_keyboard_content(users_not_assigned, chat_id, bot),
            )
            return ANOTHER_ASSIGNMENT
        else:
            botManager.send_message(
                update=update,
                chat_id=chat_id,
                message_id=message_id,
                text=_("Do you want to assign the task to another member?"),
                reply_markup=binary_keyboard_content(),
            )
            return ASSIGNMENT

    else:
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=message_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar_content(),
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
        context.bot, update, chat_id, user_id, message_id, ask_for_continuing=True
    )


def todo_assignment(update, context):

    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id
    message_id = update.callback_query.message.message_id

    if answer == "1":  # Continue asking for assignments
        return check_and_ask_assignation(
            context.bot, update, chat_id, user_id, message_id, ask_for_continuing=False
        )

    else:  # Next step
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar_content(),
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
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("You have selected %s\nDo you want to save the task?")
            % (date.strftime("%d/%m/%Y")),
            reply_markup=binary_keyboard_content(),
        )

    else:  # no deadline selected
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Do you want to save the task?"),
            reply_markup=binary_keyboard_content(),
        )

    return TODO_END


def todo_end(update, context):
    answer = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id

    if answer == "1":
        db.storePendingTodo(chat_id=chat_id, user_id=user_id)

        botManager.send_message(
            update=update,
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id,
            text=_("Task saved!"),
        )
    else:
        db.clear_pending_todo(chat_id=chat_id, user_id=user_id)

        botManager.send_message(
            update=update,
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
            context.bot,
            update,
            chat_id,
            user_id,
            message_id=None,
            ask_for_continuing=False,
        )

    # edit_message_text

    else:
        botManager.send_message(
            update=update,
            chat_id=chat_id,
            text=_("Assign a deadline"),
            reply_markup=telegramcalendar.create_calendar_content(),
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
