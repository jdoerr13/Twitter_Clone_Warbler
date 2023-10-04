import unittest
from app import app, db
from models import Message

class MessageModelTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_message(self):
        message = Message(text='Test message', user_id=1)  # Replace with a valid user_id
        db.session.add(message)
        db.session.commit()

        retrieved_message = Message.query.filter_by(text='Test message').first()
        self.assertIsNotNone(retrieved_message)
        self.assertEqual(retrieved_message.text, 'Test message')
        # Add more assertions for the Message model here

    # Add more Message model tests here
