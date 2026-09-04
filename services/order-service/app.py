import os
import sys
import time
import json
from decimal import Decimal

import jwt
import psycopg2
import psycopg2.extras
import redis
import requests
from flask import Flask, request, jsonify, g
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Order Service', version='1.1')

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-service:6379/0")
PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://product-service:80").rstrip('/')
JWT_SECRET = os.environ["JWT_SECRET"]
INTERNAL_API_TOKEN = os.environ["INTERNAL_API_TOKEN"]
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "5"))
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_API_TOKEN}
VALID_STATUSES = {"pending", "paid", "failed", "cancelled"}


# ---------- connections ----------

def get_db():
    if 'db' not in g:
        for attempt in range(5):
            try:
                g.db = psycopg2.connect(DATABASE_URL)
                break
            except psycopg2.OperationalError:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("Could not connect to database after 5 attempts")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_redis():
    if 'redis' not in g:
        for attempt in range(5):
            try:
                g.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
                g.redis.ping()
                break
            except redis.ConnectionError:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("Could not connect to Redis after 5 attempts")
    return g.redis


@app.teardown_appcontext
def close_redis(exception):
    r = g.pop('redis', None)
    if r is not None:
        r.close()


def get_user_id():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth_header.split(' ', 1)[1], JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except (jwt.InvalidTokenError, KeyError):
        return None


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            total_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
            transaction_id VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_amount NUMERIC(10,2) NOT NULL DEFAULT 0;")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(255);")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(10,2) NOT NULL DEFAULT 0
        );
    """)
    cur.execute("ALTER TABLE order_items ADD COLUMN IF NOT EXISTS unit_price NUMERIC(10,2) NOT NULL DEFAULT 0;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);")
    conn.commit()
    cur.close()


# ---------- product-service helpers ----------

def fetch_product(product_id):
    resp = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=HTTP_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def adjust_stock(product_id, quantity, restore=False):
    """Returns (ok, error_message)."""
    body = {"quantity": quantity}
    if restore:
        body["restore"] = True
    resp = requests.patch(f"{PRODUCT_SERVICE_URL}/products/{product_id}/stock",
                          json=body, headers=INTERNAL_HEADERS, timeout=HTTP_TIMEOUT)
    if resp.status_code == 200:
        return True, None
    try:
        msg = resp.json().get('error', resp.text)
    except ValueError:
        msg = resp.text[:200]
    return False, msg


def validate_items(raw_items):
    """Normalise and validate the items payload -> list of {product_id, quantity} or (None, error)."""
    if not isinstance(raw_items, list) or not raw_items:
        return None, "items must be a non-empty list"
    merged = {}
    for it in raw_items:
        try:
            pid = int(it['product_id'])
            qty = int(it['quantity'])
        except (KeyError, TypeError, ValueError):
            return None, "each item needs integer product_id and quantity"
        if pid <= 0 or qty <= 0:
            return None, "product_id and quantity must be positive"
        merged[pid] = merged.get(pid, 0) + qty
    return [{"product_id": p, "quantity": q} for p, q in merged.items()], None


# ---------- routes ----------

@app.route('/healthz')
def healthz():
    get_db()
    get_redis()
    return jsonify({"status": "healthy"}), 200


@app.route('/orders', methods=['GET'])
def list_orders():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    cur = get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT o.id, o.status, o.total_amount, o.transaction_id, o.created_at,
               COALESCE(json_agg(json_build_object(
                   'product_id', oi.product_id, 'quantity', oi.quantity, 'unit_price', oi.unit_price)
               ) FILTER (WHERE oi.id IS NOT NULL), '[]') AS items
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.user_id = %s
        GROUP BY o.id
        ORDER BY o.created_at DESC;
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    for r in rows:
        r['total_amount'] = float(r['total_amount'])
        r['created_at'] = r['created_at'].isoformat()
    return jsonify(rows)


@app.route('/orders', methods=['POST'])
def place_order():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    items, err = validate_items(data.get('items'))
    if err:
        return jsonify({"error": err}), 400
    payment_method_id = data.get('payment_method_id')
    if not isinstance(payment_method_id, str) or not payment_method_id:
        return jsonify({"error": "payment_method_id is required"}), 400

    # 1. Look up prices first (read-only) so we fail before touching stock.
    total = Decimal("0")
    try:
        for item in items:
            product = fetch_product(item['product_id'])
            if product is None:
                return jsonify({"error": f"Product {item['product_id']} not found"}), 400
            item['unit_price'] = Decimal(str(product['price']))
            total += item['unit_price'] * item['quantity']
    except requests.RequestException as e:
        app.logger.error("product-service unreachable: %s", e)
        return jsonify({"error": "Product service unavailable, try again"}), 503

    # 2. Reserve stock; roll back every successful reservation if any one fails.
    reserved = []
    try:
        for item in items:
            ok, msg = adjust_stock(item['product_id'], item['quantity'])
            if not ok:
                raise ValueError(f"Product {item['product_id']}: {msg}")
            reserved.append(item)
    except (ValueError, requests.RequestException) as e:
        for item in reserved:
            try:
                adjust_stock(item['product_id'], item['quantity'], restore=True)
            except requests.RequestException as re:
                app.logger.error("stock restore failed for product %s: %s", item['product_id'], re)
        status = 400 if isinstance(e, ValueError) else 503
        return jsonify({"error": str(e) if status == 400 else "Product service unavailable, try again"}), status

    # 3. Persist order + items atomically; release stock if the DB write fails.
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO orders (user_id, status, total_amount) VALUES (%s, 'pending', %s) RETURNING id;",
                    (user_id, total))
        order_id = cur.fetchone()[0]
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES %s;",
            [(order_id, it['product_id'], it['quantity'], it['unit_price']) for it in items]
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        app.logger.error("order insert failed: %s", e)
        for item in reserved:
            try:
                adjust_stock(item['product_id'], item['quantity'], restore=True)
            except requests.RequestException:
                pass
        return jsonify({"error": "Could not save order"}), 500
    finally:
        cur.close()

    # 4. Emit event for payment-service. Amount is in the smallest currency unit (paise).
    event = {
        "order_id": order_id,
        "user_id": user_id,
        "items": [{"product_id": it['product_id'], "quantity": it['quantity'], "unit_price": float(it['unit_price'])} for it in items],
        "amount": int(total * 100),
        "currency": "inr",
        "payment_method_id": payment_method_id,
    }
    try:
        get_redis().publish("order.created", json.dumps(event))
    except redis.RedisError as e:
        # Order is saved; payment will not run. Surface it rather than pretend success.
        app.logger.error("failed to publish order.created for order %s: %s", order_id, e)
        return jsonify({"message": "Order saved but payment could not be started", "order_id": order_id,
                        "total_amount": float(total), "status": "pending"}), 202

    return jsonify({"message": "Order placed", "order_id": order_id,
                    "total_amount": float(total), "status": "pending"}), 201


@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    """Internal: called by payment-service. Never exposed through the public ingress."""
    if request.headers.get('X-Internal-Token') != INTERNAL_API_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = %s, transaction_id = COALESCE(%s, transaction_id) WHERE id = %s;",
                (new_status, data.get('transaction_id'), order_id))
    updated = cur.rowcount
    conn.commit()
    cur.close()
    if updated == 0:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"message": f"Order {order_id} status updated to {new_status}"})


def wait_for_db_and_init():
    for i in range(30):
        try:
            psycopg2.connect(DATABASE_URL).close()
            print("Database connection successful")
            break
        except Exception as e:
            print(f"Waiting for database... ({i+1}/30) error: {e}")
            time.sleep(1)
    else:
        print("Could not connect to database after 30 seconds")
        sys.exit(1)

    with app.app_context():
        for attempt in range(5):
            try:
                init_db()
                print("Database schema initialised")
                return
            except Exception as e:
                print(f"init_db attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
    print("Could not initialise database after 5 attempts")
    sys.exit(1)


if __name__ == '__main__':
    wait_for_db_and_init()
    app.run(host='0.0.0.0', port=5003)
