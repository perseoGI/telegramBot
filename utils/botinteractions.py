from telegram import ParseMode, ChatAction

from i18n import install_user_language


class BotManager:
    class __impl:
        bot = None
        """ implementation of the singleton class """

        def send_message(
            self,
            chat_id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            message_id=None,
            reply_markup=None,
        ):
            # bot = self.bot if not bot else bot  # TODO
            print(self.bot)
            self.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            if message_id:
                self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_notification=True,
                )
            else:
                self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_notification=True,
                )

        def send_message(
            self,
            update,
            chat_id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            message_id=None,
            reply_markup=None,
        ):

            translate = install_user_language(update)

            self.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            if message_id:
                self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=translate(text),
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_notification=True,
                )
            else:
                self.bot.send_message(
                    chat_id=chat_id,
                    text=translate(text),
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_notification=True,
                )

    # The private class attribute holding the "one and only instance"
    __instance = __impl()

    def set_bot(self, bot):
        self.__setattr__("bot", bot)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)
