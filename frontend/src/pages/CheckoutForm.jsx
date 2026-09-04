import { useState } from 'react';
import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Button, Alert, Group, Paper, Text } from '@mantine/core';

const cardStyle = {
  style: {
    base: { fontSize: '16px', color: '#ffffff', '::placeholder': { color: '#aab7c4' } },
    invalid: { color: '#fa755a' },
  },
};

/** Collects card details and hands a Stripe PaymentMethod id to the parent. */
function CheckoutForm({ onPaymentMethodReady, total, loading }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!stripe || !elements) return;
    setProcessing(true);
    setError('');
    const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
      type: 'card',
      card: elements.getElement(CardElement),
    });
    setProcessing(false);
    if (stripeError) {
      setError(stripeError.message);
      return;
    }
    await onPaymentMethodReady(paymentMethod.id);
  };

  if (!stripe) {
    return (
      <Alert color="yellow" mt="lg">
        Payments are not configured (missing VITE_STRIPE_PUBLISHABLE_KEY).
      </Alert>
    );
  }

  return (
    <Paper p="lg" radius="lg" mt="lg" withBorder bg="dark.6">
      <Text fw={500} mb="md">Card details</Text>
      <form onSubmit={handleSubmit}>
        <CardElement options={cardStyle} />
        {error && <Alert color="red" mt="sm">{error}</Alert>}
        <Group justify="flex-end" mt="md">
          <Button type="submit" loading={processing || loading} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
            Pay ${total.toFixed(2)}
          </Button>
        </Group>
      </form>
    </Paper>
  );
}

export default CheckoutForm;
