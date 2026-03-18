/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BACKEND_URL || 'http://localhost:5000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
