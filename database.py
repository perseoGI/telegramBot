from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model
import json

# Pragma to enable foreign keys on_delete and avoid bugs
db = SqliteDatabase("prod.db", pragmas={"foreign_keys": 1}, autoconnect=False)
# mysql_db = MySQLDatabase('telegramBot', user='bot', password='TODO', host='localhost', port=3316)


def connectDB():
    db.connect()


def closeDB():
    db.close()


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    __table_name__ = "users"

    id = IntegerField(primary_key=True)  # user_id
    name = TextField(null=True)
    active = BooleanField(default=True)


class Chat(BaseModel):
    __table_name__ = "chat"

    id = IntegerField(primary_key=True)  # chat_id
    # more data... eg. members count...


# count = IntegerField(null=True)
# members = ManyToManyField(User, backref='members')


class ChatUser(BaseModel):
    __table_name__ = "ChatUser"

    user_id = ForeignKeyField(User)
    chat_id = ForeignKeyField(Chat)


class Category(BaseModel):
    __table_name__ = "category"

    id = IntegerField(primary_key=True)
    name = CharField()
    chat_id = ForeignKeyField(Chat)


class Todo(BaseModel):
    __table_name__ = "todo"

    id = IntegerField(primary_key=True)
    category_id = ForeignKeyField(Category, backref="categories")
    creator_id = ForeignKeyField(User)
    chat_belonging_id = ForeignKeyField(Chat)
    assignment_users = ManyToManyField(User, backref="todos")
    description = TextField()
    deadline = DateField(null=True)
    # deadline = DateTimeField(null=True)
    completed = BooleanField(default=False)


UserTodo = (
    Todo.assignment_users.get_through_model()
)  # Table to relates User with Todo.assignment_users

# class AssingmentTodos(BaseModel):
#
#     user_id = ForeignKeyField(User)
#     todo_id = ForeignKeyField(Todo)


pending_todos = {}
pending_assignment_users = {}
pending_background_todo_ids = {}


class TodoModel:
    def __init__(self, description):
        self.desc = description
        self.category_id = None
        self.users_id = []

    def setCategory(self, cat):
        self.category_id = cat

    def setUsers(self, user):
        self.users_id.append(user)

    def setDeadline(
        self,
    ):
        pass


def setPendingTodosDescription(chat_id, user_id, description):
    pending_todos[(chat_id, user_id)] = Todo(
        chat_belonging_id=chat_id, creator_id=user_id, description=description
    )


def setPendingTodosCategory(chat_id, user_id, category):
    pending_todos[(chat_id, user_id)].category_id = category


def setPendingTodoAssingment(chat_id, user_id, assigned_user_id):
    db.connect()
    user = User.get(User.id == assigned_user_id)
    if not (chat_id, user_id) in pending_assignment_users:
        pending_assignment_users[(chat_id, user_id)] = []
    pending_assignment_users[(chat_id, user_id)].append(user.id)
    db.close()


def getPendingTodoNotAssigned(chat_id, user_id):
    db.connect()
    group_members = set([user["user_id"] for user in getUsersIdFromChat(chat_id)])
    db.close()
    if (chat_id, user_id) in pending_assignment_users:
        already_assigned = pending_assignment_users[(chat_id, user_id)]
        return list(
            group_members - set(already_assigned)
        )  # The members that are not assigned yet!
    else:
        return group_members  # All the members!


def getPendingTodoAssignment(chat_id, user_id):
    if (chat_id, user_id) in pending_assignment_users:
        return pending_assignment_users[(chat_id, user_id)]


def setPendingTodoDeadline(chat_id, user_id, deadline):
    pending_todos[(chat_id, user_id)].deadline = deadline


def storePendingTodo(chat_id, user_id):
    # print(pending_todos)
    db.connect()
    pending_todos[(chat_id, user_id)].save()
    if (chat_id, user_id) in pending_assignment_users:
        pending_todos[(chat_id, user_id)].assignment_users.add(
            pending_assignment_users.pop((chat_id, user_id))
        )
    db.close()
    clear_pending_todo(chat_id, user_id)


def clear_pending_todo(chat_id, user_id):
    if (chat_id, user_id) in pending_todos:
        del pending_todos[(chat_id, user_id)]


########### Category ##############


def getCategories(chat_id):
    print(db.connect())
    categories = Category.select().where(Category.chat_id == chat_id).dicts()
    db.close()
    return categories


# def printDB():
#     users = User.select()
#     print("Users: ", [user.id for user in users])
#     userChat = ChatUser.select()
#     for uC in userChat:
#         print('User_id {} on chat_id {}'.format(uC.user_id, uC.chat_id))

