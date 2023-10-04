from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

bcrypt = Bcrypt()
db = SQLAlchemy()

# Define the association table for followers and followings
followers_following = db.Table(
    'followers_following',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('following_id', db.Integer, db.ForeignKey('users.id'))
)

class Like(db.Model):
    """Mapping user likes to messages."""

    __tablename__ = 'likes'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade')
    )

    liker = db.relationship('User', backref='likes')  # Change 'user' to 'liker'
    message = db.relationship('Message', backref='likes')


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )

    bio = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    messages = db.relationship('Message', backref='user', lazy='dynamic')

    # Relationship for users that the logged-in user is following

    following = db.relationship(
        'User',
        secondary=followers_following,
        primaryjoin=(followers_following.c.follower_id == id),
        secondaryjoin=(followers_following.c.following_id == id),
        backref='followers_of',
        lazy='dynamic'
    )

    followers = db.relationship(
        'User',
        secondary=followers_following,
        primaryjoin=(followers_following.c.following_id == id),
        secondaryjoin=(followers_following.c.follower_id == id),
        backref='following_by',
        lazy='dynamic'
    )
    
    # Add the single_parent=True flag here for the following relationship
    following = db.relationship(
        'User',
        secondary=followers_following,
        primaryjoin=(followers_following.c.follower_id == id),
        secondaryjoin=(followers_following.c.following_id == id),
        backref='followers_of',
        lazy='dynamic',
        cascade='all, delete-orphan',
        single_parent=True  # Add this line
    )



    user_liked_messages = db.relationship(
        'Message',
        secondary='likes',
        back_populates='likers'  # Explicitly specify the reverse relationship
    )
    # Define a relationship for liked messages
    user_likes = db.relationship('Like', backref='user', lazy='dynamic')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""
        return other_user in self.followers

    def is_following(self, other_user):
        """Is this user following `other_use`?"""
        return other_user in self.following
    
    @property
    def following_count(self):
        return self.followers.count()
    
    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def liked_messages_count(self):
        return self.user_likes.count()

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to the system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')

        user = cls(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If it can't find a matching user (or if the password is wrong), it returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    likers = db.relationship(
        'User',
        secondary='likes',
        back_populates='user_liked_messages'
    )

    def __repr__(self):
        return f"<Message #{self.id}: {self.text[:20]}..."

    @property
    def like_count(self):
        return Like.query.filter_by(message_id=self.id).count()

    def is_liked_by(self, user):
        return Like.query.filter_by(message_id=self.id, user_id=user.id).first() is not None

def connect_db(app):
    """Connect this database to the provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
    app.app_context().push()
    db.create_all()
