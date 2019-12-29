from binhex import openrsrc

import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard




########################### TODOLIST ###########################################

TODOLIST_CATEGORY, TODOLIST_ASSINGNED, TODOLIST_EDIT, TODOLIST_EDIT_TODO, TODOLIST_FINISH = range(5)

# First '0' to null. callback cannot take '0' value because it has to be a string ('0' is a null)
_, ACTION_COMPLETE, ACTION_UNCOMPLETE, ACTION_POSTPONE, ACTION_EDIT, ACTION_BACK, ACTION_FINISH, ACTION_NEXT, ACTION_NONE = range(9)


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



####################### TODO: change design ######################

def todolist_item_keyboard(todo_id, index=0, limit=None, completed=None):
    keyboard = [None] * 4
   # keyboard[0] = [InlineKeyboardButton("Un-complete", callback_data=str(ACTION_UNCOMPLETE) + "," + str(index)) if completed else
   #                InlineKeyboardButton("Complete", callback_data=str(ACTION_COMPLETE) + "," + str(index))]
    keyboard[0] = [] if completed else [InlineKeyboardButton("Complete", callback_data=str(ACTION_COMPLETE) + "," + str(index))]

    keyboard[1] = [InlineKeyboardButton("Postpone", callback_data=str(ACTION_POSTPONE) + "," + str(index))]

    keyboard[2] = [InlineKeyboardButton("Edit", callback_data=str(ACTION_EDIT) + "," + str(index))]

    keyboard[3] = [InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit in ('L', 'B') else
                   InlineKeyboardButton("←", callback_data=str(ACTION_BACK) + "," + str(index - 1)),

                   InlineKeyboardButton("Finish", callback_data=str(ACTION_FINISH)),

                   InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit in ('R', 'B') else
                   InlineKeyboardButton("→", callback_data=str(ACTION_NEXT) + "," + str(index + 1))]

    return InlineKeyboardMarkup(keyboard)



def todolist_send_item(bot, update, chat_id, user_id, index):
    todo, limit = db.get_todos_listed(chat_id, user_id, index)
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=text,
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=todolist_item_keyboard(todo_id=todo['id'], index=index, limit=limit, completed=todo['completed']))

def todolist_assigned(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    user_assigned = update.callback_query.data

    db.set_todolist_filter_assigned(chat_id=chat_id, user_id=user_id, user_assigned=user_assigned)

    # Obtain list of todos
    todos = db.get_todo_list(chat_id=chat_id, user_id=user_id)
    if todos:
        db.set_todos_listed(chat_id, user_id, todos)

        todolist_send_item(context.bot, update, chat_id, user_id, 0)

        return TODOLIST_EDIT

    else:   # no todos available
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
    index = int(data[1]) if len(data) > 1 else None
    if operation == ACTION_COMPLETE:  # TODO #or operation == ACTION_UNCOMPLETE:
        db.set_pending_altered_todo(chat_id=chat_id, user_id=user_id, index=index, op={'completed': True})
        todolist_send_item(context.bot, update, chat_id, user_id, index)

        return TODOLIST_EDIT

    # TODO
    elif operation == ACTION_EDIT:
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Type to edit TODO:\n ```{0}```".
                                      format(db.todos_listed[(chat_id, user_id)][index]['description']),
                                      parse_mode=ParseMode.MARKDOWN)

        return TODOLIST_EDIT_TODO
    elif operation == ACTION_POSTPONE:
        pass

    # Store changes!
    elif operation == ACTION_FINISH:

        pending_changes = db.get_pending_changes_todo(chat_id, user_id)
        if pending_changes:
            context.bot.edit_message_text(chat_id=chat_id,
                                          message_id=update.callback_query.message.message_id,
                                          text=pending_changes,
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=binary_keyboard())
            return TODOLIST_FINISH
        else:
            context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="No changes!")
            return ConversationHandler.END


    elif operation == ACTION_NEXT or operation == ACTION_BACK:
        todolist_send_item(context.bot, update, chat_id, user_id, index)
        return TODOLIST_EDIT

    elif operation == ACTION_NONE:
        return TODOLIST_EDIT

    return TODOLIST_EDIT #ConversationHandler.END

def todolist_edit_todo(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    edited_description = update.message.text
   # db.set_pending_altered_todo(chat_id=chat_id, user_id=user_id, index=index, op={'description': edited_description})
 #   todolist_send_item(context.bot, update, chat_id, user_id, index)

    return TODOLIST_EDIT

def todolist_finish(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    operation = update.callback_query.data
    if operation == '1':
        db.set_changes_todo(chat_id=chat_id, user_id=user_id)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Changes saved!")
    else:
        db.clear_pending_changes_todo(chat_id, user_id)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Restore version!")
    return ConversationHandler.END

def delete_messages(bot, chat_id, user_id):
    for id in db.pop_messages_to_clear(chat_id, user_id):
        bot.delete_message(chat_id=chat_id,
                           message_id=id,
                           )  # TODO : check timeout option!


# TODO
def todolist_cancel(update, context):
    pass


# TODOLIST
todolist_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('todolist', todolist_start)],
    states={
        TODOLIST_CATEGORY: [CallbackQueryHandler(todolist_category)],
        TODOLIST_ASSINGNED: [CallbackQueryHandler(todolist_assigned)],
        TODOLIST_EDIT: [CallbackQueryHandler(todolist_edit)],
        TODOLIST_EDIT_TODO: [MessageHandler(Filters.text,todolist_edit_todo)],
        TODOLIST_FINISH: [CallbackQueryHandler(todolist_finish)]
    },
    fallbacks=[CommandHandler('todolist_cancel', todolist_cancel)]
)