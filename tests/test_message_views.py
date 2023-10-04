import unittest
from models import db, connect_db, User, Message, Like
from forms import UserAddForm, LoginForm, MessageForm, UserProfileForm
from app import app, db

class MessageViewTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_messages_page(self):
        response = self.client.get('/messages')
        self.assertEqual(response.status_code, 200)
        # Add more tests for messages page

    # Add more view function tests for message-related routes here