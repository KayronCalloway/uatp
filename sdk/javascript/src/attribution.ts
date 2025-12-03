/**
 * UATP JavaScript/TypeScript SDK - Attribution Tracking Module
 * 
 * Provides attribution tracking functionality for AI interactions and content generation.
 */

import CryptoJS from 'crypto-js';
import { ApiResponse, UATPError, Timestamp, UUID } from './types';

export interface TrackInteractionOptions {
  prompt: string;
  response: string;
  platform: string;
  model: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export interface AttributionResult {
  capsuleId: string;
  attributionId: string;
  confidenceScore: number;
  creatorAttribution: {
    userId?: string;
    contributionType: string;
    attributionPercentage: number;
  };
  aiAttribution: {
    platform: string;
    model: string;
    attributionPercentage: number;
  };
  economicImpact: {
    estimatedValue: number;
    creatorReward: number;
    commonsContribution: number;
  };
  verificationStatus: string;
  timestamp: Timestamp;
}

export interface UpdateAttributionOptions {
  updates: Record<string, any>;
}

export interface GetUserAttributionsOptions {
  limit?: number;
  offset?: number;
}

/**
 * Handles attribution tracking for AI interactions.
 */
export class AttributionTracker {
  private client: any;
  private attributionCache: Map<string, AttributionResult> = new Map();

  constructor(client: any) {
    this.client = client;
  }

  /**
   * Track an AI interaction for attribution.
   */
  async trackInteraction(options: TrackInteractionOptions): Promise<AttributionResult> {
    const { prompt, response, platform, model, userId, metadata = {} } = options;

    // Generate interaction hash for uniqueness
    const interactionData = {
      prompt,
      response,
      platform,
      model,
      timestamp: new Date().toISOString()
    };

    const interactionHash = CryptoJS.SHA256(
      JSON.stringify(interactionData)
    ).toString().substring(0, 16);

    // Build attribution request
    const attributionRequest = {
      interactionHash,
      prompt,
      response,
      platform,
      model,
      userId,
      metadata,
      timestamp: new Date().toISOString(),
      sdkVersion: '1.0.0'
    };

    try {
      // Submit to UATP attribution service
      const response = await this.client.request(
        'POST',
        '/api/v1/attribution/track',
        attributionRequest
      );

      const resultData = response.data;

      // Create attribution result
      const attributionResult: AttributionResult = {
        capsuleId: resultData.capsuleId || `cap_${interactionHash}`,
        attributionId: resultData.attributionId || `attr_${interactionHash}`,
        confidenceScore: resultData.confidenceScore || 0.85,
        creatorAttribution: {
          userId,
          contributionType: 'human_input',
          attributionPercentage: resultData.creatorPercentage || 0.3
        },
        aiAttribution: {
          platform,
          model,
          attributionPercentage: resultData.aiPercentage || 0.7
        },
        economicImpact: {
          estimatedValue: resultData.estimatedValue || 0.0,
          creatorReward: resultData.creatorReward || 0.0,
          commonsContribution: resultData.commonsContribution || 0.0
        },
        verificationStatus: resultData.verificationStatus || 'verified',
        timestamp: new Date().toISOString()
      };

      // Cache the result
      this.attributionCache.set(attributionResult.attributionId, attributionResult);

      this.client.emit('attribution_tracked', { attributionId: attributionResult.attributionId });
      return attributionResult;

    } catch (error) {
      // Return fallback attribution result
      const fallbackResult: AttributionResult = {
        capsuleId: `fallback_cap_${interactionHash}`,
        attributionId: `fallback_attr_${interactionHash}`,
        confidenceScore: 0.5,
        creatorAttribution: {
          userId,
          contributionType: 'human_input',
          attributionPercentage: 0.3
        },
        aiAttribution: {
          platform,
          model,
          attributionPercentage: 0.7
        },
        economicImpact: {
          estimatedValue: 0.0,
          creatorReward: 0.0,
          commonsContribution: 0.0
        },
        verificationStatus: 'pending',
        timestamp: new Date().toISOString()
      };

      this.attributionCache.set(fallbackResult.attributionId, fallbackResult);
      return fallbackResult;
    }
  }

