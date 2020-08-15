from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin


# this is for managing sessions for each user - This how it keeps track of which user is currently logged in
@login_manager.user_loader
def load_user(user_id):  # function to get user details given the user ID
    return User.query.get(int(user_id))


# ---------- CONTAINS DEFINITION OF ALL DATABASE MODELS IN THE PROJECT --------------------- #

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(30), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)  # 'Post' <- Class. "author" is a dynamically
    text_files = db.relationship('FileUpload', backref='uploader', lazy=True)

    # retrieved column from post table. It does not physically exist in the schema

    def __repr__(self):
        return "User('{}', '{}')".format(self.username, self.email)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # not using utcnow() as this will
    # set the value to the current time for all objects
    content = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # "user" is the table name. In SQLAlchemy, tables are created for each of these classes with their table names
    # set to class names in lower case, user.id is the id column in the user table

    def __repr__(self):
        return "Post('{}', '{}', '{}')".format(self.title, self.user_id, self.date_posted)


class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text_file = db.Column(db.String(30), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # not using utcnow() as this will
    # set the value to the current time for all objects

    def __repr__(self):
        return "File('{}', '{}', '{}')".format(self.user_id, self.text_file, self.date_posted)