# def printTodos():
#     todos = Todo.select()
#     for todo in todos:
#         print('User_id created {}, desc: {}\n Assinged to {}'.format(todo.creator_id, todo.description, todo.assignment_users))


def checkDatabase(chat_id, user_id):
    # Check if user is register in database
    db.connect(reuse_if_open=True)
    exist = User.select().where(User.id == user_id).count()

    if not exist:  # Create the user
        user = User.create(id=user_id)

    # Check if the chat exist
    exist = Chat.select().where(Chat.id == chat_id).count()
    if not exist:  # Create a chat
        Chat.create(id=chat_id)
        ChatUser.create(user_id=user_id, chat_id=chat_id)

    # Check if that user is register in that chat
    else:
        exist = (
            ChatUser.select()
            .where((ChatUser.user_id == user_id) & (ChatUser.chat_id == chat_id))
            .count()
        )
        if not exist:
            ChatUser.create(user_id=user_id, chat_id=chat_id)

    db.close()


def getUsersIdFromChat(chat_id):
    users = ChatUser.select(ChatUser.user_id).where(ChatUser.chat_id == chat_id).dicts()
    return users


def getCategoriesIdFromChat(chat_id):

    categories = (
        Category.select(Category.name, Category.id)
        .where(Category.chat_id == chat_id)
        .dicts()
    )
    return categories


def createCategory(chat_id, name):
    db.connect(reuse_if_open=True)
    category_id = Category.create(name=name, chat_id=chat_id)
    db.close()
    return category_id._pk


########################### TODOLIST ###########################################


pending_todoslist = {}
pending_altered_todo = {}


def set_todolist_filter_category(chat_id, user_id, category):
    pending_todoslist[(chat_id, user_id)] = {"category": category}


def set_todolist_filter_assigned(chat_id, user_id, user_assigned):
    pending_todoslist[(chat_id, user_id)].update({"assignment_users": user_assigned})


# def get_todo_list(chat_id, user_id):
#     filters = pending_todoslist[(chat_id, user_id)]
# #TODO: mejorar eficiencia ...
#     if filters['assignment_users'] == '-1':
#         todos = Todo.select().where((Todo.chat_belonging_id == chat_id) &
#                                     (Todo.category_id == filters['category'] if filters['category'] != '-1' else True) &
#                                     (Todo.completed == False)).order_by(Todo.deadline.asc(nulls='LAST')).dicts()
#
#     else:
#         todos = Todo.select().join(UserTodo).where((Todo.chat_belonging_id == chat_id) &
#                                     (Todo.category_id == filters['category'] if filters['category'] != '-1' else True) &
#                                     (UserTodo.user == filters['assignment_users']) &
#                                     (Todo.completed == False)).order_by(Todo.deadline.asc(nulls='LAST')).dicts()
#     return todos


todos_listed = {}


def get_todo_list(chat_id, user_id):
    filters = pending_todoslist[(chat_id, user_id)]
    # TODO: mejorar eficiencia ...

    if not "assignment_users" in filters or filters["assignment_users"] == "-1":
        todos = (
            Todo.select()
            .where(
                (Todo.chat_belonging_id == chat_id)
                & (
                    Todo.category_id == filters["category"]
                    if filters["category"] != "-1"
                    else True
                )
                & (Todo.completed == False)
            )
            .order_by(Todo.deadline.asc(nulls="LAST"))
            .dicts()
        )

    else:
        todos = (
            Todo.select()
            .join(UserTodo)
            .where(
                (Todo.chat_belonging_id == chat_id)
                & (
                    Todo.category_id == filters["category"]
                    if filters["category"] != "-1"
                    else True
                )
                & (UserTodo.user == filters["assignment_users"])
                & (Todo.completed == False)
            )
            .order_by(Todo.deadline.asc(nulls="LAST"))
            .dicts()
        )

    db.connect()
    if todos:
        # Store todos in temporal memory
        todos_listed[(chat_id, user_id)] = {
            "todos": [todo for todo in todos],
            "index": 0,
            "completed": [],
            "delayed": {},
            "edited": {},
        }
        res = True
    else:
        res = False
    db.close()
    return res


def get_category_name(category_id):
    db.connect()
    category_name = Category.get(Category.id == category_id).name
    db.close()
    return category_name


def get_assigned_users(todo_id):
    db.connect()
    todos = Todo.get(Todo.id == todo_id)
    users = []
    for user in todos.assignment_users:
        users.append(user)
    db.close()
    return users


