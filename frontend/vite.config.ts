import { defineConfig } from "vite";

export default defineConfig({
  base: "/genomics/",
  server: {
    port: 5173,
    proxy: {
      "/api/genomics": {
        target: "http://localhost:8002",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
