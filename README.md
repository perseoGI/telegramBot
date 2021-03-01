# PlaneandingBot

**You can find this bot active in Telegram! \
Look for @PlaneandingBot and start managing your tasks!**

Planeanding Telegram bot will help you managing your tasks by:
- Creating tasks
- Classifying them into categories
- Assigning them to you (if private chat) or to whoever in a group (if you add PlaneandingBot as a group/channel member)
- Assigning them a deadline to finish

While this bot will help also to manage your tasks by:
- Listing and filtering tasks
- Completing tasks
- Editing tasks
- Delaying tasks



### Development environment setup
For developing purposes, following dependencies versions has to be installed*:
- Python 3.7.0
- Pip 10.0

*This versions or higher

And a bot Token should be in your possession (talk to @botfather for creating your bot)

Create a file called **secret.py** on the root of the project and write:

    from os import environ
    environ['BOT_KEY'] = 'YOUR_BOT_TOKEN'

Create *virtual environment*, using following command:

    python -m venv ./venv

This will create a folder *venv* in the root of our project where python environment will reside

Activate virtual environment with following command:

    (Windows) venv\Scripts\activate

    (Linux/MacOS) source venv/bin/activate

Once venv activated, a *(venv)* will appear on the beginning of our prompt.
To install python dependencies:

    pip install -r requirements.txt


### Launch the bot
To launch the bot, just type following command:

    python main.py


### Misc
##### ConversationHandler on group/channel
For enabling ConversationHandler on a group or channel:

1. Talk to @botfather
2. disable privacy mode
3. remove the bot from all groups/channels
4. add the bot to all groups/channels

Step 3 and 4 are **NOT** optional



##### Chat_id curiosity

- Chat_id < 0 if the chat is a group
- Chat_id >0 if it is a private chat

##### Callback_data
callback_data in a InlineKeyboardButton **CAN NOT** BE '0', because 0 is NULL

##### Maximum messages to be send by a Bot
Telegram limits a bot up to:
- 20 msg / 60 s on a group or channel
- 30 msg / 1 s on a private chat

Check out main.py for a deeper explanation\
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits


##### Monospaced text

When sending a message with the bot on monospaced format, surround text with spaces:

    ```{0}```.format(text)  # will omit the first word on text
    ``` {0} ```.format(text)  # will work as expected


#### TODO

- [x] Generate events on the chat when deadline of a task is ready to finish
- [x] Generate events on the chat when deadline of a task has finished, allowing:
    - [x] Delay the task
    - [x] Mark as completed
- [] Manage categories:
    - [] Create a category (from outside a task creation interaction)
    - [] Edit name of category
    - [] Remove a category (if not empty, create a tour with uncompleted tasks in order to complete them)
- [] Command to list completed tasks


