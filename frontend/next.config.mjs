// NOTE: Section 3 lists `next.config.ts`, but TypeScript Next config is only
// supported from Next.js 15. Section 2 pins Next.js 14.x, so this is `.mjs`
// (the working equivalent on 14). Rename to .ts if/when upgrading to Next 15.
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Backend serves audit images/crawl data from arbitrary domains later;
  // keep remote patterns open in dev, tighten per-domain in production.
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
};

export default nextConfig;
