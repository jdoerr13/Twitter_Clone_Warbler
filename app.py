import os
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, delete, and_, or_
from forms import UserAddForm, LoginForm, MessageForm, UserProfileForm
from models import db, connect_db, User, Message, Like, followers_following

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# toolbar = DebugToolbarExtension(app)


connect_db(app)
app.app_context().push()
db.create_all()

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)
        return redirect("/")
    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")
        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""
    session.pop(CURR_USER_KEY)
    flash("You have been logged out.", "success")
    return redirect("/")

##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """
    search = request.args.get('q')

    if not search:
        users = User.query.all()
        flash('Displaying all users', 'info')
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""
    user = User.query.get_or_404(user_id)
    is_own_profile = g.user == user

    liked_messages = [message.id for message in user.user_liked_messages]  # Get a list of liked message IDs

    # Calculate the counts
    following_count = user.following.count()
    followers_count = user.followers.count()

    # Fetch messages for the user and others they are following
    followed_users = [user.id for user in g.user.following]
    messages = (Message.query.join(User)
                    .filter((User.id.in_(followed_users)) | (User.id == g.user.id))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

    messages_liked_by_user = user.user_liked_messages  # Fetch liked messages for the user
    messages_liked_by_others = Message.query.filter(Message.id.in_(liked_messages)).all()  # Fetch messages liked by others

    return render_template(
        'users/show.html',
        user=user,
        messages=messages,
        is_own_profile=is_own_profile,
        liked_messages=liked_messages,
        messages_liked_by_user=messages_liked_by_user,
        messages_liked_by_others=messages_liked_by_others,
        following_count=following_count,
        followers_count=followers_count  # Pass the counts to the template
    )

@app.route('/users/<string:username>')
def user_profile(username):
    """Show user profile."""
    user = User.query.filter_by(username=username).first_or_404()
    is_own_profile = g.user == user

    # Add your profile rendering logic here

    return render_template(
        'users/show.html',
        user=user,
        is_own_profile=is_own_profile,
        # Other variables you want to pass to the template
    )

@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    follower_count = user.followers.count()  # Count of followers for the profile being viewed
    
    return render_template('users/following.html', user=user, follower_count=follower_count)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
  
    user = User.query.get_or_404(user_id)

    return render_template('users/followers.html', user=user)

@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    
    # Check if the user is already following
    if g.user.is_following(followed_user):
        flash(f"You are already following {followed_user.username}.", "info")
    else:
        # Add the user to the following list
        g.user.following.append(followed_user)
        # Add the current user to the follower list of the followed user
        followed_user.followers.append(g.user)
        db.session.commit()
        flash(f"You are now following {followed_user.username}.", "success")

    return redirect(f"/users/{follow_id}")

# Define the route to stop following a user
@app.route('/users/stop-following/<int:user_id>', methods=['POST'])
def stop_following(user_id):
    """Stop following a user."""

    # Check if the logged-in user is following the user to be unfollowed
    if g.user.is_following(user_id):
        # Remove the relationship
        followed_user = User.query.get(user_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        # Update the counts for the current user (who is unfollowing)
        g.user.following_count = g.user.following.count()
        # Update the counts for the user who was unfollowed
        followed_user.followers_count = followed_user.followers.count()

        db.session.commit()  # Commit the updates to the counts

        flash('You have stopped following this user.', 'success')
    else:
        flash('You are not following this user.', 'danger')

    # Redirect to the user's profile page
    return redirect(f'/users/{user_id}')


@app.route('/users/follow-unfollow/<int:user_id>', methods=['POST'])
def follow_unfollow(user_id):
    user_to_follow_unfollow = User.query.get_or_404(user_id)
    action = request.form.get('action')

    if action == 'follow':
        if not g.user.is_following(user_to_follow_unfollow):
            g.user.follow(user_to_follow_unfollow)
            flash(f'You are now following {user_to_follow_unfollow.username}.', 'success')
        else:
            flash(f'You are already following {user_to_follow_unfollow.username}.', 'info')
    elif action == 'unfollow':
        # Check if there is exactly one row to delete
        delete_count = db.session.query(followers_following).filter_by(follower_id=g.user.id, following_id=user_id).delete()
        if delete_count == 1:
            flash(f'You have unfollowed {user_to_follow_unfollow.username}.', 'success')
        elif delete_count == 0:
            flash(f'You are not following {user_to_follow_unfollow.username}.', 'danger')
        else:
            flash(f'You are now following {user_to_follow_unfollow.username}.', 'success')

    db.session.commit()

    # Redirect back to the user's profile page
    return redirect(url_for('user_profile', username=user_to_follow_unfollow.username))


#__________________________________________________________________________________________________
@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user_id = g.user.id
    form = UserProfileForm(obj=g.user)
    if form.validate():
        g.user.username = form.username.data
        g.user.email = form.email.data
        g.user.bio = form.bio.data
        g.user.image_url = form.image_url.data
        g.user.header_image_url = form.header_image_url.data
        g.user.location = form.location.data
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(f"/users/{g.user.id}")
    return render_template('users/edit.html', form=form, user_id=user_id)


@app.route('/users/<int:user_id>', methods=['POST', 'DELETE'])
def delete_user(user_id):
    if request.form.get('_method') == 'DELETE':
        user = User.query.get(user_id)
        if user:
            try:
                # Delete likes associated with the user
                Like.query.filter_by(user_id=user_id).delete()

                # Delete records in the followers_following table
                delete_statement = followers_following.delete().where(
                    or_(
                        followers_following.c.follower_id == user_id,
                        followers_following.c.following_id == user_id
                    )
                )
                db.session.execute(delete_statement)

                # Remove the user from the followers' following lists
                user.followers_by = []
                user.following = []

                # Delete the user
                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully', 'success')
            except Exception as e:
                # Handle any exceptions that may occur during the deletion process
                db.session.rollback()
                flash('Error deleting user', 'error')
                print("Error:", str(e))  # Add this line to print the error message
            return redirect(url_for('user_profile', username=user.username))  # Redirect to an appropriate route after deletion
        else:
            flash('User not found', 'error')
            return redirect(url_for('user_profile', username=user.username))  # Redirect to an appropriate route if the user is not found
    else:
        # Handle other POST requests here, if needed
        pass


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")
    return render_template('messages/new.html', form=form)

@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""
    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)

@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(f"/users/{g.user.id}")

##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    if g.user:
        followed_users = [user.id for user in g.user.following]
        messages_query = (Message.query.join(User)
                    .filter((User.id.in_(followed_users)) | (User.id == g.user.id))
                    .order_by(Message.timestamp.desc())
                    .limit(100))
        
        # Execute the query and retrieve the count
        messages = messages_query.all()
        messages_count = messages_query.count()
        
        liked_messages_count = Like.query.filter_by(user_id=g.user.id).count()
        return render_template('home.html', messages=messages, messages_count=messages_count, liked_messages_count=liked_messages_count, user=g.user)
    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""
    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req

@app.route('/like/<int:message_id>')
def like(message_id):
    if not g.user:
        flash('You must be logged in to like warbles.', 'danger')
        return redirect(url_for('login'))
    
    message = Message.query.get_or_404(message_id)
    
    if message.user_id == g.user.id:
        flash('You cannot like your own warbles.', 'danger')
    elif message in g.user.user_liked_messages:
        flash('You have already liked this warble.', 'info')
    else:
        like = Like(user_id=g.user.id, message_id=message_id)
        db.session.add(like)
        db.session.commit()
        flash('You liked a warble!', 'success')
    
    return redirect(request.referrer)

@app.route('/unlike/<int:message_id>')
def unlike(message_id):
    if not g.user:
        flash('You must be logged in to unlike warbles.', 'danger')
        return redirect(url_for('login'))
    
    message = Message.query.get_or_404(message_id)
    
    if message in g.user.user_liked_messages:
        like = Like.query.filter_by(user_id=g.user.id, message_id=message_id).first()
        db.session.delete(like)
        db.session.commit()
        flash('You unliked a warble.', 'success')
    else:
        flash('You cannot unlike a warble you have not liked.', 'info')
    
    return redirect(request.referrer)

@app.route('/liked_messages/<int:user_id>')
def liked_messages(user_id):
    """Show liked messages by a specific user."""
    user = User.query.get_or_404(user_id)
    liked_messages = user.user_liked_messages  # Fetch liked messages for the user
    
    return render_template('users/liked_messages.html', user=user, liked_messages=liked_messages)



    

    




