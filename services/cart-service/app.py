import os
import time

import jwt
import redis
from flask import Flask, request, jsonify, g
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Cart Service', version='1.1')

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-service:6379/0")
JWT_SECRET = os.environ["JWT_SECRET"]


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


@app.route('/healthz')
def healthz():
    get_redis()
    return jsonify({"status": "healthy"}), 200


@app.route('/cart', methods=['GET', 'POST', 'DELETE'])
def handle_cart():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    r = get_redis()
    cart_key = f"cart:{user_id}"

    if request.method == 'GET':
        items = r.hgetall(cart_key)
        # Redis hash keys are strings; return the same types the frontend/product-service use.
        cart = [{"product_id": int(pid), "quantity": int(qty)} for pid, qty in items.items()]
        return jsonify(cart)

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        try:
            product_id = int(data['product_id'])
            quantity = int(data['quantity'])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "product_id and quantity (integers) required"}), 400
        if product_id <= 0 or quantity <= 0:
            return jsonify({"error": "product_id and quantity must be positive"}), 400
        r.hset(cart_key, product_id, quantity)
        return jsonify({"message": "Item added to cart", "product_id": product_id, "quantity": quantity}), 200

    if request.method == 'DELETE':
        data = request.get_json(silent=True) or {}
        product_id = data.get('product_id')
        if product_id is not None:
            r.hdel(cart_key, str(int(product_id)))
            return jsonify({"message": "Item removed"}), 200
        r.delete(cart_key)
        return jsonify({"message": "Cart cleared"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
