import flask
from config import Config
config = Config()
def create_app():
    app = flask.Flask(__name__)
    config.init_app(app)
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app
