/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (
    config,
    { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }
  ) => {
    // Important: return the modified config
    config.externals.unshift(
      {
        sqlite3: 'sqlite3',
        crypto: 'crypto',
        ws: 'ws',
        'indexeddb-js': 'indexeddb-js'
      });
    config.module.rules.push({
      test: /\.jsx?$/, // This regex matches both .js and .jsx files
      include: [/node_modules\/lo_event/], // Include only the lo_event module
      use: {
        loader: 'babel-loader',
        options: {
          // Add your babel presets here (e.g., @babel/preset-react)
          presets: ['@babel/preset-react'] // Assuming you use React
        },
      },
    });
    return config;
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  output: 'export',
  // TODO this is only needed when building for use within LO
  // basePath: '/_next/learning_observer_template/toy_assess'
};

module.exports = nextConfig;
