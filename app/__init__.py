from flask import Flask
from .extensions import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # register blueprints
    from .routes.auth.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.candidate.cv_upload_routes import cv_upload_bp
    from .routes.candidate.job_routes import job_bp
    from .routes.employer.job_routes import employer_job_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(cv_upload_bp)
    app.register_blueprint(employer_job_bp)

    return app