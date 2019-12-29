import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler
from calendarBot import telegramcalendar
from .keyboards import todo_member_keyboard, todo_category_keyboard, binary_keyboard




########################### TODOLIST ###########################################

TODOLIST_CATEGORY, TODOLIST_ASSINGNED, TODOLIST_EDIT = range(3)

# First '0' to null. callback cannot take '0' value because it has to be a string ('0' is a null)
_, ACTION_COMPLETE, ACTION_POSTPONE, ACTION_EDIT, ACTION_BACK, ACTION_FINISH, ACTION_NEXT, ACTION_NONE = range(8)


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

def todolist_item_keyboard(todo_id, index=0, limit=None):
    keyboard = [None] * 4
    keyboard[0] = [InlineKeyboardButton("Complete", callback_data=str(ACTION_COMPLETE) + "," + str(todo_id))]

    keyboard[1] = [InlineKeyboardButton("Postpone", callback_data=str(ACTION_POSTPONE) + "," + str(todo_id))]

    keyboard[2] = [InlineKeyboardButton("Edit", callback_data=str(ACTION_EDIT) + "," + str(todo_id))]

    keyboard[3] = [InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit == 'L' else
                   InlineKeyboardButton("←", callback_data=str(ACTION_BACK) + "," + str(index - 1)),

                   InlineKeyboardButton("Finish", callback_data=str(ACTION_FINISH) + "," + str(todo_id)),

                   InlineKeyboardButton(" ", callback_data=str(ACTION_NONE)) if limit == 'R' else
                   InlineKeyboardButton("→", callback_data=str(ACTION_NEXT) + "," + str(index + 1))]

    return InlineKeyboardMarkup(keyboard)


# def todolist_comlete_postpone_keyboard(todo_id):
#     keyboard = []
#     row = []
#     row.append(InlineKeyboardButton("Complete", callback_data=str(TODOLIST_COMPLETE) + "," + str(todo_id)))
#     row.append(InlineKeyboardButton("Postpone", callback_data=str(TODOLIST_POSTPONE) + "," + str(todo_id)))
#     keyboard.append(row)
#     return InlineKeyboardMarkup(keyboard)

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

            text = "*{0}* \n``` {1} ```\n\n  _Created by {2}\n  Assigned to _{3}\n\n" \
                .format(db.get_category_name(todo['category_id']), todo['description'], creator_name,
                        assignment_users_names)

        else:  # individual chat, no need creator and assigned name
            text = "*{0}* \n``` {1} ```\n\n".format(db.get_category_name(todo['category_id']),
                                                    todo['description'])

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=text,
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=todolist_item_keyboard(todo_id=todo['id'], index=index, limit=limit))

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


# def todolist_assigned(update, context):
#     user_id = update.effective_user.id
#     chat_id = update.callback_query.message.chat_id
#     user_assigned = update.callback_query.data
#
#     db.set_todolist_filter_assigned(chat_id=chat_id, user_id=user_id, user_assigned=user_assigned)
#
#     # Obtain list of todos
#     todos = db.get_todo_list(chat_id=chat_id, user_id=user_id)
#     text = ""
#     if todos:
#         iter = 0
#         for todo in todos:
#             if chat_id < 0:  # group
#                 # TODO: en general_check, pasarle el nombre del usuario que hable para no tener que revisarlo aqui
#                 creator_name = get_username_from_id(context.bot, chat_id, todo['creator_id'])
#                 assignment_users_id = db.get_assigned_users(todo['id'])
#                 assignment_users_names = ""
#                 for i in range(len(assignment_users_id)):
#                     assignment_users_names += get_username_from_id(context.bot, chat_id, assignment_users_id[i].id)
#                     if i < len(assignment_users_id) - 2:
#                         assignment_users_names += ", "
#                     elif i == len(assignment_users_id) - 2:
#                         assignment_users_names += " and "
#
#                 text = "*{0}* \n``` {1} ```\n  _Created by {2}\n  Assigned to _{3}\n\n"\
#                     .format(db.get_category_name(todo['category_id']), todo['description'], creator_name, assignment_users_names)
#
#             else: # individual chat, no need creator and assigned name
#                 text += "*{0}* \n``` {1} ```\n\n".format(db.get_category_name(todo['category_id']),
#                                                          todo['description'])
#             if iter == 0:
#                 message_id = context.bot.edit_message_text(chat_id=chat_id,
#                                                             message_id=update.callback_query.message.message_id,
#                                                             text=text,
#                                                             parse_mode=ParseMode.MARKDOWN,
#                                                             reply_markup=todolist_comlete_postpone_keyboard(todo_id=todo['id'])).message_id
#                 print("id", message_id)
#             else:
#                 message_id = context.bot.send_message(chat_id=chat_id,
#                                          text=text,
#                                          parse_mode=ParseMode.MARKDOWN,
#                                          reply_markup=todolist_item_keyboard(todo_id=todo['id'])).message_id
#             iter += 1
#
#             db.add_messages_to_clear(chat_id, user_id, message_id) # Add message_id to clear them later
#
#
#         # End
#         context.bot.send_message(chat_id=chat_id,
#                                  text="Press FINISH to complete\nCANCEL to undo any operations",
#                                  parse_mode=ParseMode.MARKDOWN,
#                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("FINISH", callback_data=TODOLIST_FINISH),
#                                                                      InlineKeyboardButton("CANCEL", callback_data=TODOLIST_CANCEL)]]))
#
#         return TODOLIST_EDIT
#
#     else: # no todos available
#         context.bot.edit_message_text(chat_id=chat_id,
#                                       message_id=update.callback_query.message.message_id,
#                                       text="There is no pending todos :)\n*Now you are free!*",
#                                       parse_mode=ParseMode.MARKDOWN)
#
#         return ConversationHandler.END


def todolist_edit(update, context):
    user_id = update.effective_user.id
    chat_id = update.callback_query.message.chat_id
    data = update.callback_query.data.split(',')

    operation = int(data[0])

    if operation == ACTION_COMPLETE:
        todo_id = int(data[1])
        print(todo_id)
        db.set_pending_complete_todo(chat_id=chat_id, user_id=user_id, todo_id=todo_id)
        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Todo completed!",
                                      parse_mode=ParseMode.MARKDOWN)
        return TODOLIST_EDIT

    # TODO
    elif operation == ACTION_POSTPONE:
        pass

    # Store changes!
    elif operation == ACTION_FINISH:

        context.bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text="Done!")
        db.set_complete_todo(chat_id=chat_id, user_id=user_id)
        delete_messages(context.bot, chat_id, user_id)
        return ConversationHandler.END

    elif operation == ACTION_NEXT or operation == ACTION_BACK:
        index = int(data[1])
        todolist_send_item(context.bot, update, chat_id, user_id, index)

      #  db.clear_pending_complete_todo(chat_id=chat_id, user_id=user_id)
      #  delete_messages(context.bot, chat_id, user_id)
        return TODOLIST_EDIT

    elif operation == ACTION_NONE:
        return TODOLIST_EDIT

    return TODOLIST_EDIT #ConversationHandler.END

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
    },
    fallbacks=[CommandHandler('todolist_cancel', todolist_cancel)]
)