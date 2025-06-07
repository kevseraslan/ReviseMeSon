import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://E\\SQLEXPRESS/ReviseMe?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    
    # Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'inforeviseme@gmail.com'
    MAIL_PASSWORD = 'wjkn wyfm dmih rtsl'
    
    # Password reset settings
    PASSWORD_RESET_EXPIRATION = timedelta(hours=1)
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(_file_)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Notification settings
    DEFAULT_REPEAT_INTERVALS = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)
    }