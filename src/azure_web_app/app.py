from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template
from azure_web_app.sessions import login_required

from azure_web_app import auth, db, sessions
from azure_web_app._constants import SECRET_ENV_FILE


BOOKS = [
    {
        "title": "The Hunger Games",
        "author": "Suzanne Collins",
        "genre": "fiction",
        "priority": True,
        "note": "A story to explore about survival and difficult choices.",
    },
    {
        "title": "AI Snake Oil",
        "author": "Arvind Narayanan and Sayash Kapoor",
        "genre": "technology",
        "priority": True,
        "note": "A book about understanding what AI can and cannot do.",
    },
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "genre": "classic",
        "priority": False,
        "note": "A story that raises questions about creation and responsibility.",
    },
]


def create_app():
    load_dotenv(find_dotenv(SECRET_ENV_FILE))
    app = Flask(__name__)
    db.setup_for_app(app)
    sessions.setup_sessions(app)
    auth.setup_auth(app)
    setup_routes(app)
    return app


def index():
    return render_template("index.html", name="Carla")


def reading():
    """Display my reading interests using Bootstrap components."""
    return render_template("reading.html", books=BOOKS)


@login_required
def account():
    """Display the logged-in user's account."""
    return render_template("account.html")


@login_required
def reading_goals():
    """Show reading goals only to signed-in users."""
    return render_template("reading_goals.html")

def setup_routes(app):
    app.route("/")(index)
    app.route("/reading")(reading)
    app.route("/account")(account)
    app.route("/reading-goals")(reading_goals)


def run_app(debug: bool = True) -> None:
    app = create_app()
    app.run(debug=debug)


if __name__ == "__main__":
    run_app()