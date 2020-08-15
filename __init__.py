from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_session import Session

# -------------------- INITIALIZE THE APP AND DATABASE ----------------------- #

app = Flask(__name__)  # create app instance

app.config['SECRET_KEY'] = 'ee31769c0a0d49b384d7bc70fe1fb3af'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # /// -> relative path
app.config['SESSION_TYPE'] = 'filesystem'  # to use Server side sessions
Session(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)  # to manage user sessions when logged in
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'  # bootstrap category like success and danger

from flaskblog import routes
