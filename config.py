import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vb69n83n89sv49es98e59889e9n6g'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False