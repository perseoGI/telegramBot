from database import (
    mark_todo_as_completed,
    set_todo_deadline,
    get_pending_background_todo_id_and_description,
    set_pending_background_todo_id,
)
from utils.botinteractions import BotManager
from calendarBot import telegramcalendar
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from i18n import _

botManager = BotManager()

# ConversationHandler callback identifier
BACKGROUND_TODO_POSTPONE = 1


def background_response_callback(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    data = update.callback_query.data
    (_, action, todo_id) = data.split("-")

    if action == "postpone":
        # store todo_id on a temporal structure in order to recover it on next callback (add message_id to increase trazability)
        set_pending_background_todo_id(chat_id, user_id, message_id, todo_id)

        botManager.send_message(
            chat_id=chat_id,
            message_id=message_id,
            text=_("Asigne un nuevo deadline"),
            reply_markup=telegramcalendar.create_calendar(),
        )
        return BACKGROUND_TODO_POSTPONE

    elif action == "complete":
        todo_description_completed = mark_todo_as_completed(todo_id)
        botManager.send_message(
            chat_id,
            text=_("La tarea:\n\n``` {0} ```\n\nha sido completada con éxito").format(
                todo_description_completed
            ),
            message_id=message_id,
        )
        return ConversationHandler.END


def background_todo_postpone(update, context):
    chat_id = update.callback_query.message.chat_id
    user_id = update.effective_user.id
    message_id = update.callback_query.message.message_id
    date = telegramcalendar.process_calendar_selection(context.bot, update)

    if not date:
        return BACKGROUND_TODO_POSTPONE

    (todo_id, todo_description) = get_pending_background_todo_id_and_description(
        chat_id, user_id, message_id
    )

    if date != "0":  # Day selected
        botManager.send_message(
            chat_id=chat_id,
            message_id=message_id,
            text=_(
                "La tarea:\n\n``` {0} ```\n\nha sido pospuesta para el día {1}"
            ).format(todo_description, date.strftime("%d/%m/%Y")),
        )

        deadline = date.strftime("%Y-%m-%d")

    else:  # no deadline selected
        botManager.send_message(
            chat_id=chat_id,
            message_id=message_id,
            text=_("La tarea:\n\n``` {0} ```\n\nha sido guardada sin deadline"),
        ).format(todo_description)

        deadline = None

    set_todo_deadline(todo_id, newDeadline=deadline)
    return ConversationHandler.END


def background_todo_cancel(update, context):
    user = update.message.from_user
    # logger.info("Background Todo: User %s canceled the conversation.", user.first_name)
    update.message.reply_text(_("Ha ocurrido un error"), reply_markup=None)

    return ConversationHandler.END


# todo_deadline_achieved = CallbackQueryHandler(background_response_callback, pattern='^todo_deadline_achieved-(\w+)-(\d+)$')

background_response_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            background_response_callback, pattern="^todo_deadline_achieved-(\w+)-(\d+)$"
        )
    ],
    states={
        BACKGROUND_TODO_POSTPONE: [CallbackQueryHandler(background_todo_postpone)],
    },
    fallbacks=[CommandHandler("background_cancel", background_todo_cancel)],
)
