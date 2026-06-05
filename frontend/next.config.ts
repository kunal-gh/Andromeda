import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // @ts-ignore: ESLint config might not be strictly typed in this Next version
  eslint: { ignoreDuringBuilds: true },
  // @ts-ignore: TS config might not be strictly typed in this Next version
  typescript: { ignoreBuildErrors: true }
};

export default nextConfig;
