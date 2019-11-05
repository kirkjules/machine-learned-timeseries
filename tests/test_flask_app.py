import os
import pytest
from flask import request, session, get_flashed_messages
from web_app.models import User


def test_db_fixture(dbsession):
    for x, y, z in dbsession().get_bind().connection.connection.execute(
        'PRAGMA database_list'):
            path_to_file = z
    assert path_to_file == '/Users/juleskirk/Documents/tutorials/instance/test.db'

def test_index_redirect(client):
    index = client.get('/index')
    assert index.data.find(
        b"you should be redirected automatically to target url")

def login(client, username, password):
    return client.post(
        '/login', data=dict(username=username, password=password),
        follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def test_login_logout(client, dbsession):
    """Make sure login and logout works."""

    u = User(username="username")
    u.set_password('password')
    dbsession.add(u)
    dbsession.commit()

    r = login(client, "username", "password")
    assert r.status_code == 200

    r = logout(client)
    assert r.status_code == 200

    r = login(client, "usnglnea", "password")
    assert r.status_code == 200

    r = login(client, "username", "pafgbajg")
    assert r.status_code == 200

    assert 0
