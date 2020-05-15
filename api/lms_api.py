import os
import random
import string
from functools import wraps

from datetime import datetime
import jwt
from flask import Blueprint, jsonify, current_app
from flask import Flask, request, make_response, Response
from models import Users, UserSchema, db, ma, UserAuthentication, Books, \
    BookIssue, BooksSchema, BookIssueSchema, Fines, FineSchema, CollectedFines, \
    CollectedFineSchema

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
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
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

        user_authentication = UserAuthentication()
        user_authentication.username = username
        user_authentication.token = token
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


@api.route('/login', methods=["GET"])
def login():
    auth = request.authorization
    user = Users.query.filter_by(username=auth.username).first()
    if user and user.password == auth.password:
        token = jwt.encode({'user': auth.username,
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                                days=7)}, current_app.config['SECRET_KEY'])

        return make_response({'token': token.decode('UTF-8')}, 200)

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
        return make_response({"book": BooksSchema(many=True).dump(all_books)},
                             200)

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
        return make_response({"Book": BooksSchema().dump(book)}, 200)
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
        return make_response({"Book": BooksSchema().dump(book)}, 200)


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

    def collect_fine():
        user = Fines.query.filter_by(uid=request.json['uid']).first()
        if user:
            fine = user.fine
            user.fine = 0
            db.session.commit()
            user = CollectedFines()
            user.uid = request.json['uid']
            user.fine = fine
            db.session.add(user)
            db.session.commit()
        return True

    if request.method == "POST" and request.user.role == 'staff':
        if collect_fine():
            if not is_already_assigned():
                user_id = request.json["uid"]
                book = Books.query.filter_by(isbn=isbn).first()
                book_count = book.count
                if book_count > 0:
                    book_issue = BookIssue()
                    book_issue.bid = isbn
                    book_issue.uid = user_id
                    book_issue.status = "active"
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
        return make_response(
            {"issued books": BookIssueSchema(many=True).dump(issued_books)},
            200)
    return make_response('Not Authorized for this operation', 401)


@api.route('/books/<isbn>/return', methods=["GET", "POST"])
@token_required
def book_return(isbn):
    if request.method == "POST" and request.user.role == "staff":
        # Fine Collection
        user = Fines.query.filter_by(uid=request.json['uid']).first()
        collected_fine = CollectedFines()
        collected_fine.uid = request.json['uid']
        collected_fine.fine = user.fine
        db.session.add(collected_fine)
        db.session.commit()
        user.fine = 0
        db.session.commit()

        # Update book count  in Books table after return and changing status
        book = Books.query.filter_by(isbn=isbn).first()
        book.count = book.count + 1
        db.session.commit()
        issued_book = BookIssue.query.filter_by(uid=request.json['uid'], bid=isbn, status='active').first()
        issued_book.status = 'inactive'
        db.session.commit()
        return make_response({"Returned": book.isbn}, 200)


@api.route('/users/profile')
@token_required
def user_profile():
    user = request.user
    issued_books = BookIssue.query.filter_by(uid=user.id)
    return make_response({"user": UserSchema().dump(user),
                          "issued books": BookIssueSchema(many=True).dump(
                              issued_books)}, 200)


@api.route('/users/<uid>/fine')
@token_required
def user_fine(uid):
    issued_books = BookIssue.query.filter_by(uid=uid).all()
    active_books = [book for book in issued_books if book.status == "active"]

    total_fine = 0
    for book in active_books:
        delay = datetime.now() - book.created_at
        if delay.days > 14:
            fine = (delay.days - 14) * 10
            total_fine += fine

    fined_user = Fines.query.filter_by(uid=uid).first()
    if fined_user:
        fined_user.fine = total_fine
        db.session.commit()
    else:
        fined_user = Fines()
        fined_user.uid = uid
        fined_user.fine = total_fine
        db.session.add(fined_user)
        db.session.commit()

    user = Fines.query.filter_by(uid=uid).first()
    return make_response({"Fines": FineSchema().dump(user)}, 200)


if __name__ == '__main__':
    POSTGRES_URL = get_env_variable("POSTGRES_URL")
    POSTGRES_USER = get_env_variable("POSTGRES_USER")
    POSTGRES_PW = get_env_variable("POSTGRES_PW")
    POSTGRES_DB = get_env_variable("POSTGRES_DB")
    DB_URL = 'postgres+psycopg2://{user}:{pw}@{url}/{db}'.format(
        user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB)
    app = create_app(DB_URL)
    app.run(debug=True)
