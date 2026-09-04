import { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { showNotification } from '@mantine/notifications';
import {
  Container, Title, Text, Grid, Card, Image, Badge, Button, Skeleton, Group, Box,
} from '@mantine/core';
import { IconShoppingCartPlus, IconCheck } from '@tabler/icons-react';
import { fetchProducts } from '../store/slices/productSlice';
import { addToCart } from '../store/slices/cartSlice';

function HomePage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items, status } = useSelector((state) => state.products);
  const { token } = useSelector((state) => state.auth);

  useEffect(() => {
    if (status === 'idle') dispatch(fetchProducts());
  }, [status, dispatch]);

  const handleAddToCart = async (productId, productName) => {
    const res = await dispatch(addToCart({ product_id: productId, quantity: 1 }));
    if (addToCart.fulfilled.match(res)) {
      showNotification({ title: 'Added to cart', message: `${productName} added!`, color: 'green', icon: <IconCheck size={16} /> });
    } else {
      showNotification({ title: 'Could not add to cart', message: res.error.message, color: 'red' });
    }
  };

  return (
    <Container size="xl" py="xl">
      <Box
        p="4rem 2rem" mb="3rem" ta="center"
        style={{
          background: 'linear-gradient(135deg, var(--mantine-color-dark-7) 0%, var(--mantine-color-dark-9) 100%)',
          borderRadius: 'var(--mantine-radius-lg)',
          border: '1px solid var(--mantine-color-dark-4)',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
        }}
      >
        <Title order={1} fz="3.5rem" fw={900} style={{ letterSpacing: '-2px' }}>
          <Text component="span" inherit variant="gradient" gradient={{ from: 'indigo', to: 'cyan', deg: 45 }}>
            Discover Premium Products
          </Text>
        </Title>
        <Text size="xl" mt="md" c="dimmed" maw={600} mx="auto">
          Curated for excellence. Free shipping on orders over $50.
        </Text>
      </Box>

      {status === 'loading' && (
        <Grid>
          {Array(6).fill().map((_, i) => (
            <Grid.Col span={{ base: 12, sm: 6, md: 4 }} key={i}><Skeleton height={350} radius="lg" /></Grid.Col>
          ))}
        </Grid>
      )}

      {status === 'succeeded' && items.length === 0 && (
        <Text c="dimmed" ta="center">No products yet — add some from the admin page.</Text>
      )}

      {status === 'succeeded' && (
        <Grid>
          {items.map((product) => (
            <Grid.Col span={{ base: 12, sm: 6, md: 4 }} key={product.id}>
              <Card shadow="xl" p="lg" radius="lg" withBorder bg="dark.6">
                <Card.Section>
                  <Image src={`https://picsum.photos/seed/${product.id}/400/300`} h={200} alt={product.name} fit="cover" />
                </Card.Section>
                <Group justify="space-between" mt="md" mb="xs">
                  <Text fw={600} size="lg">{product.name}</Text>
                  <Badge color="pink" variant="light" size="lg">${Number(product.price).toFixed(2)}</Badge>
                </Group>
                <Text size="sm" c="dimmed" mb="md">
                  {product.stock > 0 ? `In stock: ${product.stock}` : 'Out of stock'}
                </Text>
                {token && (
                  <Button fullWidth leftSection={<IconShoppingCartPlus size={18} />}
                    onClick={() => handleAddToCart(product.id, product.name)}
                    disabled={product.stock <= 0} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
                    Add to Cart
                  </Button>
                )}
                <Button fullWidth mt="xs" variant="outline" onClick={() => navigate(`/product/${product.id}`)}>
                  View Details
                </Button>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      )}

      {status === 'failed' && <Text c="red" ta="center">Failed to load products.</Text>}
    </Container>
  );
}

export default HomePage;
