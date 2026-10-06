import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 브라우저 → /api/... (5173) → Vite 서버가 백엔드(8000)로 대신 전달
    // 브라우저는 5173만 알면 되므로 WSL/원격 환경 포트 문제와 CORS가 사라진다.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
