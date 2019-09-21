from peewee import *

# Pragma to enable foreign keys on_delete and avoid bugs
db = SqliteDatabase('test1.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    __table_name__ = 'users'

    id = IntegerField(primary_key=True)     # user_id
    name = TextField()
    active = BooleanField(default=True)


class Chat(BaseModel):
    __table_name__ = 'chat'

    id = IntegerField(primary_key=True)  # chat_id
    # more data... eg. members count...
    count = IntegerField(null=True)
   # members = ManyToManyField(User, backref='members')


class ChatUser(BaseModel):
    __table_name__ = 'ChatUser'

    user_id = ForeignKeyField(User)
    chat_id = ForeignKeyField(Chat)


class Category(BaseModel):
    __table_name__ = 'category'

    id = IntegerField(primary_key=True)
    name = CharField()
    chat_id = ForeignKeyField(Chat)


class Todo(BaseModel):
    __table_name__ = 'todo'

    id = IntegerField(primary_key=True)
    category_id = ForeignKeyField(Category, backref='categories')
    creator_id = ForeignKeyField(User)
    chat_belonging_id = ForeignKeyField(Chat)
    assignment_users = ManyToManyField(User, backref='todos')
    description = TextField()
    # TODO: deadLine

UserTodos = Todo.assignment_users.get_through_model()

# class AssingmentTodos(BaseModel):
#
#     user_id = ForeignKeyField(User)
#     todo_id = ForeignKeyField(Todo)


pending_todos = {}

class TodoModel:
    def __init__(self, description):
        self.desc = description
        self.category_id = None
        self.users_id = []

    def setCategory(self, cat):
        self.category_id = cat

    def setUsers(self, user):
        self.users_id.append(user)

    def setDeadline(self, ):
        pass


def setPendingTodosDescription(chat_id, user_id, description):
   # pending_todos[(chat_id, user_id)] = TodoModel(description)
    pending_todos[(chat_id, user_id)] = Todo(description=description)
    print(pending_todos)


def setPendingTodosCategory(chat_id, user_id, category):
    pass
    #pending_todos[(chat_id, user_id)].category_id = category


def setPendingTodoAssingment(chat_id, user_id, assigned_user_id):
    pass
    #pending_todos[(chat_id, user_id)].users.add(User.get(User.id == assigned_user_id))


def storePendingTodo(chat_id, user_id):
    pass
 #   pending_todos[(chat_id, user_id)].save()
 #   print([todo.description for todo in Todo.select()])


def clearPendingTodo(chat_id, user_id):
    pass
  #  pending_todos[(chat_id, user_id)] = None   # TODO_ revisar




########### Category ##############

def getCategories(chat_id):
    return Category.select().where(Category.chat_id == chat_id).dicts()



def checkUserId(chat_id, user_id):

    chat = Chat.get(id == chat_id)
    if(chat):
        pass





def init_db():
    print("Creating...")
    db.create_tables([
        User,
        Chat,
      #  ChatUser,
        Category,
        Todo])

    print("Created")

    User.create(id=1, name='Cesar')
    User.create(id=2, name='Daniel')
    User.create(id=3, name='Perseo')

    users = User.select()
    print([user.name for user in users])


    Chat.create(id=1)
   # ChatUser.create(user_id=1, chat_id=1)

  #  q = Chat.update(members).where(id=1)
   # q.execute()

    #chats = Chat.select()
    #print([chat.members for chat in chats])


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


    #Todo.create(description='Primer todo', id_category=Category.select().where(Category.name == 'Diseño'))


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

if __name__ == '__main__':
    init_db()
