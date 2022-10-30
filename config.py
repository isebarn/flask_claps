import os


class Config(object):
    ENV = os.environ.get("APP_ENV")
    DEBUG = False
    TESTING = False

    # MYSQL CONFIGS
    # server=localhost;database=claps_net;user=root;password=blink182
    MYSQL_HOST = os.environ.get("MYSQL_HOST", 'localhost')
    MYSQL_USER = os.environ.get("MYSQL_USER", 'root')
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", 'blink182')
    MYSQL_PORT = os.environ.get("MYSQL_PORT", '3306')
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", 'claps_net')

class DevelopmentConfig(Config):
    DEBUG = True
