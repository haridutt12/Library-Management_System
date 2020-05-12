import unittest, json
from lms_api import create_app, token_required, get_env_variable
from models import Users, UserSchema, db, UserAuthentication, Books, BookIssue
from requests.auth import _basic_auth_str
from sqlalchemy import create_engine

POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = 'testdb'


class LMSTest(unittest.TestCase):

    def setUp(self):
        DB_URL = 'postgres+psycopg2://{user}:{pw}@{url}/{db}'.format(
            user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
            db=POSTGRES_DB)
        self.app = create_app(DB_URL)
        self.client = self.app.test_client()
        self.engine = create_engine(DB_URL)
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['SECRET_KEY'] = "secretkey"

    def test_lms(self):
        payload = {
            "email": "test@gmail.com",
            "username": "tester",
            "fname": "test",
            "lname": "unittests",
            "role": "staff"
        }
        self.headers = {"Content-Type": "application/json"}
        response = self.client.post('/users', headers=self.headers,
                                    data=json.dumps(payload))

        db_user = self.client.get('/users', headers=self.headers)

        self.token = response.json["token"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["username"],
                         db_user.json["user"][0]["username"])

        with self.subTest("activate user"):
            payload = {"password": "password"}
            response = self.client.post('/activate/{}'.format(self.token),
                                        headers=self.headers,
                                        data=json.dumps(payload))

            self.assertEqual(response.status_code, 200)
            db_user = self.client.get('/users', headers=self.headers)
            self.assertEqual(db_user.json["user"][0]['status'], "active")

        with self.subTest("login user"):
            self.headers = {"Content-Type": "application/json",
                            'Authorization': _basic_auth_str(username="tester",
                                                             password="password")}
            response = self.client.get('/login', headers=self.headers)
            self.token = response.json['token']
            self.assertEqual(response.status_code, 200)

        with self.subTest("Add Book"):
            self.headers = {'Content-Type': 'application/json',
                            "Authorization": self.token}
            payload = {
                "isbn": 1,
                "title": "test",
                "author": "testing",
                "publisher": "testing lms",
                "publication_year": "2014-01-21",
                "category": "cse",
                "count": 1
            }
            response = self.client.post('/books', headers=self.headers,
                                        data=json.dumps(payload))
            self.assertEqual(response.status_code, 200)

        with self.subTest("Get Books"):
            response = self.client.get('/books', headers=self.headers)
            self.assertEqual(response.json["book"][0]['title'], 'test')

        with self.subTest("Issue Book"):
            payload = {"uid": 1}
            response = self.client.post('/books/1/issue',
                                        headers=self.headers,
                                        data=json.dumps(payload))
            self.assertEqual(response.status_code, 200)

        with self.subTest("Get Issued Books"):
            response = self.client.get('/books/issued', headers=self.headers)
            self.assertEqual(response.status_code, 200)

        with self.subTest("Return Books"):
            payload = {"uid": 1}
            return_response = self.client.post('/books/1/return',
                                               headers=self.headers,
                                               data=json.dumps(payload))

            issue_response = self.client.get('/books/issued',
                                             headers=self.headers)
            self.assertEqual(return_response.status_code, 200)
            self.assertEqual(issue_response.json["issued books"][0]['status'],
                             'inactive')

        with self.subTest("user profile"):
            response = self.client.get('/users/profile', headers=self.headers)
            self.assertEqual(response.status_code, 200)

    # def test_delete_user_table(self):
    #     self.headers = {"Content-Type": "application/json"}
    #     print("i am executing")
    #     Users().__table__.drop(self.engine)
    #     response = self.client.get('/users', headers=self.headers)
    #     print(response.status_code, response.json)
    #     self.assertEqual(response.status_code, 404)

    def tearDown(self):
        BookIssue().__table__.drop(self.engine)
        Users().__table__.drop(self.engine)
        UserAuthentication().__table__.drop(self.engine)
        Books().__table__.drop(self.engine)

# if __name__ == "__main__":
#     unittest.main()
