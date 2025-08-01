from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
load_dotenv()
from firstblog.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager=LoginManager()
login_manager.login_view='users.login'
login_manager.login_message_category = 'info'
mail = Mail()

migrate = Migrate(db)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app)

    from firstblog.users.routes import users
    app.register_blueprint(users)
    from firstblog.posts.routes import posts
    app.register_blueprint(posts)
    from firstblog.main.routes import main
    app.register_blueprint(main)
    from firstblog.errors.handlers import errors
    app.register_blueprint(errors)

    return app

