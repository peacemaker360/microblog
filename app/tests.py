# tests.py / Python Unit testing
from datetime import datetime, timedelta
import os
import unittest
from app import app, db
from app.models import User, Post

basedir = os.path.abspath(os.path.dirname(__file__))

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db') #os.environ.get('DATABASE_URL')
        #db.create_all()
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        #db.session.remove()
        #db.drop_all()
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
        'd4c74594d841139328695756648b6bd6'
        '?d=identicon&s=128'))

    def test_follow(self):
        # Erst, testen ohne follower
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])
        # => Abfragen u1.followed.all() und u1.followers.all() sollten jeweils eine leer Liste als Ergebnis haben

        # Jetzt, testen mit follower
        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')
        # => e Ergebnisse geprüft: Folgt u1 u2? Hat u2 genau einen Follower? Stimmt der Username für u2? Usw



    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
            timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
            timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
            timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
            timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2) # john follows susan
        u1.follow(u4) # john follows david
        u2.follow(u3) # susan follows mary
        u3.follow(u4) # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

if __name__ == '__main__':
    unittest.main(verbosity=2)