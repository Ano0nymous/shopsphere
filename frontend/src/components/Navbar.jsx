import { Link, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Group, Button, Text, ActionIcon, Indicator, Tooltip, Flex, useMantineColorScheme,
} from '@mantine/core';
import {
  IconShoppingCart, IconUser, IconLogout, IconSun, IconMoonStars, IconPlus, IconReceipt,
} from '@tabler/icons-react';
import { logout } from '../store/slices/authSlice';
import { resetCart } from '../store/slices/cartSlice';

function Navbar() {
  const { token, username } = useSelector((state) => state.auth);
  const cartItemsCount = useSelector((state) => state.cart.items.length);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const dark = colorScheme === 'dark';

  const handleLogout = () => {
    dispatch(logout());
    dispatch(resetCart());
    navigate('/');
  };

  return (
    <Flex
      justify="space-between"
      align="center"
      px="xl"
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 70, zIndex: 1000,
        backdropFilter: 'blur(12px)',
        backgroundColor: dark ? 'rgba(20, 20, 30, 0.8)' : 'rgba(255,255,255,0.8)',
        borderBottom: `1px solid ${dark ? 'var(--mantine-color-dark-4)' : 'var(--mantine-color-gray-2)'}`,
        boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Text component={Link} to="/" fw={900} size="xl" variant="gradient"
        gradient={{ from: 'indigo', to: 'cyan', deg: 45 }} style={{ letterSpacing: '-1px' }}>
        ShopSphere
      </Text>

      <Group gap="md">
        <Tooltip label={dark ? 'Light mode' : 'Dark mode'}>
          <ActionIcon onClick={toggleColorScheme} variant="subtle" size="lg">
            {dark ? <IconSun size={18} /> : <IconMoonStars size={18} />}
          </ActionIcon>
        </Tooltip>

        {token ? (
          <>
            <Tooltip label="Add new product">
              <ActionIcon component={Link} to="/admin" variant="light" color="gray" size="lg">
                <IconPlus size={20} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Order history">
              <ActionIcon component={Link} to="/orders" variant="light" color="gray" size="lg">
                <IconReceipt size={20} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="View cart">
              <Indicator label={cartItemsCount} size={16} disabled={cartItemsCount === 0} color="red">
                <ActionIcon component={Link} to="/cart" variant="light" color="gray" size="lg">
                  <IconShoppingCart size={20} />
                </ActionIcon>
              </Indicator>
            </Tooltip>
            <Group gap="xs">
              <IconUser size={16} />
              <Text size="sm" fw={500}>{username || 'User'}</Text>
            </Group>
            <Button variant="subtle" color="red" size="sm" onClick={handleLogout} leftSection={<IconLogout size={16} />}>
              Logout
            </Button>
          </>
        ) : (
          <>
            <Button component={Link} to="/login" variant="subtle" size="sm">Login</Button>
            <Button component={Link} to="/signup" variant="filled" size="sm">Sign Up</Button>
          </>
        )}
      </Group>
    </Flex>
  );
}

export default Navbar;
