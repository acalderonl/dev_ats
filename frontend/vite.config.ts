import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** A dónde manda Vite lo que no es del frontend. Dentro de compose el backend se
 *  llama `backend`; quien levante Vite a mano pone aquí localhost. */
const BACKEND = process.env.VITE_PROXY_TARGET ?? 'http://backend:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    watch: {
      usePolling: true,
    },
    proxy: {
      // La página con las etiquetas Open Graph la genera el backend, pero el enlace
      // que se reparte es el del frontend. En producción lo reenvía nginx; sin esto,
      // en desarrollo Vite devolvería el `index.html` vacío de la SPA y la tarjeta de
      // LinkedIn saldría en blanco justo donde se la quiere probar.
      '/compartir': { target: BACKEND, changeOrigin: false },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
})
