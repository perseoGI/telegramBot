import database as db
import requests
import re
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackQueryHandler
from utils.botinteractions import BotManager
from i18n import _

########################### Misc ###########################################

botManager = BotManager()


def start(update, context):
    botManager.send_message(
        update=update,
        chat_id=update.message.chat_id,
        text=_("Hey! I'm PlaneandingBot, let me help you managing your tasks :)"),
    )


def echo(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


def caps(update, context):
    text_caps = " ".join(context.args).upper()
    context.bot.send_message(chat_id=update.message.chat_id, text=text_caps)


def get_url():
    contents = requests.get("https://random.dog/woof.json").json()
    url = contents["url"]
    return url


def get_image_url():
    allowed_extension = ["jpg", "jpeg", "png"]
    file_extension = ""
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$", url).group(1).lower()
    return url


def bop(update, context):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=get_image_url())


def general_check(update, context):
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    # Check if user or chat exist in database and if not, insert them
    db.checkDatabase(chat_id=chat_id, user_id=user_id)
    # print("Incoming msg: ", update.message.text)


# def test(update, context):
#     chat_id = update.message.chat_id
#     for i in range(10):
#         context.bot.send_message(chat_id=chat_id, text="pruebaaa de spam "+ str(i))


misc_handlers = [
    CommandHandler("bop", bop),
    # CommandHandler('start', start),
    # CommandHandler('caps', caps),
    # CommandHandler('test', test)
]
# dp.add_handler(MessageHandler(Filters.text, echo))
misc_handler_low_priority = MessageHandler(
    Filters.text, general_check
)  # , group=2  TODO
