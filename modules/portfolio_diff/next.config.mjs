/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: "/_next/wo_portfolio_diff/portfolio_diff",
  eslint: {
    ignoreDuringBuilds: true,
  },
  transpilePackages: ["lo_event", "lo_dash_react_components"],
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
