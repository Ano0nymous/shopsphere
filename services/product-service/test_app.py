import os

import jwt
import psycopg2
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import app as app_module  # noqa: E402
from app import app, init_db  # noqa: E402

USER_HEADERS = {"Authorization": "Bearer " + jwt.encode({"user_id": 1, "username": "t"}, "test-secret", algorithm="HS256")}
INTERNAL_HEADERS = {"X-Internal-Token": "test-internal"}


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
        init_db()
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


def test_create_requires_auth(client):
    assert client.post('/products', json={"name": "X", "price": 1}).status_code == 401


def test_create_and_get_products(client):
    assert client.get('/products').get_json() == []

    rv = client.post('/products', json={"name": "Test Widget", "price": 9.99, "stock": 5}, headers=USER_HEADERS)
    assert rv.status_code == 201
    body = rv.get_json()
    assert body == {"id": 1, "name": "Test Widget", "price": 9.99, "stock": 5}

    assert len(client.get('/products').get_json()) == 1
    rv = client.get('/products/1')
    assert rv.status_code == 200
    assert rv.get_json()['name'] == "Test Widget"


def test_stock_deduct_and_restore(client):
    # not internal -> forbidden
    assert client.patch('/products/1/stock', json={"quantity": 1}).status_code == 403

    rv = client.patch('/products/1/stock', json={"quantity": 3}, headers=INTERNAL_HEADERS)
    assert rv.status_code == 200 and rv.get_json()['remaining'] == 2

    rv = client.patch('/products/1/stock', json={"quantity": 3}, headers=INTERNAL_HEADERS)
    assert rv.status_code == 409  # insufficient

    rv = client.patch('/products/1/stock', json={"quantity": 3, "restore": True}, headers=INTERNAL_HEADERS)
    assert rv.status_code == 200 and rv.get_json()['remaining'] == 5


def test_404(client):
    assert client.get('/products/999').status_code == 404
