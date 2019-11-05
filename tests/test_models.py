import pytest
from web_app.models import User


@pytest.mark.incremental
class TestUserHandling:
    def test_add_user(self, dbsession):
        u = User(username="James")
        dbsession.add(u)
        dbsession.commit()
        result = dbsession.query(User).filter_by(username="James").all()
        assert len(result) == 1
        assert result[0].password_hash == None

    def test_set_password(self, dbsession):
        u = dbsession.query(User).filter_by(username="James").first()
        u.set_password('password')
        dbsession.add(u)
        dbsession.commit()
        result = dbsession.query(User).filter_by(username="James").all()
        assert len(result) == 1
        assert result[0].check_password('password')
