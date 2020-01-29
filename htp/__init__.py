import os
from flask import Flask
from celery import Celery
from flask_login import LoginManager


celery = Celery(__name__, broker=os.environ['CELERY_BROKER'])
# result_backend="redis://localhost:6379/0",
celery.conf.update(
    result_backend=f"db+{os.environ['DATABASE']}",  # CELERY_BACKEND'],
    accept_content=['pickle', 'json'],
    task_serializer='pickle',
    result_accept_content=['pickle', 'json'],
    result_serializer='pickle',
    worker_send_task_events=True,
    task_send_sent_event=True,
    result_chord_join_timeout=None
)
login = LoginManager()
login.login_view = 'auth.login'
# print(celery.conf.result_chord_join_timeout)


def create_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ['FLASK_SECRET_KEY'])

    # celery config goes here

    login.init_app(app)

    from htp.aux.database import db_session

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    from htp.views import index
    app.register_blueprint(index.bp)

    from htp.views import auth
    app.register_blueprint(auth.bp)

    from htp.views import get
    app.register_blueprint(get.bp)

    from htp.views import indicate
    app.register_blueprint(indicate.bp)

    from htp.views import signal
    app.register_blueprint(signal.bp)

    from htp.views import signal_prep
    app.register_blueprint(signal_prep.bp)

    return app
