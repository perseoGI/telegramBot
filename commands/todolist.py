from binhex import openrsrc

import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard, todolist_item_keyboard
from .common import send_message
from . import callbacks as Callback



########################### TODOLIST ###########################################

TODOLIST_CATEGORY, TODOLIST_ASSINGNED, TODOLIST_MENU, TODOLIST_EDIT_DESCRIPTION, TODOLIST_EDIT_DEADLINE, TODOLIST_FINISH = range(6)



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
    message_id = update.callback_query.message.message_id

    db.set_todolist_filter_category(chat_id=chat_id, user_id=user_id, category=category)

    if chat_id < 0:  # It's a group
        db.connectDB()
        group_member_ids = [user['user_id'] for user in db.getUsersIdFromChat(chat_id)]
        db.closeDB()
        send_message(bot=context.bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    text="Filtrar tareas por usuario asignado",
                    reply_markup=todo_member_keyboard(group_member_ids, chat_id, context.bot, todolist=True))
        return TODOLIST_ASSINGNED

    else:
        if create_temporal_todo_list(context.bot, chat_id, user_id, message_id):
            return TODOLIST_MENU
        else:
            return ConversationHandler.END

def todolist_assigned(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    user_assigned = update.callback_query.data
    message_id = update.callback_query.message.message_id
    # Set last filter
    db.set_todolist_filter_assigned(chat_id=chat_id, user_id=user_id, user_assigned=user_assigned)
    if create_temporal_todo_list(context.bot, chat_id, user_id, message_id):
        return TODOLIST_MENU
    else:
        return ConversationHandler.END


def create_temporal_todo_list(bot, chat_id, user_id, message_id):
    # Create a temporal list of todos if exist
    exist = db.get_todo_list(chat_id=chat_id, user_id=user_id)
    if exist:
        todolist_send_item(bot, message_id, chat_id, user_id)
        return True

    else:   # no todos available
        send_message(bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    text="There is no pending todos :)\n*Now you are free!*")

        return False


def get_username_from_id(bot, chat_id, user_id):
    return bot.getChatMember(chat_id=int(chat_id), user_id=user_id)['user']['first_name']


####################### TODO: change design ######################






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
            text = "*{0}* \n``` {1} ```\n_Deadline: {2}_\n\n".format(db.get_category_name(todo['category_id']),
                                                    todo['description'], todo['deadline'])
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
    if operation == Callback.ACTION_COMPLETE or operation == Callback.ACTION_UNCOMPLETE:
        action = True if operation == Callback.ACTION_COMPLETE else False
        db.change_todos_listed(chat_id=chat_id, user_id=user_id, key='completed', value=action)
        todolist_send_item(context.bot, message_id, chat_id, user_id)

        return TODOLIST_MENU

    elif operation == Callback.ACTION_EDIT:
        todo, _ = db.get_todos_listed(chat_id, user_id)

        send_message( bot=context.bot,
                      chat_id=chat_id,
                      message_id=message_id,
                      text="Type to edit TODO:\n ```{0}```".
                      format(todo['description']))

        return TODOLIST_EDIT_DESCRIPTION
    elif operation == Callback.ACTION_POSTPONE:
        send_message(bot=context.bot,
                     chat_id=chat_id,
                     message_id=message_id,
                     text="Assign a new deadline",
                     reply_markup=telegramcalendar.create_calendar())

        return TODOLIST_EDIT_DEADLINE
    # Store changes!
    elif operation == Callback.ACTION_FINISH:

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

    elif operation == Callback.ACTION_NEXT or operation == Callback.ACTION_BACK:
        db.set_todos_listed_index(chat_id, user_id, 1 if operation == Callback.ACTION_NEXT else -1)
        todolist_send_item(context.bot, message_id, chat_id, user_id)
        return TODOLIST_MENU

    elif operation == Callback.ACTION_NONE:
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

    date = telegramcalendar.process_calendar_selection(context.bot, update)
    if date == False:
        return TODOLIST_EDIT_DEADLINE

    if date != '0':
        date = date.strftime("%Y-%m-%d")
    else:
        date = None
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