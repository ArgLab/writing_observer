/** @type {import('next').NextConfig} */
const basePath = "/_next/wo_portfolio_diff/portfolio_diff";

const nextConfig = {
  basePath,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  transpilePackages: ["lo_event"],
  webpack: (
    config,
    { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }
  ) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false, // tells Webpack to ignore fs in client bundle
    };
    return config;
  },
  output: "export",
};

export default nextConfig;
