"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows

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

    @classmethod
    def setUpClass(cls):
        User.query.delete()
        db.session.execute(text('ALTER SEQUENCE users_id_seq RESTART'))

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

    def setUp(self):
        """Create test client, add sample data."""
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
    
    def tearDown(self):
        '''Clean up any fouled transaction, reset primary key value to 1'''
        db.session.rollback()

    def test_message_model(self):
        """Tests the basic model"""
        m = Message(text="This is a test",
                     user_id=1)
        db.session.add(m)
        db.session.commit()

        user = User.query.one()
        self.assertEqual(len(user.messages), 1)
        self.assertEqual(user.messages[0].text, "This is a test")
    
    
