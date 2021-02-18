from telegram import ParseMode, ChatAction

def send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN, message_id=None, reply_markup=None):
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    if message_id:
        bot.edit_message_text(chat_id=chat_id,
                              message_id=message_id,
                              text=text,
                              parse_mode=parse_mode,
                              reply_markup=reply_markup,
                              disable_notification=True)
    else:
        bot.send_message(chat_id=chat_id,
                         text=text,
                         parse_mode=parse_mode,
                         reply_markup=reply_markup,
                         disable_notification=True)
