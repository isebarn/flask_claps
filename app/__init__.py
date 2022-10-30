import logging
import os

from dotenv import load_dotenv

from flask import Flask, got_request_exception
from flask_cors import CORS
from flask_pymysql import MySQL

db = MySQL()

def get_config():
    app_env = os.environ.get("APP_ENV", 'DEVELOPMENT').lower().title()
    return f'config.{app_env}Config'


def create_app(test_config=False):
    from app.controllers import init_app
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(get_config())

    CORS(app)

    pymysql_connect_kwargs = {
        'user': app.config['MYSQL_USER'],
        'password': app.config['MYSQL_PASSWORD'],
        'host': app.config['MYSQL_HOST'],
        'port': int(app.config['MYSQL_PORT']),
        'database': app.config['MYSQL_DATABASE']
    }
    app.config['pymysql_kwargs'] = pymysql_connect_kwargs
    db.init_app(app)


    init_app(app)


    return app
