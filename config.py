import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_USER = os.getenv('DB_USER', 'your_app_user')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'your_app_db')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"