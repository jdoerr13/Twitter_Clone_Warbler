"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase


from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        # Create the main test user
        self.testuser = User.signup(username="testuser", email="test@test.com", password="testuser", image_url=None)

        # Create followers for the main test user
        follower1 = User.signup(username="follower1", email="follower1@test.com", password="follower1", image_url=None)
        follower2 = User.signup(username="follower2", email="follower2@test.com", password="follower2", image_url=None)

        self.testuser.followers.append(follower1)
        self.testuser.followers.append(follower2)

        db.session.commit()


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message(self):
            """Can a user delete their message?"""

            msg = Message(text="Test Message", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.post(f"/messages/{msg.id}/delete")

                self.assertEqual(resp.status_code, 302)
                self.assertIsNone(Message.query.get(msg.id))

    def test_view_followers_logged_in(self):
        """When logged in, can you view a user's followers page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Followers of", resp.data)

    def test_view_followers_logged_out(self):
        """When logged out, are you disallowed from visiting a user's followers page?"""

        resp = self.client.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"Followers of", resp.data)
        """When logged in, can you add a message as yourself?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Message.query.count(), 1)
            self.assertEqual(Message.query.first().text, "Hello")

    def test_add_message_logged_out(self):
        """When logged out, are you prohibited from adding messages?"""

        resp = self.client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Message.query.count(), 0)

    # Add similar tests for deleting messages, adding messages as another user, etc.

    def test_delete_message_logged_in(self):
        """When logged in, can you delete a message as yourself?"""

        msg = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Message.query.count(), 0)

    def test_delete_message_logged_out(self):
        """When logged out, are you prohibited from deleting messages?"""

        msg = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        resp = self.client.post(f"/messages/{msg.id}/delete", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Message.query.count(), 1)
    
    def test_user_profile(self):
        """Test user profile route."""

        with self.client as c:
            # Simulate a logged-in user session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Replace '1' with the actual user ID you want to test
            user_id_to_test = self.test_profile_user.id

            # Make a GET request to the user profile route
            resp = c.get(f"/users/{user_id_to_test}")

            # Assert that the response status code is 200 (OK)
            self.assertEqual(resp.status_code, 200)

            # Assert that the response data contains expected content
            self.assertIn(b"User Profile", resp.data)
            self.assertIn(b"Followers", resp.data)
            self.assertIn(b"Following", resp.data)
            # Add more assertions as needed based on your template
