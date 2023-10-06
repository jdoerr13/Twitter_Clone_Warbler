"""User model tests."""

# run these tests like:
#
#    python3 -m unittest test_message_model.py


import os
from unittest import TestCase
from models import db, User, Message, Like, followers_following
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.user = User.signup("testuser", "test@test.com", "password", None)
        db.session.add(self.user)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transactions."""
        db.session.rollback()

    def test_message_repr(self):
        """Does the __repr__ method work as expected?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        expected_repr = f"<Message #{message.id}: Test message..."
        self.assertEqual(repr(message), expected_repr)

    def test_is_liked_by_when_liked(self):
        """Does is_liked_by successfully detect when a user has liked a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message) #this message is added to the DB
        db.session.commit()
#create like object as well
        like = Like(user_id=self.user.id, message_id=message.id)
        db.session.add(like)
        db.session.commit()

        self.assertTrue(message.is_liked_by(self.user))

    def test_is_liked_by_when_not_liked(self):
        """Does is_liked_by successfully detect when a user has not liked a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        self.assertFalse(message.is_liked_by(self.user))

    def test_like_count_zero_when_no_likes(self):
        """Does like_count return zero when no users have liked a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        self.assertEqual(message.like_count, 0)

    def test_like_count_correct_when_likes_exist(self):
        """Does like_count return the correct count when multiple users have liked a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.add(user2)
        db.session.commit()

        like1 = Like(user_id=self.user.id, message_id=message.id)
        like2 = Like(user_id=user2.id, message_id=message.id)

        db.session.add(like1)
        db.session.add(like2)
        db.session.commit()

        self.assertEqual(message.like_count, 2)

    def test_like_count_updates_on_like(self):
        """Does like_count property update correctly when a user likes a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.add(user2)
        db.session.commit()

        like1 = Like(user_id=self.user.id, message_id=message.id)
        db.session.add(like1)
        db.session.commit()

        self.assertEqual(message.like_count, 1)

        like2 = Like(user_id=user2.id, message_id=message.id)
        db.session.add(like2)
        db.session.commit()

        self.assertEqual(message.like_count, 2)

    def test_like_count_updates_on_unlike(self):
        """Does like_count property update correctly when a user unlikes a message?"""
        message = Message(text="Test message", user_id=self.user.id)
        db.session.add(message)
        db.session.commit()

        user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.add(user2)
        db.session.commit()

        like1 = Like(user_id=self.user.id, message_id=message.id)
        like2 = Like(user_id=user2.id, message_id=message.id)

        db.session.add(like1)
        db.session.add(like2)
        db.session.commit()

        self.assertEqual(message.like_count, 2)

        db.session.delete(like2)
        db.session.commit()

        self.assertEqual(message.like_count, 1)

    def test_create_message(self):
        """Does creating a new message with valid data using Message.create work as expected?"""
        message = Message.create("Test message", self.user.id)
        db.session.commit()

        self.assertEqual(message.text, "Test message")
        self.assertEqual(message.user_id, self.user.id)

    def test_create_message_missing_required_data(self):
        """Does creating a new message with missing required data using Message.create raise the appropriate error?"""
        with self.assertRaises(IntegrityError):
            message = Message.create(None, self.user.id)
            db.session.commit()