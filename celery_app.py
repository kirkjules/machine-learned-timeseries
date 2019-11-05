#!/usr/bin/env python
# activated inside virtual environment with:
# (venv) $ celery worker -A celery_worker.celery --loglevel=info
from htp import celery, create_app


app = create_app()
app.app_context().push()
