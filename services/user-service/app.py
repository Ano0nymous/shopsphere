import os
import sys
import time
import datetime

import jwt
import psycopg2
from flask import Flask, request, jsonify, g
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'User Service', version='1.1')

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://shop:shoppass@localhost:5432/shopsphere")
# No insecure default: the service refuses to start without a real secret.
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_TTL_HOURS = int(os.environ.get("JWT_TTL_HOURS", "1"))


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
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()


@app.route('/healthz')
def healthz():
    get_db()
    return jsonify({"status": "healthy"}), 200


def _credentials(data):
    """Return (username, password, error_response)."""
    if not data or not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
        return None, None, (jsonify({"error": "username and password (strings) are required"}), 400)
    username = data['username'].strip()
    password = data['password']
    if not (3 <= len(username) <= 100):
        return None, None, (jsonify({"error": "username must be 3-100 characters"}), 400)
    if len(password) < 8:
        return None, None, (jsonify({"error": "password must be at least 8 characters"}), 400)
    return username, password, None


@app.route('/signup', methods=['POST'])
def signup():
    username, password, err = _credentials(request.get_json(silent=True))
    if err:
        return err
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s);",
                    (username, generate_password_hash(password)))
        conn.commit()
        return jsonify({"message": "User created"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"error": "Username already exists"}), 409
    finally:
        cur.close()


@app.route('/login', methods=['POST'])
def login():
    username, password, err = _credentials(request.get_json(silent=True))
    if err:
        return err
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    if not user or not check_password_hash(user[1], password):
        return jsonify({"error": "Invalid credentials"}), 401
    now = datetime.datetime.now(datetime.timezone.utc)
    token = jwt.encode({
        'user_id': user[0],
        'username': username,
        'iat': now,
        'exp': now + datetime.timedelta(hours=JWT_TTL_HOURS),
    }, JWT_SECRET, algorithm='HS256')
    return jsonify({"token": token})


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
    app.run(host='0.0.0.0', port=5001)
