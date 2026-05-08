import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import cloudinary

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_NAME = os.getenv("DB_NAME")
    DB_SSL_CA = os.getenv("DB_SSL_CA")

    ssl_ca_path = os.path.join(BASE_DIR, "ca.pem")

    if os.getenv("DB_SSL_CA_CONTENT"):
        with open(ssl_ca_path, "w") as f:
            f.write(os.getenv("DB_SSL_CA_CONTENT"))

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?ssl_ca={ssl_ca_path}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    MAIL_SERVER   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        os.getenv("MAIL_DEFAULT_SENDER_NAME", "JobPlatform"),
        os.getenv("MAIL_USERNAME"),
    )

    # SERVER_NAME = "localhost:5000"
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost:5000")

def init_cloudinary(app):

    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"],
        secure=True
    )