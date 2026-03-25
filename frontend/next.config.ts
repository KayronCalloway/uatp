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
 * Known type issues to fix (as of 2026-03-25):
 * - src/components/capsules/capsule-detail.tsx: 'confidence' property access
 * - src/components/akc/akc-dashboard.tsx: null check for mockStats
 * - src/app/system/page.tsx: vis-network types
 *
 * To check TypeScript errors locally: npx tsc --noEmit
 * To check ESLint errors locally: npx eslint src/
 */
const nextConfig: NextConfig = {
  output: 'standalone',

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
