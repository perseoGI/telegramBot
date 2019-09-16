from peewee import *

db = SqliteDatabase('test1.db')

class BaseModel(Model):
    class Meta:
        database = db


class User(Model):
    __table_name__ = 'users'

    id = IntegerField(primary_key=True )
    name = TextField()
    active = BooleanField(default=True)


class Category(Model):
    __table_name__ = 'category'
    id = IntegerField(primary_key=True)
    name = TextField()


class Todo(Model):
    __table_name__ = 'todo'
    id = IntegerField(primary_key=True)
    description = TextField()
    id_category = ForeignKeyField(Category, backref='categories')
    users = ManyToManyField(User, backref='todos')


UserTodos = Todo.users.get_through_model()

def init_db():
    db.create_tables([
        User,
        Category,
        Todo])

    User.create(name='Cesar')
    User.create(name='Daniel')
    Category.create(name='Diseño')

    Todo.create(description='Primer todo', id_category=Category.select().where(Category.name == 'Diseño'))

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
