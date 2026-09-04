"""order-service tests. Needs Postgres + Redis on localhost (CI provides both).
product-service is faked in-memory so the stock reservation / rollback logic is exercised."""
import os

import jwt
import psycopg2
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import app as app_module  # noqa: E402
from app import app, init_db  # noqa: E402

AUTH = {"Authorization": "Bearer " + jwt.encode({"user_id": 42, "username": "t"}, "test-secret", algorithm="HS256")}


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code, self._body, self.text = status_code, body, str(body)

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(self.status_code)


class FakeProductService:
    """Minimal stand-in for product-service: /products/<id> and /products/<id>/stock."""
    def __init__(self):
        self.products = {1: {"id": 1, "name": "A", "price": 10.5, "stock": 5},
                         2: {"id": 2, "name": "B", "price": 2.0, "stock": 1}}

    def get(self, url, timeout=None):
        pid = int(url.rstrip('/').split('/')[-1])
        p = self.products.get(pid)
        return FakeResponse(200, p) if p else FakeResponse(404, {"error": "Product not found"})

    def patch(self, url, json=None, headers=None, timeout=None):
        assert headers == {"X-Internal-Token": "test-internal"}
        pid = int(url.split('/')[-2])
        p = self.products[pid]
        delta = json['quantity'] if json.get('restore') else -json['quantity']
        if p['stock'] + delta < 0:
            return FakeResponse(409, {"error": "Insufficient stock"})
        p['stock'] += delta
        return FakeResponse(200, {"remaining": p['stock']})


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
def fake_products(monkeypatch):
    fake = FakeProductService()
    monkeypatch.setattr(app_module.requests, "get", fake.get)
    monkeypatch.setattr(app_module.requests, "patch", fake.patch)
    return fake


@pytest.fixture()
def client(test_db, fake_products):
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_requires_auth(client):
    assert client.post('/orders', json={"items": []}).status_code == 401
    assert client.get('/orders').status_code == 401


def test_validation(client):
    assert client.post('/orders', json={"items": [], "payment_method_id": "pm_x"}, headers=AUTH).status_code == 400
    assert client.post('/orders', json={"items": [{"product_id": 1, "quantity": 1}]}, headers=AUTH).status_code == 400


def test_place_order_and_history(client, fake_products):
    rv = client.post('/orders', json={
        "items": [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}],
        "payment_method_id": "pm_test"}, headers=AUTH)
    assert rv.status_code == 201, rv.get_json()
    body = rv.get_json()
    assert body['total_amount'] == 23.0
    assert fake_products.products[1]['stock'] == 3
    assert fake_products.products[2]['stock'] == 0

    rv = client.get('/orders', headers=AUTH)
    orders = rv.get_json()
    assert len(orders) == 1 and orders[0]['status'] == 'pending'
    assert sorted(i['product_id'] for i in orders[0]['items']) == [1, 2]


def test_insufficient_stock_rolls_back_reservations(client, fake_products):
    before = fake_products.products[1]['stock']
    rv = client.post('/orders', json={
        "items": [{"product_id": 1, "quantity": 1}, {"product_id": 2, "quantity": 99}],
        "payment_method_id": "pm_test"}, headers=AUTH)
    assert rv.status_code == 400
    assert "Insufficient stock" in rv.get_json()['error']
    assert fake_products.products[1]['stock'] == before   # product 1 reservation was released


def test_status_update_is_internal_only(client):
    assert client.patch('/orders/1/status', json={"status": "paid"}).status_code == 403
    rv = client.patch('/orders/1/status', json={"status": "paid", "transaction_id": "pi_1"},
                      headers={"X-Internal-Token": "test-internal"})
    assert rv.status_code == 200
    rv = client.patch('/orders/1/status', json={"status": "bogus"}, headers={"X-Internal-Token": "test-internal"})
    assert rv.status_code == 400
    assert client.get('/orders', headers=AUTH).get_json()[0]['status'] == 'paid'
