from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import enum

db = SQLAlchemy()
ma = Marshmallow()


class UserRoleEnum(str, enum.Enum):
    student = 'student'
    staff = 'staff'
    admin = 'admin'


class UserStatusEnum(str, enum.Enum):
    active = 'active'
    pending = 'pending'
    suspended = 'suspended'


class BookCategoryEnum(str, enum.Enum):
    ece = 'ece'
    biotech = 'biotech'
    cse = 'cse'
    mba = 'mba'


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(),
                           server_onupdate=db.func.now())


class Users(BaseModel):
    __tablename__ = 'users'
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    fname = db.Column(db.String(30))
    lname = db.Column(db.String(30))
    role = db.Column(db.Enum(UserRoleEnum), default=UserRoleEnum.student,
                     nullable=False)
    status = db.Column(db.Enum(UserStatusEnum), default=UserStatusEnum.pending,
                       nullable=False)

    def __init__(self, username, email, fname, lname, role):
        self.username = username
        self.email = email
        self.fname = fname
        self.lname = lname
        self.role = role


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'email', 'status')


class UserAuthentication(BaseModel):
    username = db.Column(db.String(80))
    token = db.Column(db.String(20))
    varified = db.Column(db.Boolean, default=False)

    def __init__(self, username, token):
        self.username = username
        self.token = token


class Books(db.Model):
    __tablename__ = 'books'
    isbn = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    author = db.Column(db.String(30))
    publisher = db.Column(db.String(30))
    publication_year = db.Column(db.DATE)
    category = db.Column(db.Enum(BookCategoryEnum))
    count = db.Column(db.INTEGER)

    def __init__(self, isbn, title, author, publisher, publication_year,
                 category, count):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.publisher = publisher
        self.publication_year = publication_year
        self.category = category
        self.count = count


class BooksSchema(ma.Schema):
    class Meta:
        fields = (
            'isbn', 'title', 'author', 'publisher', 'publication_year',
            'category', 'count')


class BookIssue(BaseModel):
    bid = db.Column(db.INTEGER, db.ForeignKey('books.isbn'))
    uid = db.Column(db.INTEGER, db.ForeignKey('users.id'))

    def __init__(self, bid, uid):
        self.bid = bid
        self.uid = uid


class BookIssueSchema(ma.Schema):
    class Meta:
        fields = ('bid', 'uid')
