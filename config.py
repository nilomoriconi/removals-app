import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))          # carga variables

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

    # Usa la DB que venga por variable; si no existe ⇒ lanza error.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if SQLALCHEMY_DATABASE_URI is None:
        raise RuntimeError("DATABASE_URL not set – configure Postgres or SQLite")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY_SERVER = os.getenv("GOOGLE_MAPS_API_KEY_SERVER")
    GOOGLE_MAPS_API_KEY_CLIENT = os.getenv("GOOGLE_MAPS_API_KEY_CLIENT")

class DevelopmentConfig(Config):
    DEBUG = True
    # En desarrollo puedes permitir un fallback a SQLite:
    if SQLALCHEMY_DATABASE_URI is None:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'removalist.db')}"

class ProductionConfig(Config):
    DEBUG = False