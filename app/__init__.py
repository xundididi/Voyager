from flask import Flask
from flask import render_template

from app.extensions import mongo
from app.extensions import csrf
from app.config import DevConfig


def create_app(config_class=DevConfig):
    app = Flask(__name__)

    app.config.from_object(config_class)

    mongo.init_app(app)
    csrf.init_app(app)

    # 注册 blueprint
    from app.blueprint import admin as admin_blueprint

    app.register_blueprint(admin_blueprint, url_prefix="/")

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app
