import os
import time
import json

import redis
import requests
import stripe

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis-service:6379/0")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:80").rstrip('/')
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
INTERNAL_API_TOKEN = os.environ["INTERNAL_API_TOKEN"]
PAYMENT_RETURN_URL = os.environ.get("PAYMENT_RETURN_URL", "http://localhost:8080/order-confirmation")
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "5"))
INTERNAL_HEADERS = {"X-Internal-Token": INTERNAL_API_TOKEN}

stripe.api_key = STRIPE_SECRET_KEY


def get_redis():
    for attempt in range(5):
        try:
            r = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_keepalive=True)
            r.ping()
            return r
        except redis.ConnectionError:
            time.sleep(2 ** attempt)
    raise RuntimeError("Could not connect to Redis after 5 attempts")


def process_order(order):
    order_id = order['order_id']
    payment_method_id = order.get('payment_method_id')
    amount = order.get('amount')
    currency = order.get('currency', 'inr')

    if not payment_method_id:
        finish(order_id, "failed", "Missing payment method")
        return
    if not isinstance(amount, int) or amount <= 0:
        finish(order_id, "failed", "Invalid order amount")
        return

    print(f"Processing Stripe payment for order {order_id}: {amount} ({currency})")
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method=payment_method_id,
            confirm=True,
            return_url=PAYMENT_RETURN_URL,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            idempotency_key=f"order-{order_id}",   # safe to retry the same order
            metadata={"order_id": order_id, "user_id": order.get('user_id')},
        )
        if intent.status == 'succeeded':
            finish(order_id, "paid", "Payment succeeded", intent.id)
        else:
            finish(order_id, "failed", f"Payment not completed (status: {intent.status})", intent.id)
    except stripe.error.CardError as e:
        finish(order_id, "failed", f"Card declined: {e.user_message or e.code}")
    except stripe.error.StripeError as e:
        finish(order_id, "failed", f"Payment provider error: {e.user_message or str(e)}")


def finish(order_id, status, message, txn_id=None):
    print(f"Order {order_id}: {status} – {message}")
    update_order_status(order_id, status, txn_id)
    publish_event(order_id, status, message, txn_id)


def update_order_status(order_id, status, txn_id=None):
    body = {"status": status}
    if txn_id:
        body["transaction_id"] = txn_id
    for attempt in range(3):
        try:
            resp = requests.patch(f"{ORDER_SERVICE_URL}/orders/{order_id}/status",
                                  json=body, headers=INTERNAL_HEADERS, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200:
                return
            print(f"Failed to update order {order_id}: {resp.status_code} {resp.text[:200]}")
            if resp.status_code < 500:
                return
        except requests.RequestException as e:
            print(f"Error updating order {order_id} (attempt {attempt+1}): {e}")
        time.sleep(2 ** attempt)


def publish_event(order_id, status, message, txn_id=None):
    event = {"order_id": order_id, "status": status, "transaction_id": txn_id, "message": message}
    channel = "payment.completed" if status == "paid" else "payment.failed"
    get_redis().publish(channel, json.dumps(event))
    print(f"{channel} event published for order {order_id}")


def main():
    print("Payment service (Stripe) started. Listening for order.created events...")
    while True:
        try:
            pubsub = get_redis().pubsub()
            pubsub.subscribe("order.created")
            print("Subscribed to Redis channel 'order.created'")
            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue
                try:
                    order = json.loads(message['data'])
                    print(f"Received order {order['order_id']}")
                    process_order(order)
                except Exception as e:
                    print(f"Error processing message: {e}")
        except redis.exceptions.ConnectionError as e:
            print(f"Redis connection lost: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Reconnecting in 10 seconds...")
            time.sleep(10)


if __name__ == '__main__':
    main()
