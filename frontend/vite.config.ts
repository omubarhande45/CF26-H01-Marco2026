import { defineConfig, type ProxyOptions } from "vite";
import react from "@vitejs/plugin-react";

const apiProxy: Record<string, ProxyOptions> = {
  "/api": {
    target: "http://127.0.0.1:8080",
    changeOrigin: true,
    secure: false,
    rewrite: (p) => p.replace(/^\/api/, ""),
    configure: (proxy) => {
      proxy.on("proxyReq", (proxyReq, req) => {
        const auth = req.headers.authorization;
        const custom = req.headers["x-fcqf-token"];
        if (auth) proxyReq.setHeader("Authorization", Array.isArray(auth) ? auth[0] : auth);
        if (custom) proxyReq.setHeader("X-FCQF-Token", Array.isArray(custom) ? custom[0] : custom);
        const cookie = req.headers.cookie;
        if (cookie) proxyReq.setHeader("Cookie", cookie);
      });
    },
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: apiProxy,
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: apiProxy,
  },
});
