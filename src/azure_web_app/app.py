from flask import Flask, render_template


def create_app():
    app = Flask(__name__)
    setup_routes(app)
    return app


def index():
    return render_template("index.html", name="Flask Bootstrap5")


def setup_routes(app):
    app.route("/")(index)


def run_app(debug: bool = True) -> None:
    app = create_app()
    app.run(debug=debug)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
