/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The frontend talks to the Python core exclusively over HTTP - never to the
// filesystem or DuckDB directly (DEC-001). In dev, /api is proxied to the
// FastAPI server; in the future Tauri host the same bundle is unchanged.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Vite's default port (5173) collides with another dev server on this
  // machine, so the frontend dev server is pinned here. strictPort matters:
  // without it Vite silently hops to the next free port and the Tauri shell's
  // devUrl is left pointing at a dead port - which is exactly how the shell
  // ended up showing an empty window. Override with DAH_DEV_PORT=... if needed.
  server: {
    port: Number(process.env.DAH_DEV_PORT ?? 5273),
    strictPort: true,
    proxy: {
      '/api': {
        // The core's default port is the one the Tauri shell's sidecar binds;
        // DAH_CORE_PORT lets a second, isolated core answer instead - a
        // visual check against seeded data, without touching the case store
        // the running app owns.
        target: `http://127.0.0.1:${Number(process.env.DAH_CORE_PORT ?? 8123)}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setup-tests.ts'],
    // The accessibility audit reads the stylesheet the product ships from the
    // DOM, the way a browser reads it - so the focus rule it checks for is the
    // one the build actually emits, not a claim about a file. CSS is inert in
    // every other test (no component imports a stylesheet), so turning it on
    // costs nothing but makes that one audit honest.
    css: true,
    // Each test file finishes in well under a second on its own, but running
    // the files in parallel starves the jsdom environments of CPU on a loaded
    // machine and the same tests then blow the 5s timeout without ever
    // touching it - a red suite that says nothing about the code. Serialising
    // the files costs no wall-clock time and makes the gate deterministic.
    fileParallelism: false,
  },
})
