from binhex import openrsrc

import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard
from .common import send_message



########################### TODOLIST ###########################################

TODOLIST_CATEGORY, TODOLIST_ASSINGNED, TODOLIST_MENU, TODOLIST_EDIT_DESCRIPTION, TODOLIST_EDIT_DEADLINE, TODOLIST_FINISH = range(6)

# First '0' to null. callback cannot take '0' value because it has to be a string ('0' is a null)
_, ACTION_COMPLETE, ACTION_UNCOMPLETE, ACTION_POSTPONE, ACTION_EDIT, ACTION_BACK, ACTION_FINISH, ACTION_NEXT, ACTION_NONE = range(9)


def todolist_start(update, context):
    chat_id = update.message.chat_id

    send_message(
        bot=context.bot,
        chat_id=chat_id,
        text="Filtrar tareas por categoria",
        reply_markup=todo_category_keyboard(chat_id, todolist=True))

    return TODOLIST_CATEGORY

def todolist_category(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    category = update.callback_query.data

    db.set_todolist_filter_category(chat_id=chat_id, user_id=user_id, category=category)

    send_message(bot=context.bot,
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                text="Filtrar tareas por usuario asignado",
                reply_markup=todo_member_keyboard(chat_id, context.bot, todolist=True))

    return TODOLIST_ASSINGNED


def todolist_assigned(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    user_assigned = update.callback_query.data
    message_id = update.callback_query.message.message_id
    # Set last filter
    db.set_todolist_filter_assigned(chat_id=chat_id, user_id=user_id, user_assigned=user_assigned)

    # Create a temporal list of todos if exist
    exist = db.get_todo_list(chat_id=chat_id, user_id=user_id)
    if exist:
        todolist_send_item(context.bot, message_id, chat_id, user_id)
        return TODOLIST_MENU

    else:   # no todos available
        send_message(bot=context.bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    text="There is no pending todos :)\n*Now you are free!*")

        return ConversationHandler.END


def get_username_from_id(bot, chat_id, user_id):
    return bot.getChatMember(chat_id=int(chat_id), user_id=user_id)['user']['first_name']


####################### TODO: change design ######################


def todolist_item_keyboard(limit=None, completed=None):
    keyboard = [None] * 4
    keyboard[0] = [InlineKeyboardButton("Un-complete", callback_data=str(ACTION_UNCOMPLETE)) if completed else
                   InlineKeyboardButton("Complete", callback_data=str(ACTION_COMPLETE))]
  #  keyboard[0] = [] if completed else [InlineKeyboardButton("Complete", callback_data=str(ACTION_COMPLETE))]

    keyboard[1] = [InlineKeyboardButton("Postpone", callback_data=str(ACTION_POSTPONE))]

    keyboard[2] = [InlineKeyboardButton("Edit", callback_data=str(ACTION_EDIT))]

    keyboard[3] = [InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit in ('L', 'B') else
                   InlineKeyboardButton("←", callback_data=str(ACTION_BACK)),

                   InlineKeyboardButton("Finish", callback_data=str(ACTION_FINISH)),

                   InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit in ('R', 'B') else
                   InlineKeyboardButton("→", callback_data=str(ACTION_NEXT))]

    return InlineKeyboardMarkup(keyboard)



def todolist_send_item(bot, message_id, chat_id, user_id):
    todo, limit = db.get_todos_listed(chat_id, user_id)
    if todo:
        if chat_id < 0:  # group
            creator_name = get_username_from_id(bot, chat_id, todo['creator_id'])
            assignment_users_id = db.get_assigned_users(todo['id'])
            assignment_users_names = ""
            for i in range(len(assignment_users_id)):
                assignment_users_names += get_username_from_id(bot, chat_id, assignment_users_id[i].id)
                if i < len(assignment_users_id) - 2:
                    assignment_users_names += ", "
                elif i == len(assignment_users_id) - 2:
                    assignment_users_names += " and "

            text = "*{0}* {5}\n``` {1} ```\n\n  _Created by {2}\n  Assigned to {3}\n  Deadline: {4}_\n\n" \
                .format(db.get_category_name(todo['category_id']), todo['description'], creator_name,
                        assignment_users_names, todo['deadline'], "   COMPLETED!" if todo['completed'] else "")

        else:  # individual chat, no need creator and assigned name
            text = "*{0}* \n``` {1} ```\n\n".format(db.get_category_name(todo['category_id']),
                                                    todo['description'])
        send_message( bot=bot,
                      chat_id=chat_id,
                      message_id=message_id,
                      text=text,
                      reply_markup=todolist_item_keyboard(limit=limit, completed=todo['completed']))


def todolist_edit(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    data = update.callback_query.data.split(',')
    message_id = update.callback_query.message.message_id

    operation = int(data[0])
    index = int(data[1]) if len(data) > 1 else None
    if operation == ACTION_COMPLETE or operation == ACTION_UNCOMPLETE:
        action = True if operation == ACTION_COMPLETE else False
        db.change_todos_listed(chat_id=chat_id, user_id=user_id, key='completed', value=action)
        todolist_send_item(context.bot, message_id, chat_id, user_id)

        return TODOLIST_MENU

    # TODO
    elif operation == ACTION_EDIT:
        todo, _ = db.get_todos_listed(chat_id, user_id)

        send_message( bot=context.bot,
                      chat_id=chat_id,
                      message_id=message_id,
                      text="Type to edit TODO:\n ```{0}```".
                      format(todo['description']))

        return TODOLIST_EDIT_DESCRIPTION
    elif operation == ACTION_POSTPONE:
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=message_id,
                     text="Assign a new deadline",
                     reply_markup=telegramcalendar.create_calendar())

        return TODOLIST_EDIT_DEADLINE
    # Store changes!
    elif operation == ACTION_FINISH:

        pending_changes = db.get_pending_changes_todo(chat_id, user_id)
        if pending_changes:
            pending_changes = "Do you want to store pending changes?\n\n" + pending_changes
            send_message(bot=context.bot,
                         chat_id=chat_id,
                         message_id=message_id,
                         text=pending_changes,
                         reply_markup=binary_keyboard())
            return TODOLIST_FINISH
        else:
            send_message(bot=context.bot,
                         chat_id=chat_id,
                         message_id=message_id,
                         text="No changes!")
            return ConversationHandler.END

    elif operation == ACTION_NEXT or operation == ACTION_BACK:
        db.set_todos_listed_index(chat_id, user_id, 1 if operation == ACTION_NEXT else -1)
        todolist_send_item(context.bot, message_id, chat_id, user_id)
        return TODOLIST_MENU

    elif operation == ACTION_NONE:
        return TODOLIST_MENU

    return TODOLIST_MENU


def todolist_edit_description(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    edited_description = update.message.text
    db.change_todos_listed(chat_id=chat_id, user_id=user_id, key='description', value=edited_description)
    # Send message as new message
    todolist_send_item(context.bot, message_id=None, chat_id=chat_id, user_id=user_id)
    return TODOLIST_MENU

def todolist_edit_deadline(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    date = telegramcalendar.process_calendar_selection(context.bot, update).strftime("%Y-%m-%d")

    db.change_todos_listed(chat_id=chat_id, user_id=user_id, key='deadline', value=date)
    todolist_send_item(context.bot, update.callback_query.message.message_id, chat_id, user_id)
    return TODOLIST_MENU


def todolist_finish(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    operation = update.callback_query.data
    if operation == '1':
        db.store_changes_todo(chat_id=chat_id, user_id=user_id)
        send_message( bot=context.bot,
                      chat_id=chat_id,
                      message_id=message_id,
                      text="Changes saved!")
    else:
        db.clear_todo_list(chat_id, user_id)
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=message_id,
                     text="Restore version!")

    return ConversationHandler.END



# TODO
def todolist_cancel(update, context):
    pass


# TODOLIST
todolist_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('todolist', todolist_start)],
    states={
        TODOLIST_CATEGORY: [CallbackQueryHandler(todolist_category)],
        TODOLIST_ASSINGNED: [CallbackQueryHandler(todolist_assigned)],
        TODOLIST_MENU: [CallbackQueryHandler(todolist_edit)],
        TODOLIST_EDIT_DESCRIPTION: [MessageHandler(Filters.text, todolist_edit_description)],
        TODOLIST_EDIT_DEADLINE: [CallbackQueryHandler(todolist_edit_deadline)],
        TODOLIST_FINISH: [CallbackQueryHandler(todolist_finish)]
    },
    fallbacks=[CommandHandler('todolist_cancel', todolist_cancel)]
)