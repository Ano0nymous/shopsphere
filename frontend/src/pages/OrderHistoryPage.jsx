import { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Container, Title, Table, Alert, Loader, Center, Badge, Text } from '@mantine/core';
import { fetchOrders } from '../store/slices/orderSlice';

const statusColor = { paid: 'green', pending: 'yellow', failed: 'red', cancelled: 'gray' };

function OrderHistoryPage() {
  const dispatch = useDispatch();
  const { orderHistory, historyStatus, error } = useSelector((state) => state.orders);
  const { token } = useSelector((state) => state.auth);

  useEffect(() => {
    if (token) dispatch(fetchOrders());
  }, [dispatch, token]);

  if (!token) return <Container><Alert color="red">Please log in to view your orders.</Alert></Container>;
  if (historyStatus === 'loading') return <Center><Loader /></Center>;
  if (historyStatus === 'failed') return <Container><Alert color="red">Error loading orders: {error}</Alert></Container>;

  return (
    <Container size="lg" py="xl">
      <Title order={2} mb="lg">Order History</Title>
      {orderHistory.length === 0 ? (
        <Alert color="gray">You haven't placed any orders yet.</Alert>
      ) : (
        <Table verticalSpacing="sm" highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Order</Table.Th>
              <Table.Th>Date</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Total</Table.Th>
              <Table.Th>Items</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {orderHistory.map((order) => (
              <Table.Tr key={order.id}>
                <Table.Td>#{order.id}</Table.Td>
                <Table.Td>{new Date(order.created_at).toLocaleString()}</Table.Td>
                <Table.Td><Badge color={statusColor[order.status] || 'gray'}>{order.status}</Badge></Table.Td>
                <Table.Td>${Number(order.total_amount).toFixed(2)}</Table.Td>
                <Table.Td>
                  {order.items.map((item) => (
                    <Text key={item.product_id} size="sm">
                      Product #{item.product_id} × {item.quantity} @ ${Number(item.unit_price).toFixed(2)}
                    </Text>
                  ))}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Container>
  );
}

export default OrderHistoryPage;
