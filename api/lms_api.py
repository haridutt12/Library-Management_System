import os
import random
import string
from functools import wraps

import datetime
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
POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = get_env_variable("POSTGRES_DB")


def create_app():
    app = Flask(__name__)
    DB_URL = 'postgres+psycopg2://{user}:{pw}@{url}/{db}'.format(
        user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
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
        email = request.json["email"]
        username = request.json["username"]
        fname = request.json["fname"]
        lname = request.json["lname"]
        role = request.json["role"]

        if Users.query.filter_by(username=username).first():
            return '{"err":"user already exist"}', 400

        new_user = Users(username, email, fname, lname, role)

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
    return UserSchema(many=True).jsonify(all_users)


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
    return Response({"verified": True}, status=200)


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
    if request.method == "GET" and request.user.role == 'student':
        all_books = Books.query.all()
        return BooksSchema(many=True).jsonify(all_books)
    book_data = request.json
    book = Books(book_data)
    db.session.add(book)
    db.session.commit()
    return BooksSchema.jsonify(book)


@api.route('/books/<isbn>/issue', methods=["GET", "POST"])
@token_required
def issue(isbn):
    if request.method == "GET" and request.user.role == 'staff':
        issued_book = BookIssue.query.filter_by(isbn=isbn)
        return BookIssueSchema.jsonify(issued_book)

    if request.method == "POST" and request.user.role == 'staff':
        user_id = request.json["uid"]
        book = Books.query.filter_by(isbn=isbn).first()
        book_count = book.count
        if book_count > 0:
            book_issue = BookIssue(isbn, user_id)
            db.session.add(book_issue)
            db.session.commit()
            book.count -= 1
            db.session.add(book)
            db.session.commit()
        return make_response('Book Not Available', 403)

    return make_response('Not Allowed', 405)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
