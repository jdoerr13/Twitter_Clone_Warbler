"""User model tests."""

# run these tests like:
#
#    python3 -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        if db.session.is_active:
            db.session.rollback()

        db.session.begin()

        User.query.delete()

        self.client = app.test_client()


    def teardown(self):
        """Create test client, add sample data."""
        db.session.remove()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

def test_user_model(self):
    """Does basic model work?"""
    user = User(
        email="test@test.com",
        username="testuser",
        password="HASHED_PASSWORD"
    )
    db.session.add(user)
    db.session.commit()

    # Now retrieve the user from the database
    u = User.query.get(user.id)

    # Check if the user object is not None
    self.assertIsNotNone(u)

    # Example: Check if the user's messages count is 0
    self.assertEqual(u.messages.count(), 0)

#2 & 3:
    def test_is_following(self):
        """Test the is_following method."""
        user1 = User(
            email="user1@test.com",
            username="user1",
            password="password"
        )
        user2 = User(
            email="user2@test.com",
            username="user2",
            password="password"
        )

        db.session.add(user1)
        db.session.add(user2)

        user1.following.append(user2)

        db.session.commit()

        self.assertTrue(user1.is_following(user2))
        self.assertFalse(user2.is_following(user1))

#4  & 5: 
    def test_is_followed_by(self):
        """Test the is_followed_by method."""
        user1 = User(
            email="user1@test.com",
            username="user1",
            password="password"
        )
        user2 = User(
            email="user2@test.com",
            username="user2",
            password="password"
        )

        db.session.add(user1)
        db.session.add(user2)

        user1.following.append(user2)

        db.session.commit()

        self.assertTrue(user2.is_followed_by(user1))  # user1 is followed by user2
        self.assertFalse(user1.is_followed_by(user2))  # user2 is not followed by user1

#6
    def test_create_user(self):
        """Test User.create method."""
        user = User.create(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )

        db.session.commit()
        retrieved_user = User.query.get(user.id)

        self.assertEqual(retrieved_user.username, "testuser")
#7
    def test_create_user_fail(self):
        """Test User.create method for failure."""
        with self.assertRaises(IntegrityError):  # Import IntegrityError from SQLAlchemy
            User.create(
                username="testuser",
                email="test@test.com",
                password=None  # Missing password
            )

        db.session.rollback()  # Rollback transaction due to failure

#8
    def test_authenticate_valid_credentials(self):
        """Test User.authenticate method with valid credentials."""
        # Create a user with known credentials
        user = User.signup("testuser", "test@test.com", "password123", None)

        # Authenticate the user with valid credentials
        authenticated_user = User.authenticate("testuser", "password123")

        # Check if the authenticated user matches the original user
        self.assertEqual(authenticated_user.id, user.id)


#9
    def test_authenticate_invalid_username(self):
        """Test User.authenticate method with an invalid username."""
        # Attempt to authenticate with an invalid username
        authenticated_user = User.authenticate("nonexistentuser", "password123")

        # Check if the authenticated user is False (i.e., not found)
        self.assertFalse(authenticated_user)


#10
    def test_authenticate_invalid_password(self):
        """Test User.authenticate method with an invalid password."""
        # Create a user with known credentials
        user = User.signup("testuser", "test@test.com", "password123", None)

        # Attempt to authenticate with an invalid password
        authenticated_user = User.authenticate("testuser", "wrongpassword")

        # Check if the authenticated user is False (i.e., password mismatch)
        self.assertFalse(authenticated_user)