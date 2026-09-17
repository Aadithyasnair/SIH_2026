import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || "http://backend:8000";

const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default config;

