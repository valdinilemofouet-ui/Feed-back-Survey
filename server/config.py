import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/survey_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_dev_key") # À changer en prod !
    JWT_EXPIRATION_HOURS = 24