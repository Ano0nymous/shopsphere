import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { showNotification } from '@mantine/notifications';
import {
  Container, Title, Table, Button, Group, Alert, Text, Image, Loader, Center, Divider, Paper,
} from '@mantine/core';
import { IconTrash, IconShoppingCart, IconArrowLeft } from '@tabler/icons-react';
import { fetchCart, removeFromCart, clearCart } from '../store/slices/cartSlice';
import { fetchProducts } from '../store/slices/productSlice';
import { placeOrder } from '../store/slices/orderSlice';
import CheckoutForm from './CheckoutForm';

function CartPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items, status: cartStatus } = useSelector((state) => state.cart);
  const { token } = useSelector((state) => state.auth);
  const { items: products, status: productStatus } = useSelector((state) => state.products);
  const { status: orderStatus, error: orderError } = useSelector((state) => state.orders);
  const [checkingOut, setCheckingOut] = useState(false);

  useEffect(() => {
    if (token) dispatch(fetchCart());
    if (productStatus === 'idle') dispatch(fetchProducts()); // prices needed even on a hard refresh
  }, [dispatch, token, productStatus]);

  const getProductById = (id) => products.find((p) => p.id === Number(id));

  const subtotal = items.reduce((sum, item) => {
    const prod = getProductById(item.product_id);
    return sum + (prod ? prod.price * item.quantity : 0);
  }, 0);

  const handleRemove = (productId) => {
    dispatch(removeFromCart(productId));
    showNotification({ title: 'Removed', message: 'Item removed from cart.', color: 'orange' });
  };

  const handleClear = () => {
    dispatch(clearCart());
    setCheckingOut(false);
    showNotification({ title: 'Cart cleared', message: 'All items removed.', color: 'orange' });
  };

  const handlePayment = async (paymentMethodId) => {
    const orderItems = items.map(({ product_id, quantity }) => ({ product_id, quantity }));
    const result = await dispatch(placeOrder({ items: orderItems, payment_method_id: paymentMethodId }));
    if (placeOrder.fulfilled.match(result)) {
      dispatch(clearCart());
      navigate('/order-confirmation', { state: result.payload });
    } else {
      showNotification({ title: 'Checkout failed', message: result.error.message, color: 'red' });
    }
  };

  if (!token) {
    return <Container><Alert color="red">Please log in to view your cart.</Alert></Container>;
  }

  if (cartStatus === 'loading' && items.length === 0) {
    return <Center><Loader /></Center>;
  }

  return (
    <Container size="lg" py="xl">
      <Group mb="lg">
        <Button variant="subtle" leftSection={<IconArrowLeft size={16} />} onClick={() => navigate('/')}>
          Continue Shopping
        </Button>
      </Group>
      <Title order={2} mb="lg">Your Cart</Title>

      {items.length === 0 ? (
        <Alert icon={<IconShoppingCart size={16} />} color="gray">
          Your cart is empty.
          <Button variant="subtle" onClick={() => navigate('/')} ml="sm">Start shopping</Button>
        </Alert>
      ) : (
        <Paper p="lg" radius="lg" withBorder bg="dark.6">
          <Table verticalSpacing="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Product</Table.Th>
                <Table.Th>Price</Table.Th>
                <Table.Th>Quantity</Table.Th>
                <Table.Th>Subtotal</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((item) => {
                const prod = getProductById(item.product_id);
                return (
                  <Table.Tr key={item.product_id}>
                    <Table.Td>
                      <Group>
                        <Image src={`https://picsum.photos/seed/${item.product_id}/50/50`} w={50} h={50} radius="sm" />
                        <Text fw={500}>{prod ? prod.name : `Product #${item.product_id}`}</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>{prod ? `$${Number(prod.price).toFixed(2)}` : 'N/A'}</Table.Td>
                    <Table.Td>{item.quantity}</Table.Td>
                    <Table.Td>{prod ? `$${(prod.price * item.quantity).toFixed(2)}` : 'N/A'}</Table.Td>
                    <Table.Td>
                      <Button color="red" variant="outline" size="xs" onClick={() => handleRemove(item.product_id)}>
                        <IconTrash size={14} />
                      </Button>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>

          <Divider my="lg" />
          <Group justify="space-between">
            <Text size="xl" fw={700}>Total: ${subtotal.toFixed(2)}</Text>
            <Group>
              <Button variant="outline" color="red" onClick={handleClear}>Clear Cart</Button>
              {!checkingOut && (
                <Button size="lg" onClick={() => setCheckingOut(true)} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
                  Proceed to Checkout
                </Button>
              )}
            </Group>
          </Group>

          {checkingOut && (
            <CheckoutForm total={subtotal} loading={orderStatus === 'loading'} onPaymentMethodReady={handlePayment} />
          )}
          {orderStatus === 'failed' && orderError && (
            <Alert color="red" mt="md">{orderError}</Alert>
          )}
        </Paper>
      )}
    </Container>
  );
}

export default CartPage;
