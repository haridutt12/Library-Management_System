import unittest, json
from lms_api import create_app, token_required, get_env_variable
from models import db, Users
import random
import string
from sqlalchemy import create_engine

POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = 'testdb'


# user crud operations test
class UserTest(unittest.TestCase):

    def random_user(self):
        return ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=5))

    def setUp(self):
        # self.user = self.random_user()

        DB_URL = 'postgres+psycopg2://{user}:{pw}@{url}/{db}'.format(
            user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
            db=POSTGRES_DB)
        app = create_app(DB_URL)
        self.client = app.test_client()
        self.engine = create_engine(DB_URL)

    def test_signup(self):
        payload = {
            "email": "test@gmail.com",
            "username": "tester",
            "fname": "test",
            "lname": "unittests",
            "role": "staff"
        }
        headers = {"Content-Type": "application/json"}
        response = self.client.post('/users', headers=headers,
                                    data=json.dumps(payload))

        db_user = self.client.get('/users', headers=headers)

        self.token = response.json["token"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["username"], db_user.json["user"][0]["username"])
        print(payload["username"], db_user.json["user"][0]["username"])

        with self.subTest("activate user"):
            payload = {"password": "password"}
            response = self.client.post('/activate/{}'.format(self.token),
                                        headers=headers,
                                        data=json.dumps(payload))

            self.assertEqual(response.status_code, 200)
            db_user = self.client.get('/users', headers=headers)
            self.assertEqual(db_user.json["user"][0]['status'], "active")

        # with self.subTest("activate user"):
        #     user = self.random_user()
        #     payload = {
        #         "username": user,
        #         "email": user + "@gmail.com"
        #     }
        #
        #     headers = {"Content-Type": "application/json",
        #                'Authorization': _basic_auth_str(username="admin",
        #                                                 password="password")}
        #     r = self.client.put('/users/{}'.format(self.id), headers=headers,
        #                         data=json.dumps(payload))
        #     response = self.client.get('/users/{}'.format(self.id),
        #                                headers=headers)
        #     self.assertEqual(response.json["username"], payload["username"])
        #
        # with self.subTest("Delete user"):
        #     headers = {"Content-Type": "application/json",
        #                'Authorization': _basic_auth_str(username="admin",
        #                                                 password="password")}
        #     r = self.client.delete('/users/{}'.format(self.id),
        #                            headers=headers)
        #     response = self.client.get('/users/{}'.format(self.id),
        #                                headers=headers)
        #     self.assertEqual(response.status_code, 404)

    def tearDown(self):
        Users().__table__.drop(self.engine)


if __name__ == "__main__":
    unittest.main()
