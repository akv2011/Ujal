import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': { // Forward requests starting with /chat to the backend
        target: 'http://localhost:4000', // Your backend address
        changeOrigin: true,
        secure: false,
      },
    },
  },
});