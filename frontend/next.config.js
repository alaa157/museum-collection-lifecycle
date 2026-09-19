/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    const gateway = process.env.API_GATEWAY_URL || "http://127.0.0.1:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${gateway}/api/:path*`
      }
    ];
  }
};

module.exports = nextConfig;
