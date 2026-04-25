import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite config -- React + TypeScript SPA.
// Dev server: http://localhost:3000 (matches what was exposed under CRA so
// the Kubernetes manifest and start_all.py wiring stay unchanged).
// Build output: dist/ -- consumed by the multi-stage Dockerfile + nginx.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    watch: {
      // Polling makes file watching reliable inside Docker volumes on
      // Windows/macOS hosts where inotify events don't propagate.
      usePolling: true,
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1500,
  },
});
