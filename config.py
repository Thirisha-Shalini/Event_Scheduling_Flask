class Config:
    SECRET_KEY = "secretkey"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://flaskuser:flask123@localhost/event_scheduler"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
