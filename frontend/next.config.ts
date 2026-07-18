import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable Web Worker support via webpack 5 worker loader
  webpack: (config) => {
    config.module?.rules?.push({
      test: /\.worker\.ts$/,
      type: 'asset/resource',
      generator: {
        filename: 'static/workers/[name].[hash][ext]',
      },
    })
    return config
  },
  // Allow CDN loading of MediaPipe WASM/model assets
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'credentialless',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
        ],
      },
    ]
  },
};

export default nextConfig;
