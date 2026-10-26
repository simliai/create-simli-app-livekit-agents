import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep the dev badge clear of the footer links (bottom left).
  devIndicators: { position: "bottom-right" },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
