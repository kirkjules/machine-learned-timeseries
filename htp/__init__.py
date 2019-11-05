import os
from flask import Flask
from celery import Celery
from celery.backends import redis
from flask_login import LoginManager


celery = Celery(__name__, broker=os.environ['CELERY_BROKER'])
login = LoginManager()
login.login_view = 'auth.login'


# class CustomBackend(redis.RedisBackend):
#     def on_task_call(self, producer, task_id):
#         print("using custom backend")
#         pass

#        result_backend=f"{__name__}.CustomBackend:"
#        f"{os.environ['CELERY_BACKEND'].split('redis:')[1]}",


def create_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ['FLASK_SECRET_KEY'])

    celery.conf.update(
        result_backend=os.environ['CELERY_BACKEND'],
        accept_content=['pickle', 'json'],
        task_serializer='pickle',
        result_accept_content=['pickle', 'json'],
        result_serializer='pickle',
        worker_send_task_events=True,
        task_send_sent_event=True
    )

    login.init_app(app)

    from htp.database import db_session

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    from htp.views import home
    app.register_blueprint(home.bp)

    from htp.views import auth
    app.register_blueprint(auth.bp)

    from htp.views import acquire
    app.register_blueprint(acquire.bp)

    return app
