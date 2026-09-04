import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { signup } from '../store/slices/authSlice';
import { useNavigate } from 'react-router-dom';
import {
  TextInput,
  PasswordInput,
  Button,
  Paper,
  Title,
  Alert,
  Container,
  Text,
} from '@mantine/core';
import { IconCheck, IconAlertCircle } from '@tabler/icons-react';

function SignupPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    dispatch(signup({ username, password })).then((res) => {
      if (res.type === 'auth/signup/fulfilled') {
        setMessage('User created! Redirecting to login...');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(res.error.message || 'Signup failed');
      }
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
          Create an account
        </Title>

        {message && (
          <Alert icon={<IconCheck size={16} />} color="green" mb="md">
            {message}
          </Alert>
        )}
        {error && (
          <Alert icon={<IconAlertCircle size={16} />} color="red" mb="md">
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextInput
            label="Username"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            size="md"
          />
          <PasswordInput
            label="Password"
            placeholder="Create a password"
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
            variant="gradient"
            gradient={{ from: 'indigo', to: 'cyan' }}
          >
            Sign Up
          </Button>
        </form>

        <Text ta="center" mt="md" size="sm" c="dimmed">
          Already have an account?{' '}
          <Text
            component="span"
            c="indigo"
            style={{ cursor: 'pointer' }}
            onClick={() => navigate('/login')}
          >
            Log in
          </Text>
        </Text>
      </Paper>
    </Container>
  );
}

export default SignupPage;