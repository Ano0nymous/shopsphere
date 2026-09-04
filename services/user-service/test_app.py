import os

import psycopg2
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import app as app_module  # noqa: E402
from app import app, init_db  # noqa: E402


@pytest.fixture(scope='session')
def test_db():
    admin = psycopg2.connect(dbname='postgres', user='shop', password='shoppass', host='localhost')
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute("DROP DATABASE IF EXISTS shopsphere_test;")
    cur.execute("CREATE DATABASE shopsphere_test;")
    cur.close()
    admin.close()

    app_module.DATABASE_URL = TEST_DATABASE_URL
    with app.app_context():
        init_db()          # same schema the service creates at startup
    yield

    admin = psycopg2.connect(dbname='postgres', user='shop', password='shoppass', host='localhost')
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute("DROP DATABASE IF EXISTS shopsphere_test;")
    cur.close()
    admin.close()


@pytest.fixture()
def client(test_db):
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_healthz(client):
    assert client.get('/healthz').status_code == 200


def test_signup_validation(client):
    assert client.post('/signup', json={"username": "ab", "password": "longenough"}).status_code == 400
    assert client.post('/signup', json={"username": "valid", "password": "short"}).status_code == 400
    assert client.post('/signup', json={}).status_code == 400


def test_signup_and_login(client):
    creds = {"username": "testuser", "password": "testpass123"}
    assert client.post('/signup', json=creds).status_code == 201
    assert client.post('/signup', json=creds).status_code == 409

    rv = client.post('/login', json=creds)
    assert rv.status_code == 200
    assert 'token' in rv.get_json()

    rv = client.post('/login', json={"username": "testuser", "password": "wrongpass1"})
    assert rv.status_code == 401
