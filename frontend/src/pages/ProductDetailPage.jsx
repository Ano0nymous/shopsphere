import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { showNotification } from '@mantine/notifications';
import { Container, Title, Text, Image, Badge, Button, Skeleton, Grid, Alert } from '@mantine/core';
import { IconShoppingCartPlus, IconCheck, IconArrowLeft } from '@tabler/icons-react';
import { addToCart } from '../store/slices/cartSlice';
import { fetchProducts } from '../store/slices/productSlice';

function ProductDetailPage() {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items, status } = useSelector((state) => state.products);
  const product = items.find((p) => p.id === Number(id));
  const { token } = useSelector((state) => state.auth);

  useEffect(() => {
    if (status === 'idle') dispatch(fetchProducts()); // direct link / hard refresh
  }, [status, dispatch]);

  if (!product) {
    return (
      <Container>
        {status === 'succeeded' ? <Alert color="yellow">Product not found.</Alert> : <Skeleton height={300} />}
      </Container>
    );
  }

  const handleAdd = async () => {
    const res = await dispatch(addToCart({ product_id: product.id, quantity: 1 }));
    if (addToCart.fulfilled.match(res)) {
      showNotification({ title: 'Added to cart', message: `${product.name} added successfully.`, color: 'green', icon: <IconCheck size={16} /> });
    }
  };

  return (
    <Container size="lg" py="xl">
      <Button variant="subtle" leftSection={<IconArrowLeft size={16} />} onClick={() => navigate('/')} mb="lg">
        Back to products
      </Button>
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Image src={`https://picsum.photos/seed/${product.id}/600/400`} radius="md" alt={product.name} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Title order={1} fw={800}>{product.name}</Title>
          <Badge size="xl" color="pink" variant="light" mt="sm">${Number(product.price).toFixed(2)}</Badge>
          <Text mt="xl" size="lg">{product.stock > 0 ? `In stock: ${product.stock}` : 'Out of stock'}</Text>
          <Text mt="md" c="dimmed">
            This is a premium quality product that you'll love. Made with the finest materials and designed for comfort and durability.
          </Text>
          {token && (
            <Button mt="xl" size="lg" leftSection={<IconShoppingCartPlus size={20} />} onClick={handleAdd}
              disabled={product.stock <= 0} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
              Add to Cart
            </Button>
          )}
        </Grid.Col>
      </Grid>
    </Container>
  );
}

export default ProductDetailPage;
