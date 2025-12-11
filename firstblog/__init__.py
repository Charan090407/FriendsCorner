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

    # CLI command to mark all existing posts using the same Bard logic
    @app.cli.command('mark_posts')
    def mark_posts():
        import requests
        from firstblog.models import Post
        BARD_API_URL = "https://bard.googleapis.com/v1/query"  # replaced endpoint
        BARD_API_KEY = "AIzaSyDnEhZ4EnphPTr5zOlvdWoZ9USC2HJHL9I"

        def analyze(title, content):
            prompt_prefix = ("Search all over the web and detect if the provided description is fake or "
                             "not or it is just a neutral talk if it is fake return fake if it is real "
                             "return real and if it is just neutral talk return neutral description : ")
            prompt = prompt_prefix + " " + (title or "") + " " + (content or "")
            symbol = "➖"
            try:
                headers = {"Authorization": f"Bearer {BARD_API_KEY}", "Content-Type": "application/json"}
                resp = requests.post(BARD_API_URL, json={"prompt": prompt}, headers=headers, timeout=15)
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError:
                    data = {"text": resp.text}
                text = ""
                if isinstance(data, dict):
                    for key in ("result", "answer", "text", "output", "response"):
                        if key in data and isinstance(data[key], str):
                            text = data[key]
                            break
                    if not text:
                        text = " ".join(v for v in data.values() if isinstance(v, str))
                else:
                    text = str(data)
                t = (text or "").lower()
                if "fake" in t:
                    symbol = "⛔"
                elif "real" in t:
                    symbol = "✔️"
                elif "neutral" in t:
                    symbol = "➖"
            except Exception:
                symbol = "➖"
            return symbol

        with app.app_context():
            posts = Post.query.all()
            count = 0
            for p in posts:
                content = (p.content or "").lstrip()
                if content.startswith(("⛔", "✔️", "➖")):
                    continue
                symbol = analyze(p.title or "", p.content or "")
                p.content = f"{symbol}\n\n{p.content or ''}"
                count += 1
            db.session.commit()
            print(f"Marked {count} posts.")

    return app

