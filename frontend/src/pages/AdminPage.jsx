import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { addProduct } from '../store/slices/productSlice';
import { showNotification } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  TextInput,
  NumberInput,
  Button,
  Alert,
  Stack,
} from '@mantine/core';
import { IconCheck, IconArrowLeft } from '@tabler/icons-react';

function AdminPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { token } = useSelector((state) => state.auth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!name || !price) {
      setError('Name and price are required.');
      return;
    }
    setLoading(true);
    try {
      await dispatch(addProduct({ name, price: parseFloat(price) })).unwrap();
      showNotification({
        title: 'Product added',
        message: `${name} has been added to the store.`,
        color: 'green',
        icon: <IconCheck size={16} />,
      });
      setName('');
      setPrice('');
    } catch (err) {
      setError(err.message || 'Failed to add product');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Container size="xs" my={80}>
        <Alert color="red">You must be logged in to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container size="xs" my={80}>
      <Button
        variant="subtle"
        leftSection={<IconArrowLeft size={16} />}
        onClick={() => navigate('/')}
        mb="lg"
      >
        Back to store
      </Button>

      <Paper
        p="xl"
        radius="lg"
        withBorder
        bg="dark.6"
      >
        <Title order={2} mb="lg" ta="center">
          Add New Product
        </Title>

        {error && (
          <Alert color="red" mb="md">
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Product Name"
              placeholder="e.g. Wireless Headphones"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              size="md"
            />
            <NumberInput
              label="Price"
              placeholder="9.99"
              value={price}
              onChange={(val) => setPrice(val)}
              required
              min={0}
              decimalScale={2}
              size="md"
              hideControls
            />
            <Button
              type="submit"
              fullWidth
              mt="md"
              size="md"
              loading={loading}
              variant="gradient"
              gradient={{ from: 'indigo', to: 'cyan' }}
            >
              Add Product
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}

export default AdminPage;