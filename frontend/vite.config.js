import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
    globals: true,
    // Playwright's browser tests live in e2e/ and run with `npm run e2e`.
    exclude: ['**/node_modules/**', 'e2e/**'],
  },
});
