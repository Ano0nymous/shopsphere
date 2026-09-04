import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { login } from '../store/slices/authSlice';
import { useNavigate } from 'react-router-dom';
import { TextInput, PasswordInput, Button, Paper, Title, Alert, Container } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { status, error } = useSelector((state) => state.auth);

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(login({ username, password })).then((res) => {
      if (res.type === 'auth/login/fulfilled') navigate('/');
    });
  };

  return (
    <Container size={420} my={80}>
      <Paper
        p="xl"
        radius="lg"
        withBorder
        bg="dark.6"
      >
        <Title order={2} ta="center" mb="lg">
          Welcome back
        </Title>
        {error && (
          <Alert icon={<IconAlertCircle size={16} />} color="red" mb="md">
            {error}
          </Alert>
        )}
        <form onSubmit={handleSubmit}>
          <TextInput
            label="Username"
            placeholder="Your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            size="md"
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            mt="md"
            size="md"
          />
          <Button
            type="submit"
            fullWidth
            mt="xl"
            size="md"
            loading={status === 'loading'}
            variant="gradient"
            gradient={{ from: 'indigo', to: 'cyan' }}
          >
            {status === 'loading' ? 'Logging in...' : 'Login'}
          </Button>
        </form>
      </Paper>
    </Container>
  );
}

export default LoginPage;