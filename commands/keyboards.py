import database as db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from enum import Enum
from . import callbacks as Callback
from i18n import _


def create_locale_keyboard(translator, keyboard_content):
    keyboard = []
    for row in keyboard_content:
        button_row = []
        for button in row:
            button_row.append(
                InlineKeyboardButton(translator(button[0]), callback_data=button[1])
            )
        keyboard.append(button_row)

    return InlineKeyboardMarkup(keyboard)


def binary_keyboard_content():
    keyboard = [
        [(_("Yes"), "1"), (_("No"), "0")],  # Same line
    ]
    return keyboard


def todo_category_keyboard_content(chat_id, todolist):
    # Get categories IDs from database for a chat
    categories = db.getCategoriesIdFromChat(chat_id)
    keyboard = []
    db.connectDB()

    for category in categories:
        keyboard.append((category["name"], category["id"]))
    if todolist:
        keyboard.append((_("All categories"), -1))
    else:
        keyboard.append((_("Create new category"), -1))

    db.closeDB()
    keyboard_elements = [
        [element] for element in keyboard
    ]  # Create list of list (each button on different row)
    return keyboard_elements


def todo_member_keyboard_content(users_id, chat_id, bot, todolist=False):

    # Get user IDs members from database
    keyboard = []
    for user_id in users_id:
        # This is inefficient to generate an array of names and then try to tranlate those names
        usr = bot.getChatMember(chat_id=int(chat_id), user_id=user_id)
        keyboard.append((usr["user"]["first_name"], usr["user"]["id"]))

    if todolist:
        keyboard.append((_("All users"), -1))

    return [[element] for element in keyboard]


def todolist_item_keyboard_content(limit=None, completed=None):
    keyboard = [None] * 4
    keyboard[0] = [
        (_("Un-complete"), str(Callback.ACTION_UNCOMPLETE))
        if completed
        else (_("Complete"), str(Callback.ACTION_COMPLETE))
    ]
    keyboard[1] = [(_("Postpone"), str(Callback.ACTION_POSTPONE))]

    keyboard[2] = [(_("Edit"), str(Callback.ACTION_EDIT))]

    keyboard[3] = [
        (" ", str(Callback.ACTION_NONE))
        if limit in ("L", "B")
        else ("←", str(Callback.ACTION_BACK)),
        (_("Finish"), str(Callback.ACTION_FINISH)),
        (" ", str(Callback.ACTION_NONE))
        if limit in ("R", "B")
        else ("→", str(Callback.ACTION_NEXT)),
    ]

    return keyboard

def todocategory_options_keyboard_content():
    keyboard = [
        [ ( _("Create category"), str(Callback.CREATE_CATEGORY)) ],
        [ ( _("Delete category"), str(Callback.DELETE_CATEGORY)) ],
        [ ( _("Edit category"), str(Callback.EDIT_CATEGORY)) ]
    ]
    return keyboard


