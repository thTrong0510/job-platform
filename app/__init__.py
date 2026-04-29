from flask import Flask
from .extensions import db
from config import Config, init_cloudinary

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.config["CLOUDINARY_CLOUD_NAME"] = "ddczaiwxu"
    app.config["CLOUDINARY_API_KEY"] = "529253433446669"
    app.config["CLOUDINARY_API_SECRET"] = "_4PQw4A1aNKBkaX_gs2gfHviccA"

    init_cloudinary(app)

    # register blueprints
    from .routes.auth.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.candidate.manage_cvs import candidate_bp
    from .routes.candidate.manage_profile import candidate_profile_bp
    from .routes.candidate.cv_upload_routes import cv_upload_bp
    from .routes.candidate.job_routes import job_bp
    from .routes.employer.employer_auth_routes import employer_bp
    from .routes.employer.job_routes import employer_job_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(cv_upload_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(employer_job_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(candidate_profile_bp)

    return app