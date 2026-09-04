import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// All backend calls go through /api/* (same prefix the k8s ingress uses),
// so SPA routes like /cart and /login never collide with backend routes.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080', // kind/minikube ingress port-forward
        changeOrigin: true,
      },
    },
  },
});
