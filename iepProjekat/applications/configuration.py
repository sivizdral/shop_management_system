class Configuration ():
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/forum"
    REDIS_HOST = "localhost"
    REDIS_THREADS_LIST = "threads"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"