#!/usr/bin/env python3
#
# A library that allows to create an inline calendar keyboard.
# grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.
"""


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import datetime
import calendar
from i18n import _
from utils.botinteractions import BotManager

from datetime import date

# this is declared on calendar.month_name but _ is needed to force create i18n translations
month_name = [_('January'), _('February'), _('March'), _('April'), _('May'), _('June'), _('July'), _('August'), _('September'), _('October'), _('November'), _('December')]
week_days_name = [_("Mo"), _("Tu"), _("We"), _("Th"), _("Fr"), _("Sa"), _("Su")]

botManager = BotManager()

def create_callback_data(action, year, month, day):
    """ Create the callback data associated to each button"""
    return ";".join([action, str(year), str(month), str(day)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")

def create_calendar_content(year=None, month=None):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """
    now = datetime.datetime.now()
    if year == None:
        year = now.year
    if month == None:
        month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = []

    # First row - Month and Year
    keyboard.append([(month_name[month] + " " + str(year), data_ignore)])

    # Second row - Week Days
    keyboard.append([(day, data_ignore) for day in week_days_name ])

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append((" ", data_ignore))
            elif now.day == day and now.month == month and now.year == year:
                row.append(( '[ ' + str(day) + ' ]', create_callback_data("DAY", year, month, day)))
            else:
                row.append(( str(day), create_callback_data("DAY", year, month, day)))
        keyboard.append(row)
    # Last row - Buttons
    row = [
        ( "<", create_callback_data("PREV-MONTH", year, month, day)),
        ( _("No deadline"), create_callback_data("STOP", year, month, day)),
        ( ">", create_callback_data("NEXT-MONTH", year, month, day))
    ]
    keyboard.append(row)

    return keyboard

# def create_calendar(year=None, month=None):
    # """
    # Create an inline keyboard with the provided year and month
    # :param int year: Year to use in the calendar, if None the current year is used.
    # :param int month: Month to use in the calendar, if None the current month is used.
    # :return: Returns the InlineKeyboardMarkup object with the calendar.
    # """
    # now = datetime.datetime.now()
    # if year == None:
        # year = now.year
    # if month == None:
        # month = now.month
    # data_ignore = create_callback_data("IGNORE", year, month, 0)
    # keyboard = []
    # # First row - Month and Year
    # row = []
    # row.append(
        # InlineKeyboardButton(
            # calendar.month_name[month] + " " + str(year), callback_data=data_ignore
        # )
    # )
    # keyboard.append(row)
    # # Second row - Week Days
    # row = []
    # for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        # row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    # keyboard.append(row)

    # my_calendar = calendar.monthcalendar(year, month)
    # for week in my_calendar:
        # row = []
        # for day in week:
            # if day == 0:
                # row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            # else:
                # row.append(
                    # InlineKeyboardButton(
                        # str(day),
                        # callback_data=create_callback_data("DAY", year, month, day),
                    # )
                # )
        # keyboard.append(row)
    # # Last row - Buttons
    # row = []
    # row.append(
        # InlineKeyboardButton(
            # "<", callback_data=create_callback_data("PREV-MONTH", year, month, day)
        # )
    # )
    # row.append(
        # InlineKeyboardButton(
            # "No deadline", callback_data=create_callback_data("STOP", year, month, day)
        # )
    # )
    # row.append(
        # InlineKeyboardButton(
            # ">", callback_data=create_callback_data("NEXT-MONTH", year, month, day)
        # )
    # )
    # keyboard.append(row)

    # return InlineKeyboardMarkup(keyboard)

def process_calendar_selection(bot, update):
    """
    Process the callback_query. This method generates a new calendar if forward or
    backward is pressed. This method should be called inside a CallbackQueryHandler.
    :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns a tuple (Boolean,datetime.datetime), indicating if a date is selected
                and returning the date if so.
    """
    ret_data = False
    query = update.callback_query
    (action, year, month, day) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=query.id)
    elif action == "DAY":
        botManager.send_message(
            update=update,
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        #    ret_data = True,datetime.datetime(int(year),int(month),int(day))
        ret_data = datetime.datetime(int(year), int(month), int(day))
    elif action == "PREV-MONTH":
        pre = curr - datetime.timedelta(days=1)
        botManager.send_message(
            update=update,
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar_content(int(pre.year), int(pre.month)),
        )
    elif action == "NEXT-MONTH":
        ne = curr + datetime.timedelta(days=31)
        botManager.send_message(
            update=update,
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar_content(int(ne.year), int(ne.month)),
        )

    # NEW
    elif action == "STOP":
        botManager.send_message(
            update=update,
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        # ret_data = True, False # check for false in 2 tuple for STOP
        ret_data = "0"  # check for false in 2 tuple for STOP

    else:
        bot.answer_callback_query(
            callback_query_id=query.id, text="Something went wrong!"
        )
        # UNKNOWN

    if ret_data:
        return ret_data

    else:
        return False  # Check if False, if does, return CommandHandler who has invoked this function

