import os
import time
import json
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-service:6379/0")

def get_redis():
    """Connect to Redis with retries and keep‑alive."""
    for attempt in range(5):
        try:
            r = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_keepalive=True)
            r.ping()
            return r
        except (redis.ConnectionError, redis.TimeoutError):
            time.sleep(2 ** attempt)
    raise RuntimeError("Could not connect to Redis after 5 attempts")

def handle_payment_event(message):
    """Process a single payment event."""
    data = json.loads(message['data'])
    order_id = data.get('order_id', 'unknown')
    status = data.get('status', 'unknown')
    txn_id = data.get('transaction_id') or 'N/A'
    msg = data.get('message', '')

    if status == 'paid':
        print(f"✅ [NOTIFICATION] Order {order_id} PAID (txn: {txn_id}). Sending confirmation to user.")
        # TODO: Integrate email/SMS provider here
    else:
        print(f"❌ [NOTIFICATION] Order {order_id} FAILED. Reason: {msg}")

def main():
    print("Notification service started.")
    while True:
        try:
            r = get_redis()
            pubsub = r.pubsub()
            # Subscribe to both payment channels
            pubsub.subscribe("payment.completed", "payment.failed")
            print("Subscribed to payment.completed and payment.failed. Waiting for events...")

            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        handle_payment_event(message)
                    except Exception as e:
                        print(f"Error handling message: {e}")
        except (redis.TimeoutError, redis.ConnectionError, Exception) as e:
            print(f"Redis connection lost or error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    main()