  /**
   * Get attribution result by ID.
   */
  async getAttribution(attributionId: string): Promise<AttributionResult | null> {
    // Check cache first
    if (this.attributionCache.has(attributionId)) {
      return this.attributionCache.get(attributionId)!;
    }

    try {
      const response = await this.client.request('GET', `/api/v1/attribution/${attributionId}`);
      const data = response.data;

      const attributionResult: AttributionResult = {
        capsuleId: data.capsuleId,
        attributionId: data.attributionId,
        confidenceScore: data.confidenceScore,
        creatorAttribution: data.creatorAttribution,
        aiAttribution: data.aiAttribution,
        economicImpact: data.economicImpact,
        verificationStatus: data.verificationStatus,
        timestamp: data.timestamp
      };

      // Cache the result
      this.attributionCache.set(attributionId, attributionResult);
      return attributionResult;

    } catch (error) {
      console.error(`Failed to get attribution ${attributionId}:`, error);
      return null;
    }
  }

  /**
   * Update an existing attribution with new information.
   */
  async updateAttribution(attributionId: string, options: UpdateAttributionOptions): Promise<boolean> {
    try {
      await this.client.request(
        'PATCH',
        `/api/v1/attribution/${attributionId}`,
        options.updates
      );

      // Clear from cache to force refresh
      this.attributionCache.delete(attributionId);

      this.client.emit('attribution_updated', { attributionId });
      return true;

    } catch (error) {
      console.error(`Failed to update attribution ${attributionId}:`, error);
      return false;
    }
  }

  /**
   * Get all attributions for a specific user.
   */
  async getUserAttributions(
    userId: string,
    options: GetUserAttributionsOptions = {}
  ): Promise<AttributionResult[]> {
    const { limit = 50, offset = 0 } = options;

    try {
      const params = { userId, limit, offset };
      const response = await this.client.request('GET', '/api/v1/attribution/user', null, {
        headers: { 'X-Query-Params': JSON.stringify(params) }
      });

      const data = response.data;
      const attributions: AttributionResult[] = [];

      for (const item of data.attributions || []) {
        const attribution: AttributionResult = {
          capsuleId: item.capsuleId,
          attributionId: item.attributionId,
          confidenceScore: item.confidenceScore,
          creatorAttribution: item.creatorAttribution,
          aiAttribution: item.aiAttribution,
          economicImpact: item.economicImpact,
          verificationStatus: item.verificationStatus,
          timestamp: item.timestamp
        };
        attributions.push(attribution);
      }

      return attributions;

    } catch (error) {
      console.error(`Failed to get user attributions for ${userId}:`, error);
      return [];
    }
  }

  /**
   * Verify the cryptographic integrity of an attribution.
   */
  async verifyAttribution(attributionId: string): Promise<any> {
    try {
      const response = await this.client.request(
        'POST',
        `/api/v1/attribution/${attributionId}/verify`
      );

      this.client.emit('attribution_verified', { attributionId });
      return response.data;

    } catch (error) {
      console.error(`Attribution verification failed for ${attributionId}:`, error);
      return {
        verified: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Estimate the economic value of an attribution before tracking.
   */
  async estimateAttributionValue(options: {
    prompt: string;
    response: string;
    platform: string;
    model: string;
  }): Promise<any> {
    const estimationRequest = {
      ...options,
      estimationOnly: true
    };

    try {
      const response = await this.client.request(
        'POST',
        '/api/v1/attribution/estimate',
        estimationRequest
      );

      return response.data;

    } catch (error) {
      console.error('Attribution value estimation failed:', error);
      return {
        estimatedValue: 0.0,
        creatorReward: 0.0,
        commonsContribution: 0.0,
        confidence: 0.0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get all cached attribution results.
   */
  getCachedAttributions(): AttributionResult[] {
    return Array.from(this.attributionCache.values());
  }

  /**
   * Clear the attribution cache.
   */
  clearCache(): void {
    this.attributionCache.clear();
    this.client.emit('attribution_cache_cleared', {});
  }
}