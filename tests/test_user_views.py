"""User views tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py
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

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

class UserViewsTestCase(TestCase):
    """Test the User Views"""

    @classmethod
    def setUpClass(cls):
        db.session.execute(text('ALTER SEQUENCE users_id_seq RESTART'))
    

    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()
        self.client = app.test_client()
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()

    
    
    def tearDown(self):
        '''Clean up any fouled transaction'''
        db.session.rollback()


    def test_following_page(self):
        """Tests that a logged-in user can see the following and follower pages 
        of other users"""
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )
        u3 = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD3"
        )
        db.session.add_all([u2, u3])
        db.session.commit()
        self.testuser.following.append(u2)
        u2.following.append(u3)
        db.session.commit()
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)

            user2 = User.query.filter_by(username="testuser2").one()

            resp = c.get(f"/users/{user2.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)

            resp = c.get(f"/users/{user2.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser3", html)
    
    def test_following_page_logged_out(self):
        """Ensures that a logged out user can't see any following/follower
        pages"""
        with self.client as c:
            resp = c.get("/users/1/following")
            html = resp.get_data(as_text=True)

            #make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertIn("Redirecting", html)

    def test_send_message(self):
        """When logged in, can you add a message as yourself?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "This is a test"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "This is a test")

            resp = c.get("/")
            html = resp.get_data(as_text=True)
            #Make sure the message is on the feed page
            self.assertIn("This is a test", html)
    
    def test_delete_message(self):
        """When logged in, can you delete one of your messages?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved, so we can have
            # the rest of ours test
            c.post("/messages/new", data={"text": "This is a test"})
            msg = Message.query.one()
            
            resp = c.post(f"/messages/{msg.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Message.query.count(), 0) #ensure there are no messages
    
    def test_messages_logged_out(self):
        """When logged out, can you add or delete messages?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved
            #Make a message to attempt to delete later
            c.post("/messages/new", data={"text": "This is a cool msg"})
            c.get("/logout")

            resp = c.post("/messages/new", data={"text": "This is another message"})
            #make sure it redirects
            self.assertEqual(resp.status_code, 302)

            message = Message.query.filter_by(text="This is a cool msg").one()
            resp2 = c.post(f"/messages/{message.id}/delete")

            #make sure it redirects
            self.assertEqual(resp.status_code, 302)
    
    def test_messages_as_another_user(self):
        """When logged in, can you add or delete messages as another user?
            It appears that there's no easy way to add a message as another 
            user. Because the message is sent as a post request, it's not
            like someone can just type in a specific url. All messages are 
            created using the /messages/new route, not specifying the user.

            We can however test whether you can delete other people's messages.
        """
        self.testuser2 = User.signup(
            email="test2@test.com",
            username="otheruser",
            password="HASHED_PASSWORD2",
            image_url=None
        )
        db.session.commit()

        other_user = User.query.filter_by(username="otheruser").one()
        with self.client as c:
            with c.session_transaction() as sess: 
                #I'm assuming this is the way a hacker would attempt to add a message as
                #another user (By setting the session user key to the other user's id)
                sess[CURR_USER_KEY] = self.testuser.id
            # Now, that session setting is saved
            c.post("/messages/new", data={"text": "My first message"}) 
            msg_to_delete = Message.query.filter_by(text="My first message").first()
            c.get("/logout")

            # Now, log in as other user.
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.post(f"/messages/{msg_to_delete.id}/delete")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(Message.query.count(), 1) #Make sure the message is still there
