"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

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

class UserModelTestCase(TestCase):
    """Test the User Model"""

    # @classmethod
    # def setUpClass(cls):
    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
    
    def tearDown(self):
        '''Clean up any fouled transaction, reset primary key value to 1'''
        db.session.rollback()
        db.session.execute(text('ALTER SEQUENCE users_id_seq RESTART'))

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_user_repr(self):
        """Test whether the __repr__ method is working as expected"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

        self.assertEqual(repr(u), "<User #1: testuser, test@test.com>")
    
    def test_is_following(self):
        """Does is_following successfully detect 
        when user1 is following user2?"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )
        db.session.add_all([u1, u2])
        db.session.commit()

        self.assertFalse(u1.is_following(u2))

        #f = Follows(user_being_followed_id=2, user_following_id=1)
        u1.following.append(u2)
        #db.session.add(f)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
    
    def test_is_followed_by(self):
        """Does is_followed_by successfully detect 
        when user1 is followed by user2?"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )
        db.session.add_all([u1, u2])
        db.session.commit()

        self.assertFalse(u1.is_followed_by(u2))

        u2.following.append(u1)
        db.session.commit()
        self.assertTrue(u1.is_followed_by(u2))

    def test_signup(self):
        """Tests signup class method"""
        user = User.signup(username="spongebob",
                            email="test@test.com",
                            password="abc1234",
                            image_url="/static/images/default-pic.png")
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        found_user = User.query.one()
        self.assertEqual(found_user.username, "spongebob")
    
    def test_invalid_signup(self):
        """Tests signup class method with invalid credentials"""
        #should raise TypeError bc of missing image_url
        self.assertRaises(TypeError, User.signup, "spongebob",
                                                  "test3@test.com",
                                                  "supersecret")
        user = User.signup(username="spongebob",
                            email="test@test.com",
                            password="abc1234",     
                            image_url="/static/images/default-pic.png")
        db.session.commit()
        #Tests uniqueness restriction on usernames
        user2 = User.signup(username="spongebob",
                            email="test2@test.com",
                            password="abc12345",
                            image_url="/static/images/default-pic.png")
        #The assertRaises method appears to only support built-in Python exceptions,
        #and not exceptions from frameworks like SQLAlchemy 
        #self.assertRaises(IntegrityError, db.session.commit())
      

    def test_authenticate(self):
        """Tests authenticating with valid credentials"""
        user = User.signup(username="spongebob",
                            email="test@test.com",
                            password="abc1234",     
                            image_url="/static/images/default-pic.png")
        db.session.commit()
        self.assertTrue(User.authenticate("spongebob", "abc1234"))
        self.assertFalse(User.authenticate("spongebob1", "abc1234"))
        self.assertFalse(User.authenticate("spongebob", "abc12345"))
       
