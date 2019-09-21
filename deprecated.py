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
    # dp.add_handler(CallbackQueryHandler(todo_actions))


def todo_member_keyboard():
    group_members = ["Cesar", "Daniel", "Perseo"]

    button_list = [[KeyboardButton(s)] for s in group_members]
    ReplyKeyboardMarkup(button_list)

    keyboard = [[KeyboardButton('Cesar', callback_data='1')],
               [KeyboardButton('Daniel', callback_data='2')],
               [KeyboardButton('Perseo', callback_data='3')]
                ]
    return ReplyKeyboardMarkup(keyboard)






############################ TODOS ##################################

def todo_start(update, context):
    logger.info("New todo from: %s, cat: %d, user: %d", update.message.from_user.name, update.message.chat_id, update.message.from_user.id)
    update.message.reply_text(text="En que consiste la tarea?")
    return DESCRIPTION


def todo_description(update, context):
    user = update.message.from_user
    logger.info("Description of %s: %s", user.name, update.message.text)

    update.message.reply_text(text="En que categoria lo incluirias?")

    # Update model
    db.setPendingTodosDescription(
        chat_id=update.message.chat_id,
        user_id=update.message.from_user.id,
        description=update.message.text)

    return CATEGORY

def todo_category(update, context):
    user = update.message.from_user
    logger.info("Category of %s: %s", user.first_name, update.message.text)

    # Update model
    db.setPendingTodosCategory(
        chat_id=update.message.chat_id,
        user_id=update.message.from_user.id,
        category=update.message.text)


    chat_id = update.message.chat_id
    if (chat_id < 0 or True):       # It is a group
        context.bot.send_message(
                                chat_id=chat_id,
                                #inline_message_id=update.callback_query.message.message_id, # TODO revisar!
                                text="Asigne la tarea",
                                reply_markup=todo_member_keyboard())
        return ANOTHER_ASSIGNMENT
    # edit_message_text

    else:
        pass
    #    return ConversationHandler.END


# def todo_another_assignment(update, context):
#     print("____________")
#     user = update.callback_query.message.from_user
#     logger.info("Assignment of %s: %s", user.first_name, update.callback_query.data)
#     context.bot.send_message(chat_id=update.callback_query.message.chat_id,
#                              text="Desea asignar tarea a otro miembro mas?",
#                              reply_markup=binary_keyboard())
#     return ASSIGNMENT
#
#
# def todo_assignment(update, context):
#
#     answer = update.callback_query.data
#     print(answer)
#     if answer == '1':     # Continue asking for assignments
#         context.bot.send_message(chat_id=update.callback_query.message.chat_id,
#                                  text="Asigne la tarea",
#                                  reply_markup=todo_member_keyboard())
#         return ANOTHER_ASSIGNMENT
#
#     else:               # Next step
#         context.bot.send_message(chat_id=update.callback_query.message.chat_id,
#                                  text="Desea guardar la tarea?",
#                                  reply_markup=binary_keyboard())
#         return TODO_END
#
#
# def todo_end(update, context):
#     answer = update.callback_query.data
#     if answer == '1':
#         db.storePendingTodo(
#             chat_id=update.message.chat_id,
#             user_id=update.message.from_user.id)
#
#         update.callback_query.edit_message_text("Tarea guardada!")
#     else:
#         db.clearPendingTodo(
#             chat_id=update.message.chat_id,
#             user_id=update.message.from_user.id)
#
#         update.callback_query.edit_message_text("Tarea descartada")
#
#     return ConversationHandler.END
#
#
#
# def todo_cancel(update, context):
#     context.bot.get_chat()
#
#     user = update.message.from_user
#     logger.info("User %s canceled the conversation.", user.first_name)
#     update.message.reply_text('Tarea descartada!',
#                               reply_markup=InlineKeyboardMarkup([])
#                               )
#
#     return ConversationHandler.END


############################ Keyboards #########################################

def todo_member_keyboard():
    # TODO: obtain group members!

    keyboard = [[InlineKeyboardButton('Cesar', callback_data='1')],
               [InlineKeyboardButton('Daniel', callback_data='2')],
               [InlineKeyboardButton('Perseo', callback_data='3')]
                ]
    return InlineKeyboardMarkup(keyboard)


def binary_keyboard():
    keyboard = [[InlineKeyboardButton('Yes', callback_data='1')],
               [InlineKeyboardButton('No', callback_data='0')]]

    return InlineKeyboardMarkup(keyboard)



# todo_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('todo', todo_start)],
    #
    #     states={
    #         DESCRIPTION: [MessageHandler(Filters.text, todo_description)],
    #         CATEGORY: [MessageHandler(Filters.text, todo_category)],
    #         ANOTHER_ASSIGNMENT: [CallbackQueryHandler(todo_another_assignment)],
    #         ASSIGNMENT: [CallbackQueryHandler(todo_assignment)],
    #         TODO_END: [CallbackQueryHandler(todo_end)],
    #
    #     },
    #     fallbacks=[CommandHandler('todo_cancel', todo_cancel)]
    # )
    # dp.add_handler(todo_conv_handler)
