import { Container, Text, Group, Anchor, Divider } from '@mantine/core';

function Footer() {
  return (
    <footer style={{ marginTop: 'auto', paddingTop: '2rem' }}>
      <Divider />
      <Container size="xl" py="md">
        <Group justify="space-between">
          <Text size="sm" c="dimmed">© {new Date().getFullYear()} ShopSphere. All rights reserved.</Text>
          <Group gap="lg">
            <Anchor size="sm" href="#">Privacy Policy</Anchor>
            <Anchor size="sm" href="#">Terms of Service</Anchor>
            <Anchor size="sm" href="#">Contact</Anchor>
          </Group>
        </Group>
      </Container>
    </footer>
  );
}

export default Footer;
