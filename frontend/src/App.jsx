import { Routes, Route } from 'react-router-dom';
import { Container, Box } from '@mantine/core';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import OrderConfirmationPage from './pages/OrderConfirmationPage';
import OrderHistoryPage from './pages/OrderHistoryPage';
import AdminPage from './pages/AdminPage';

function App() {
  return (
    <Box bg="dark.7" mih="100vh" style={{ display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <Container size="xl" py="xl" style={{ paddingTop: 90, flex: 1, width: '100%' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/product/:id" element={<ProductDetailPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/orders" element={<OrderHistoryPage />} />
          <Route path="/order-confirmation" element={<OrderConfirmationPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </Container>
      <Footer />
    </Box>
  );
}

export default App;
