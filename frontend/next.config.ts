import type { NextConfig } from "next";

/**
 * Next.js Configuration
 *
 * SECURITY/QUALITY CONFIGURATION:
 * - TypeScript errors WILL fail the build (strict mode)
 * - ESLint errors WILL fail the build (strict mode)
 *
 * This is intentional to catch type safety and linting issues before deployment.
 * If you encounter build failures, fix the underlying issues rather than
 * disabling these checks.
 *
 * TypeScript Status (as of 2026-03-25):
 * - FIXED: capsule-detail.tsx 'confidence' property access
 * - FIXED: akc-dashboard.tsx null check for mockStats
 * - FIXED: system/page.tsx vis-network types
 *
 * Remaining issues (~155 errors) are spread across multiple files:
 * - capsule-list.tsx: type inference issues with demo data
 * - capsule-overview.tsx: missing CapsuleStatsResponse properties
 * - compliance-dashboard.tsx: mockStats null checks
 * - dashboard.tsx: TrustMetrics type union issues
 * - Various logger error context typing issues
 *
 * To check TypeScript errors locally: npx tsc --noEmit
 * To check ESLint errors locally: npx eslint src/
 */
const nextConfig: NextConfig = {
  output: 'standalone',

  // API proxy for development - makes API calls same-origin so cookies work
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_UATP_API_URL;
    if (!apiUrl) {
      throw new Error(
        'NEXT_PUBLIC_UATP_API_URL is required. Set it in your environment or .env.local'
      );
    }
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${apiUrl}/health`,
      },
      {
        source: '/onboarding/:path*',
        destination: `${apiUrl}/onboarding/:path*`,
      },
      {
        source: '/capsules/:path*',
        destination: `${apiUrl}/capsules/:path*`,
      },
    ];
  },

  // PRODUCTION QUALITY: Enable strict checking
  // Set to false only if you have a critical deployment blocker and
  // understand the security implications
  eslint: {
    // Enable ESLint checking during builds
    // This catches security issues, accessibility problems, and code quality issues
    ignoreDuringBuilds: process.env.SKIP_LINT_CHECK === 'true',
  },
  typescript: {
    // Enable TypeScript checking during builds
    // This catches type errors that could cause runtime failures
    ignoreBuildErrors: process.env.SKIP_TYPE_CHECK === 'true',
  },
};

export default nextConfig;
