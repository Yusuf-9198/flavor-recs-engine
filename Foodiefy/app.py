from flask import Flask

from Foodiefy.config import STATIC_DIR, TEMPLATE_DIR
from Foodiefy.routes import register_routes


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
    )
    app.config["APP_NAME"] = "Restaurant Recommendation Service"
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)