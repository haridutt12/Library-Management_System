import os
import random
import string
from functools import wraps

import datetime
# from flask_sqlalchemy import
import jwt
from flask import Blueprint, jsonify
from flask import Flask, request, make_response, Response
from models import Users, UserSchema, db, ma, UserAuthentication, Books, \
    BookIssue, BooksSchema, BookIssueSchema

api = Blueprint("api", "/v0")


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


# the values of those depend on your setup and these values are stored in
# activate script of venv

def create_app(DB_URL):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = "secretkey"
    app.register_blueprint(api)
    db.init_app(app)

    db.create_all(app=app)
    ma.init_app(app)

    return app


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers['Authorization']
        print(token)
        if not token:
            return jsonify({'message': 'provide token'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            data_list = list(data.values())
            user_obj = Users.query.filter_by(username=data_list[0]).first()
            setattr(request, "user", user_obj)
        except Exception as e:
            return jsonify({'message': str(e)})

        return f(*args, **kwargs)

    return decorated


@api.route('/users', methods=['GET', 'POST'])
def add_users():
    if request.method == "POST":

        username = request.json['username']

        if Users.query.filter_by(username=username).first():
            return make_response({"err": "user already exist"}, 400)

        new_user = Users()
        new_user.email = request.json["email"]
        new_user.username = request.json["username"]
        new_user.fname = request.json["fname"]
        new_user.lname = request.json["lname"]
        new_user.role = request.json["role"]

        db.session.add(new_user)
        db.session.commit()

        token = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=20))

        user_authentication = UserAuthentication(username, token)
        db.session.add(user_authentication)
        db.session.commit()

        return make_response({"user": UserSchema().dump(new_user),
                              "token": token}, 200)

    all_users = Users.query.all()
    return make_response({"user": UserSchema(many=True).dump(all_users)}, 200)


@api.route('/activate/<token>', methods=['POST'])
def activate_user(token):
    ua = UserAuthentication.query.filter_by(token=token).first()

    if not ua:
        return Response({"error": "invalid token"}, status=401)

    user = Users.query.filter_by(username=ua.username).first()
    user.status = 'active'
    user.password = request.json['password']

    ua.varified = True
    db.session.add(ua)
    db.session.commit()
    return make_response({"verified": True}, 200)


@api.route('/login')
def login():
    auth = request.authorization
    user = Users.query.filter_by(username=auth.username).first()
    if user and user.password == auth.password:
        token = jwt.encode({'user': auth.username,
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                                days=7)}, app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify!', 401)


# handler for resource not found
@api.errorhandler(404)
def page_not_found(e):
    return Response({"error": "invalid url"}, status=404)


@api.route('/books', methods=["GET", "POST"])
@token_required
def books():
    if request.method == "GET":
        all_books = Books.query.all()
        return BooksSchema(many=True).jsonify(all_books)

    book = Books.query.filter_by(isbn=request.json['isbn']).first()
    if book:
        book.isbn = request.json['isbn']
        book.publisher = request.json['publisher']
        book.author = request.json['author']
        book.publication_year = request.json['publication_year']
        book.category = request.json['category']
        book.count = request.json['count']
        book.title = request.json['title']
        db.session.commit()
        return BooksSchema().jsonify(book)
    else:
        book = Books()
        book.isbn = request.json['isbn']
        book.title = request.json['title']
        book.publisher = request.json['publisher']
        book.author = request.json['author']
        book.publication_year = request.json['publication_year']
        book.category = request.json['category']
        book.count = request.json['count']

        db.session.add(book)
        db.session.commit()
        return BooksSchema().jsonify(book)


@api.route('/books/<isbn>/issue', methods=["GET", "POST"])
@token_required
def issue(isbn):
    def is_already_assigned():
        # check if book belongs to library or not
        book = Books.query.filter_by(isbn=isbn).first()
        try:
            if book:
                issued_books = BookIssue.query.filter_by(
                    uid=request.json['uid'])
                for b in issued_books:
                    if b.bid == int(isbn) and b.status == 'active':
                        return True
                return False
        except Exception as e:
            print(e)

    if request.method == "POST" and request.user.role == 'staff':
        if not is_already_assigned():
            user_id = request.json["uid"]
            book = Books.query.filter_by(isbn=isbn).first()
            book_count = book.count
            if book_count > 0:
                book_issue = BookIssue(isbn, user_id, "active")
                db.session.add(book_issue)
                db.session.commit()
                book.count -= 1
                db.session.add(book)
                db.session.commit()
                return make_response("book Assigned", 200)
            return make_response("Book Not Available", 404)

        return make_response('Book Already Assigned', 403)

    return make_response('Not Allowed', 405)


@api.route('/books/issued')
@token_required
def get_issued_books():
    if request.user.role == 'staff':
        issued_books = BookIssue.query.all()
        return BookIssueSchema(many=True).jsonify(issued_books)


@api.route('/books/<isbn>/return', methods=["GET", "POST"])
@token_required
def book_return(isbn):
    """TODO: check if book pre assigned or not"""
    if request.method == "POST" and request.user.role == "staff":
        book = Books.query.filter_by(isbn=isbn).first()
        book.count = book.count + 1
        db.session.commit()
        issued_book = BookIssue.query.filter_by(
            uid=request.json['uid']).first()
        issued_book.status = 'inactive'
        db.session.commit()
        return make_response({"Returned": book.isbn}, 200)


@api.route('/users/profile')
@token_required
def user_profile():
    user = request.user
    return make_response({"user": UserSchema().dump(user)}, 200)


#
# @api.route('/users/<uid>/fine')
# @token_required
#

if __name__ == '__main__':
    POSTGRES_URL = get_env_variable("POSTGRES_URL")
    POSTGRES_USER = get_env_variable("POSTGRES_USER")
    POSTGRES_PW = get_env_variable("POSTGRES_PW")
    POSTGRES_DB = get_env_variable("POSTGRES_DB")
    DB_URL = 'postgres+psycopg2://{user}:{pw}@{url}/{db}'.format(
    user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    app = create_app(DB_URL)
    app.run(debug=True)
