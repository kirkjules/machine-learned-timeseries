#!/usr/bin/env python
# activated inside virtual environment with:
# (venv) $ celery worker -A celery_app.celery --loglevel=info
import os
from htp import celery, create_app


app = create_app()
app.app_context().push()