def get_todos_listed(chat_id, user_id):
    todo = None
    limit = None
    length = len(todos_listed[(chat_id, user_id)]["todos"])
    index = todos_listed[(chat_id, user_id)]["index"]
    if length > index:
        todo = todos_listed[(chat_id, user_id)]["todos"][index]
    if length == 1:
        limit = "B"  # B: Both
    elif length == index + 1:
        limit = "R"  # R: right
    elif index == 0:
        limit = "L"  # L: left

    return todo, limit


# Pre: offset will never overpass max size of 'todos' list
def set_todos_listed_index(chat_id, user_id, offset):
    todos_listed[(chat_id, user_id)]["index"] += offset


def change_todos_listed(chat_id, user_id, key, value):
    todo = todos_listed[(chat_id, user_id)]
    index = todo["index"]

    if key == "completed":
        if value:
            todo["completed"].append(index)
        else:
            todo["completed"].pop(index)

    elif key == "deadline":
        # Store previous deadline
        todo["delayed"].update({index: todo["todos"][index]["deadline"]})

    elif key == "description":
        # Store previous description
        todo["edited"].update({index: todo["todos"][index]["description"]})

    # Store change in provisional list
    todo["todos"][index].update({key: value})


def get_pending_changes_todo(chat_id, user_id):
    todos = todos_listed[(chat_id, user_id)]
    text = ""

    for index in todos["completed"]:
        text += "*Completed*:\n``` {0} ```\n \n".format(
            todos["todos"][index]["description"]
        )

    for index in todos["edited"]:
        text += "*Edited*:\n_Old_:\n``` {0} ```\n_New_:\n``` {1} ```\n\n".format(
            todos["edited"][index], todos["todos"][index]["description"]
        )

    for index in todos["delayed"]:
        text += "*Delayed*:\n_From_ {0} _to_ {1}\n``` {2} ```\n\n".format(
            todos["delayed"][index],
            todos["todos"][index]["deadline"],
            todos["todos"][index]["description"],
        )

    return text


def clear_todo_list(chat_id, user_id):
    del todos_listed[(chat_id, user_id)]


def store_changes_todo(chat_id, user_id):
    todos = todos_listed[(chat_id, user_id)]
    db.connect()
    for index in todos["completed"]:
        todo_id = todos["todos"][index]["id"]
        Todo.set_by_id(todo_id, {"completed": True})

    for index in todos["edited"]:
        todo_id = todos["todos"][index]["id"]
        Todo.set_by_id(todo_id, {"description": todos["todos"][index]["description"]})

    for index in todos["delayed"]:
        todo_id = todos["todos"][index]["id"]
        Todo.set_by_id(todo_id, {"deadline": todos["todos"][index]["deadline"]})

    db.close()
    clear_todo_list(chat_id, user_id)


from datetime import datetime, timedelta, date
from utils.botinteractions import BotManager
import threading

from commands.keyboards import binary_keyboard

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

botManager = BotManager()
from i18n import _


