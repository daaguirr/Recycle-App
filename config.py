class DefaultConfig(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = "1234"
    USER = "dagum"
    SQLALCHEMY_DATABASE_URI = "postgresql://" + USER + ":" + SECRET_KEY + "@localhost"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class AdminUser:
    first_name = "Daniel"
    last_name = "Aguirre"
    login = "dagum95"
    email = "dagum95@example.cl"
    password = "1234"