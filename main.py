from telegram.ext import Updater
from database import init_db, checkTodosDeadlines
from commands.todo import todo_conv_handler
from commands.todolist import todolist_conv_handler
from commands.miscelanea import miscelanea_handlers, miscelanea_handler_low_priority
from commands.category import todocategory_conv_handler
from os import environ
import secret       # Secret key for bot. Just set environ with BOT_KEY

from telegram.ext import messagequeue as mq
import telegram.bot
from telegram.utils.request import Request

# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits
# Class to "avoid" flood limits while sending multiple messages
# Telegram is limited to:
#       20 msg / 60 s   on groups or channels
#       30 msg / 1 s    on private chats
class MQBot(telegram.bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)

    @mq.queuedmessage
    def edit_message_text(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).edit_message_text(*args, **kwargs)


def main():
    # Create or launch database
    init_db()

    print("Setting up bot")
    token = environ.get('BOT_KEY')

    """ for test purposes limit global throughput to 3 messages per 3 seconds
    20 msg / 60 s ~= 0.33 msg/s -> 1 msg / 3 s -> 3 msg / 9 s ---> 6 msg / 18 s -> ... see defaults...
    Best ration (default ones)
       all_burst_limit = 30 msg
       all_time_limit_ms = 1000
       group_burst_limit = 20 msg
       group_time_limit_ms = 60000
    """
    message_queue = mq.MessageQueue()
    # set connection pool size for bot
    request = Request(con_pool_size=50)  # For example. TODO: test capacity
    bot = MQBot(token, request=request, mqueue=message_queue)
    updater = Updater(bot=bot, use_context=True)

    # updater = Updater(environ['BOT_KEY'],  use_context=True)      # Option without MQBot
    dp = updater.dispatcher

    # Initiate periodic thread
    checkTodosDeadlines()


    # Miscelanea
    for handler in miscelanea_handlers:
        dp.add_handler(handler)
    dp.add_handler(miscelanea_handler_low_priority, group=2)    # general_check function has to have low priority to allow todo_description work

    # TODOs
    dp.add_handler(todo_conv_handler)

    # TODOLIST
    dp.add_handler(todolist_conv_handler)

    # TODO_CATEGORY
    dp.add_handler(todocategory_conv_handler)

    updater.start_polling()
    print("Starting bot")
    updater.idle()


if __name__ == '__main__':
    main()
