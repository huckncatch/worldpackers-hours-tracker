import os
import logging
from flask import Flask
import db as database


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key-change-me"),
        DATABASE=os.path.join(app.instance_path, "worldpackers.db"),
    )
    if config:
        app.config.from_mapping(config)

    if "OPS_PASSWORD" not in app.config:
        app.config["OPS_PASSWORD"] = os.environ.get("OPS_PASSWORD", "changeme")
    if app.config["OPS_PASSWORD"] == "changeme":
        logging.warning("OPS_PASSWORD is not set — using insecure default 'changeme'")

    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)

    from routes.dashboard import bp as dashboard_bp
    from routes.log import bp as log_bp
    from routes.admin import bp as admin_bp
    from routes.api import bp as api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        database.init_db()
    app.run(host="0.0.0.0", port=5050, debug=False)