def checkTodosDeadlines():
    current_date = date.today()

    db.connect()
    pending_todos_expired = (
        Todo.select()
        .where((Todo.completed == False) & (current_date == Todo.deadline))
        .order_by(Todo.deadline.asc(nulls="LAST"))
        .dicts()
    )
    pending_todos_to_expire_tomorrow = (
        Todo.select()
        .where(
            (Todo.completed == False)
            & (current_date + timedelta(days=1) == Todo.deadline)
        )
        .order_by(Todo.deadline.asc(nulls="LAST"))
        .dicts()
    )

    for expired_todo in pending_todos_expired:
        text = _(
            "*Warning*:\nTask scheduled for day {0} is due today.\n\n``` {1} ```\n \nDo you want to postpone the task or mark it as completed?"
        ).format(expired_todo["deadline"], expired_todo["description"])
        keyboard = [
            [
                InlineKeyboardButton(
                    _("Postpone"),
                    callback_data="todo_deadline_achieved-postpone-{}".format(
                        expired_todo["id"]
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    _("Mark as completed"),
                    callback_data="todo_deadline_achieved-complete-{}".format(
                        expired_todo["id"]
                    ),
                )
            ],
        ]

        botManager.send_message(
            update=None,  # TODO: store last language for user and send it on the last message language
            chat_id=expired_todo["chat_belonging_id"],
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    for todo in pending_todos_to_expire_tomorrow:
        text = _(
            "*Reminder*:\nThe task scheduled for day {0} is due tomorrow.\n\n``` {1} ```"
        ).format(todo["deadline"], todo["description"])
        botManager.send_message(
            update=None, chat_id=todo["chat_belonging_id"], text=text
        )

    db.close()

    # Relaunch periodic thread
    current_datetime = datetime.today()
    tomorrow_datetime_at_9_am = current_datetime.replace(
        day=current_datetime.day, hour=9, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    seconds_to_next_morning = (
        tomorrow_datetime_at_9_am - current_datetime
    ).total_seconds()

    # threading.Timer(5, checkTodosDeadlines).start()
    threading.Timer(seconds_to_next_morning, checkTodosDeadlines).start()


def mark_todo_as_completed(todo_id):
    db.connect()
    Todo.set_by_id(todo_id, {"completed": True})
    completed_todo_description = Todo.get(Todo.id == todo_id).description
    db.close()
    return completed_todo_description


def set_pending_background_todo_id(chat_id, user_id, message_id, todo_id):
    pending_background_todo_ids[(chat_id, user_id, message_id)] = todo_id


def get_pending_background_todo_id_and_description(chat_id, user_id, message_id):
    todo_id = pending_background_todo_ids[(chat_id, user_id, message_id)]
    del pending_background_todo_ids[(chat_id, user_id, message_id)]
    db.connect()
    todo_description = Todo.get(Todo.id == todo_id).description
    db.close()
    return (todo_id, todo_description)


def set_todo_deadline(todo_id, newDeadline):
    db.connect()
    Todo.set_by_id(todo_id, {"deadline": newDeadline})
    db.close()


##################################################################
def init_db():
    print("Creating database...")
    db.connect()
    db.create_tables(
        [User, Chat, ChatUser, Category, Todo, UserTodo]
    )  # UserTodo relation get_through_model has also to be created
    print("Database created!!!")
    db.close()


def test():
    set_todolist_filter_category(1, 10, 1)
    print(pending_todoslist)
    set_todolist_filter_assigned(1, 10, 11)
    print(pending_todoslist)

    # User.create(id=1, name='Cesar')
    # User.create(id=2, name='Daniel')
    # User.create(id=3, name='Perseo')

    # Category.create(name='Diseño', chat_id=-236384136)
    # Category.create(name='Desarrollo', chat_id=-236384136)
    # Category.create(name='Economico', chat_id=-236384136)

    users = User.select()
    print([user.id for user in users])

    checkDatabase(1, 10)  # non-existent chat and user
    checkDatabase(1, 11)  # existent chat and non-existent user
    checkDatabase(2, 11)  # no existent chat and existent user

    print("____________")
    users = getUsersIdFromChat(1)
    print(vars(users))
    for user in users:
        print(user["user_id"])
        print(type(int(user["user_id"])))
        # print(user['user_id'])
        # a = user['user_id']
        # print(a)
        # print(vars(a))

    # Chat.create(id=1)


# ChatUser.create(user_id=1, chat_id=1)

#  q = Chat.update(members).where(id=1)
# q.execute()

# chats = Chat.select()
# print([chat.members for chat in chats])


# t = Todo(description='Aasdf')
#
# u = User(chat_id=1, user_id=2)
# u.name = "Pedro"
# print(u.save(force_insert=True))
#
# User.create(chat_id=1, user_id= 1, name='Cesar')
# #print(User.get(User.user_id == 2 ).name)
#
#


# User.create(name='Cesar')
# User.create(name='Daniel')
# dis = Category.create(name='Diseño')
# Category.create(name='Implementacion')
#
# User.insert(name='Perseo').execute()

# print(User.get(User.user_id == 3).name)


# categories = Category.select()
# print([cat.name for cat in categories])
#
#
# print(dis)
# for cat in categories:
#     print('{} on {}'.format(cat.name, cat.id))


# Todo.create(description='Primer todo', id_category=Category.select().where(Category.name == 'Diseño'))


# Get all usr todos
# usr = User.get(User.name == 'Cesar')
# for todo in usr.todos.order_by(Todo.id):
#     print(todo.description)


# # Get all students in "English 101":
# engl_101 = Course.get(Course.name == 'English 101')
# for student in engl_101.students:
#     print(student.name)


# # When adding objects to a many-to-many relationship, we can pass
# # in either a single model instance, a list of models, or even a
# # query of models:
# huey.courses.add(Course.select().where(Course.name.contains('English')))
#
# engl_101.students.add(Student.get(Student.name == 'Mickey'))
# engl_101.students.add([
#     Student.get(Student.name == 'Charlie'),
#     Student.get(Student.name == 'Zaizee')])
#
# # The same rules apply for removing items from a many-to-many:
# huey.courses.remove(Course.select().where(Course.name.startswith('CS')))
#
# engl_101.students.remove(huey)

# Calling .clear() will rem

if __name__ == "__main__":
    init_db()
