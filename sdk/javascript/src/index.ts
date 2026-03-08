/**
 * UATP JavaScript/TypeScript SDK - Official Developer Kit
 *
 * The complete JavaScript SDK for integrating with UATP's civilization-grade infrastructure.
 *
 *  Features:
 * - Simple attribution tracking for AI interactions
 * - Real-time economic attribution and payments
 * - Constitutional governance participation
 * - Zero-knowledge privacy proofs
 * - C2PA content credentials generation
 * - World Economic Forum Top 10 2025 watermarking
 * - Multi-platform AI integration (OpenAI, Anthropic, HuggingFace)
 *
 *  Getting Started:
 * ```typescript
 * import { UATP } from '@uatp/sdk';
 *
 * // Initialize UATP client
 * const client = new UATP({ apiKey: 'your-api-key' });
 *
 * // Track AI interaction with attribution
 * const result = await client.trackAiInteraction({
 *   prompt: 'Explain quantum computing',
 *   response: 'Quantum computing uses quantum mechanics...',
 *   platform: 'openai',
 *   model: 'gpt-4'
 * });
 *
 * // Get attribution rewards
 * const rewards = await client.getAttributionRewards('your-user-id');
 * ```
 */

export { UATP, UATPConfig, UATPOptions } from './client';
export { AttributionTracker, AttributionResult, TrackInteractionOptions } from './attribution';
export { EconomicEngine, RewardCalculator, EconomicMetrics, RewardDistribution } from './economics';
export { GovernanceClient, Proposal, Vote, ProposalStatus, VoteChoice } from './governance';
export { PrivacyEngine, ZKProof, PrivacyPolicy } from './privacy';
export { WatermarkEngine, WatermarkResult, WatermarkConfig } from './watermarking';
export { FederationClient, Node, FederationMetrics, NodeStatus, NetworkHealth } from './federation';

// Type exports
export type {
  ApiResponse,
  UATPError,
  RequestOptions,
  BaseConfig
} from './types';

// Constants
export const SDK_VERSION = '1.0.0';
export const DEFAULT_BASE_URL = 'https://api.uatp.global';

/**
 * Create a new UATP client instance with sensible defaults.
 *
 * @param options - Configuration options
 * @returns UATP client instance
 */
export function createClient(options: UATPOptions): UATP {
  return new UATP(options);
}

/**
 * Check if the current environment supports all UATP features.
 *
 * @returns Feature support information
 */
export function checkEnvironmentSupport() {
  const isNode = typeof window === 'undefined';
  const hasCrypto = typeof crypto !== 'undefined' || typeof require !== 'undefined';
  const hasLocalStorage = !isNode && typeof localStorage !== 'undefined';

  return {
    isNode,
    isBrowser: !isNode,
    supportsEncryption: hasCrypto,
    supportsLocalStorage: hasLocalStorage,
    supportsWebWorkers: !isNode && typeof Worker !== 'undefined',
    supportsWebRTC: !isNode && typeof RTCPeerConnection !== 'undefined',

    // UATP feature support
    supportsZeroKnowledge: hasCrypto,
    supportsWatermarking: true,
    supportsGovernance: true,
    supportsFederation: true
  };
}

// Default export for convenience
export default UATP;
