import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: {
      '/products': 'http://127.0.0.1:8000',
      '/plans': 'http://127.0.0.1:8000',
      '/payment-terms': 'http://127.0.0.1:8000',
      '/quotation-templates': 'http://127.0.0.1:8000',
      '/subscriptions': 'http://127.0.0.1:8000',
      '/me': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
