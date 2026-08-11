import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  // @ts-ignore
  allowedDevOrigins: ['192.168.1.209'],
};

export default nextConfig;
