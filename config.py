import os
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'project')
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-replace-me')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    PORT = int(os.getenv('PORT', '5000'))
