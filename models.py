from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref

bcrypt = Bcrypt()
db = SQLAlchemy()

# Define the association table for followers and followings
followers_following = db.Table(
    'followers_following',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')),
    db.Column('following_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
)


# from sqlalchemy import ForeignKeyConstraint

# class FollowersFollowing(db.Model):
#     __tablename__ = 'followers_following'

#     # Other columns and definitions

#     follower_id = db.Column(db.Integer, nullable=False)
#     following_id = db.Column(db.Integer, nullable=False)

#     # Define the foreign key constraint with ON DELETE CASCADE
#     ForeignKeyConstraint(
#         ['follower_id'],
#         ['users.id'],
#         ondelete='CASCADE'
#     )

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

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

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


    messages = db.relationship('Message', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # # Define the 'likes' relationship with cascade option
    # user_likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    #this shows the followers list on the page
    followers = db.relationship(
        'User',
        secondary=followers_following,
        primaryjoin=(followers_following.c.following_id == id),
        secondaryjoin=(followers_following.c.follower_id == id),
        backref='following_by',
        lazy='dynamic',
        cascade='all, delete-orphan',  # Cascade delete for followers
        single_parent=True  # Set the single_parent flag
    )
    #this shows the following list on the page
    following = db.relationship(
        'User',
        secondary=followers_following,
        primaryjoin=(followers_following.c.follower_id == id),
        secondaryjoin=(followers_following.c.following_id == id),
        backref='followers_of',
        lazy='dynamic'
    )

    user_liked_messages = db.relationship(
        'Message',
        secondary='likes',
        back_populates='likers'
    )

    user_likes = db.relationship('Like', backref='user', lazy='dynamic')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""
        return other_user in self.followers

    def is_following(self, other_user):
        """Is this user following `other_user`?"""
        return other_user in self.following
    
    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)
            user.followers.remove(self)  # Remove the reverse relationship
            return self
        
    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
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

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
    @classmethod
    def create(cls, email, username, password):
        """Create and return a new User."""
        user = cls(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return user

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
    
#Using this on show.html
    def is_liked_by(self, user):
        return Like.query.filter_by(message_id=self.id, user_id=user.id).first() is not None

#IMPLEMENT INTO APP- USING FOR TESTING
    @classmethod
    def create(cls, text, user_id):
        """Create and return a new message."""
        message = Message(text=text, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        return message


def connect_db(app):
    """Connect this database to the provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
    app.app_context().push()
    db.create_all()
