import { useLocation, useNavigate } from 'react-router-dom';
import { Title, Alert, Button, Text, Paper, Center, Group } from '@mantine/core';
import { IconCircleCheck } from '@tabler/icons-react';

function OrderConfirmationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const order = location.state;

  return (
    <Center style={{ minHeight: '60vh' }}>
      <Paper shadow="lg" p="xl" radius="lg" withBorder maw={500} w="100%">
        {order ? (
          <>
            <Center><IconCircleCheck size={64} color="green" /></Center>
            <Title ta="center" order={1} mt="md">Order Placed!</Title>
            <Text ta="center" c="dimmed" mt="sm">
              Order <strong>#{order.order_id}</strong> for ${Number(order.total_amount).toFixed(2)} has been placed.
            </Text>
            <Text ta="center" mt="xs">
              Payment is being processed — check your order history for the final status.
            </Text>
            <Group justify="center" mt="xl">
              <Button onClick={() => navigate('/orders')} variant="outline">View orders</Button>
              <Button onClick={() => navigate('/')} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
                Continue Shopping
              </Button>
            </Group>
          </>
        ) : (
          <Alert color="yellow">No order details found.</Alert>
        )}
      </Paper>
    </Center>
  );
}

export default OrderConfirmationPage;
