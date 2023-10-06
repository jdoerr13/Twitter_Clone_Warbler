import os
from unittest import TestCase

from models import db, connect_db, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app since that will have already
# connected to the database)

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data)

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_signup(self):
        """Can a user sign up?"""

        with self.client as c:
            resp = c.post("/signup", data={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "newuser",
                "image_url": None
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hello, newuser!", resp.data)

    def test_signup_existing_user(self):
        """Will signing up with an existing username fail?"""

        with self.client as c:
            resp = c.post("/signup", data={
                "username": "testuser",
                "email": "test2@test.com",
                "password": "testuser",
                "image_url": None
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Username already taken", resp.data)

    def test_login(self):
        """Can a user login?"""

        with self.client as c:
            resp = c.post("/login", data={
                "username": "testuser",
                "password": "testuser"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hello, testuser!", resp.data)

    def test_logout(self):
        """Can a user logout?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/logout", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(CURR_USER_KEY, c.session)

    def test_unauthorized_logout(self):
        """Does an unauthorized user get an error when trying to logout?"""

        with self.client as c:
            resp = c.get("/logout", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

   
#this deteted an error in my delete user - the likes for the user are interfereing with delete
    def test_delete_user(self):
        """Can a user delete their account?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"You have been logged out", resp.data)
            self.assertIsNone(User.query.get(self.testuser.id))

    def test_unauthorized_delete_user(self):
        """Does an unauthorized user get an error when trying to delete their account?"""

        with self.client as c:
            resp = c.post("/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)
