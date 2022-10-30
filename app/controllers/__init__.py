import flask_restx
from app.controllers.video import api as video_api


def init_app(app):
    api = flask_restx.Api(app)
    api.add_namespace(video_api, path='/videos')
