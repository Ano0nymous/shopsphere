import os
import sys
import time
from functools import wraps

import jwt
import psycopg2
from flask import Flask, jsonify, request, g
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Product Service', version='1.1')

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere")
JWT_SECRET = os.environ["JWT_SECRET"]
# Shared secret for service-to-service calls (order-service -> stock updates).
INTERNAL_API_TOKEN = os.environ["INTERNAL_API_TOKEN"]


def get_db():
    if 'db' not in g:
        for attempt in range(3):
            try:
                g.db = psycopg2.connect(DATABASE_URL)
                break
            except psycopg2.OperationalError:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("Could not connect to database after 3 attempts")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
            stock INTEGER NOT NULL DEFAULT 10 CHECK (stock >= 0)
        );
    """)
    conn.commit()
    cur.close()


# ---------- auth helpers ----------

def require_user(f):
    """Any logged-in user. (Extend with an is_admin claim for real admin gating.)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        try:
            g.user = jwt.decode(auth.split(' ', 1)[1], JWT_SECRET, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return wrapper


def require_internal(f):
    """Only other ShopSphere services carrying the shared internal token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get('X-Internal-Token') != INTERNAL_API_TOKEN:
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper


def row_to_product(r):
    return {"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3]}


# ---------- routes ----------

@app.route('/healthz')
def healthz():
    get_db()
    return jsonify({"status": "healthy"}), 200


@app.route('/products', methods=['GET'])
def list_products():
    cur = get_db().cursor()
    cur.execute("SELECT id, name, price, stock FROM products ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    return jsonify([row_to_product(r) for r in rows])


@app.route('/products', methods=['POST'])
@require_user
def create_product():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock', 10)
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name is required"}), 400
    try:
        price = round(float(price), 2)
        stock = int(stock)
    except (TypeError, ValueError):
        return jsonify({"error": "price must be a number and stock an integer"}), 400
    if price < 0 or stock < 0:
        return jsonify({"error": "price and stock must be non-negative"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING id, name, price, stock;",
        (name.strip(), price, stock)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return jsonify(row_to_product(row)), 201


@app.route('/products/<int:product_id>')
def get_product(product_id):
    cur = get_db().cursor()
    cur.execute("SELECT id, name, price, stock FROM products WHERE id = %s;", (product_id,))
    row = cur.fetchone()
    cur.close()
    if row:
        return jsonify(row_to_product(row))
    return jsonify({"error": "Product not found"}), 404


@app.route('/products/<int:product_id>/stock', methods=['PATCH'])
@require_internal
def update_stock(product_id):
    """Internal only. Body: {"quantity": n} deducts; {"quantity": n, "restore": true} adds back."""
    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get('quantity'))
    except (TypeError, ValueError):
        return jsonify({"error": "quantity (integer) is required"}), 400
    if quantity <= 0:
        return jsonify({"error": "quantity must be positive"}), 400
    delta = quantity if data.get('restore') else -quantity

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT stock FROM products WHERE id = %s FOR UPDATE;", (product_id,))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return jsonify({"error": "Product not found"}), 404
        if row[0] + delta < 0:
            conn.rollback()
            return jsonify({"error": "Insufficient stock", "available": row[0]}), 409
        cur.execute("UPDATE products SET stock = stock + %s WHERE id = %s RETURNING stock;",
                    (delta, product_id))
        remaining = cur.fetchone()[0]
        conn.commit()
    finally:
        cur.close()
    return jsonify({"message": "Stock updated", "remaining": remaining})


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
    app.run(host='0.0.0.0', port=5000)
