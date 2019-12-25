from telegram.ext import Updater
from database import init_db
from commands.todo import todo_conv_handler
from commands.todolist import todolist_conv_handler
from commands.miscelanea import miscelanea_handlers, miscelanea_handler_low_priority

from os import environ
import secret       # Secret key for bot. Just set environ with BOT_KEY

def main():
    # Create database
    init_db()
    print("Setting up bot")
    updater = Updater(environ['BOT_KEY'],  use_context=True)
    dp = updater.dispatcher

    # Miscelanea
    for handler in miscelanea_handlers:
        dp.add_handler(handler)
    dp.add_handler(miscelanea_handler_low_priority, group=2)    # general_check function has to have low priority to allow todo_description work

    # TODOs
    dp.add_handler(todo_conv_handler)

    # TODOLIST
    dp.add_handler(todolist_conv_handler)

    updater.start_polling()
    print("Starting bot")
    updater.idle()


if __name__ == '__main__':
    main()