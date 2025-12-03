/**
 * UATP JavaScript/TypeScript SDK - Economic Engine Module
 * 
 * Handles economic attribution, reward calculation, and payment distribution.
 */

import { ApiResponse, UATPError, Timestamp } from './types';

export interface RewardDistribution {
  distributionId: string;
  userId: string;
  amount: string; // Using string for precision with large numbers
  currency: string;
  source: 'attribution' | 'commons' | 'governance' | 'dividend';
  attributionId?: string;
  paymentStatus: 'pending' | 'processing' | 'completed' | 'failed';
  paymentMethod?: string;
  transactionHash?: string;
  timestamp: Timestamp;
}

export interface EconomicMetrics {
  totalAttributionValue: string;
  totalRewardsDistributed: string;
  commonsFundBalance: string;
  activeContributors: number;
  attributionVolume24h: number;
  averageRewardPerAttribution: string;
  ubaPercentage: number; // Universal Basic Attribution percentage
  timestamp: Timestamp;
}

export interface ValueCalculationOptions {
  contentType: string;
  contentSize: number;
  qualityScore?: number;
  platform?: string;
  model?: string;
}

export interface RewardSummary {
  userId: string;
  timePeriod: string;
  totalEarned: string;
  pendingRewards: string;
  paidRewards: string;
  attributionCount: number;
  sources: Record<string, string>;
  paymentMethods: Record<string, string>;
}

/**
 * Handles economic aspects of the UATP network.
 */
export class EconomicEngine {
  private client: any;
  private metricsCache: Map<string, { data: EconomicMetrics; timestamp: number }> = new Map();
  private readonly CACHE_TTL = 300000; // 5 minutes

  constructor(client: any) {
    this.client = client;
  }

  /**
   * Get current global economic metrics from the UATP network.
   */
  async getGlobalMetrics(): Promise<EconomicMetrics> {
    // Check cache
    const cached = this.metricsCache.get('global_metrics');
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data;
    }

    try {
      const response = await this.client.request('GET', '/api/v1/economics/metrics');
      const data = response.data;

      const metrics: EconomicMetrics = {
        totalAttributionValue: data.totalAttributionValue || '0.0',
        totalRewardsDistributed: data.totalRewardsDistributed || '0.0',
        commonsFundBalance: data.commonsFundBalance || '0.0',
        activeContributors: data.activeContributors || 0,
        attributionVolume24h: data.attributionVolume24h || 0,
        averageRewardPerAttribution: data.averageRewardPerAttribution || '0.0',
        ubaPercentage: data.ubaPercentage || 0.15,
        timestamp: new Date().toISOString()
      };

      // Cache the result
      this.metricsCache.set('global_metrics', {
        data: metrics,
        timestamp: Date.now()
      });

      this.client.emit('economic_metrics_retrieved', { metrics });
      return metrics;

    } catch (error) {
      console.error('Failed to get global metrics:', error);

      // Return fallback metrics
      return {
        totalAttributionValue: '0.0',
        totalRewardsDistributed: '0.0',
        commonsFundBalance: '0.0',
        activeContributors: 0,
        attributionVolume24h: 0,
        averageRewardPerAttribution: '0.0',
        ubaPercentage: 0.15,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Calculate the economic value of content for attribution.
   */
  async calculateAttributionValue(options: ValueCalculationOptions): Promise<any> {
    const calculationRequest = {
      ...options,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request(
        'POST',
        '/api/v1/economics/calculate-value',
        calculationRequest
      );

      this.client.emit('value_calculated', { 
        contentType: options.contentType,
        totalValue: response.data.totalValue 
      });

      return response.data;

    } catch (error) {
      console.error('Value calculation failed:', error);

      // Fallback calculation using simple heuristics
      const baseValue = this.fallbackValueCalculation(
        options.contentType,
        options.contentSize,
        options.qualityScore
      );

      return {
        totalValue: baseValue,
        creatorShare: baseValue * 0.3,
        aiPlatformShare: baseValue * 0.55,
        commonsShare: baseValue * 0.15,
        calculationMethod: 'fallback_heuristic',
        confidence: 0.5,
        timestamp: new Date().toISOString()
      };
    }
  }

  private fallbackValueCalculation(
    contentType: string,
    contentSize: number,
    qualityScore?: number
  ): number {
    // Base rates per content type (in USD)
    const baseRates: Record<string, number> = {
      text: 0.001,      // $0.001 per 100 chars
      code: 0.005,      // $0.005 per 100 chars
      image: 0.01,      // $0.01 per image
      audio: 0.002,     // $0.002 per second
      video: 0.005      // $0.005 per second
    };

    const baseRate = baseRates[contentType] || 0.001;
    const sizeFactor = Math.max(1, contentSize / 100);
    const qualityFactor = qualityScore !== undefined ? qualityScore : 0.7;

    return baseRate * sizeFactor * qualityFactor;
  }

  /**
   * Get status of the Universal Basic Attribution commons fund.
   */
  async getCommonsFundStatus(): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/economics/commons-fund');
      return response.data;

    } catch (error) {
      console.error('Failed to get commons fund status:', error);
      return {
        balance: '0.0',
        monthlyDistribution: '0.0',
        eligibleRecipients: 0,
        distributionMethod: 'pro_rata',
        nextDistribution: null,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Estimate monthly Universal Basic Attribution for a user.
   */
  async estimateMonthlyUBA(userId: string): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/economics/estimate-uba', null, {
        headers: { 'X-User-ID': userId }
      });

      return response.data;

    } catch (error) {
      console.error(`UBA estimation failed for user ${userId}:`, error);
      return {
        estimatedMonthlyUba: '0.0',
        eligibilityStatus: 'unknown',
        contributionScore: 0.0,
        paymentMethod: null,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get economic metrics for a specific AI platform.
   */
  async getPlatformEconomics(platform: string): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/economics/platform-metrics', null, {
        headers: { 'X-Platform': platform }
      });

      return response.data;

    } catch (error) {
      console.error(`Failed to get platform economics for ${platform}:`, error);
      return {
        platform,
        totalAttributions: 0,
        totalValueGenerated: '0.0',
        totalRewardsPaid: '0.0',
        attributionEfficiency: 0.0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

/**
 * Handles reward calculations and payment processing.
 */
export class RewardCalculator {
  private client: any;
  private readonly paymentMethods = ['usd', 'crypto', 'credits'];

  constructor(client: any) {
    this.client = client;
  }

  /**
   * Get reward summary for a user over a time period.
   */
  async getUserRewards(userId: string, timePeriod: string = '30d'): Promise<RewardSummary> {
    try {
      const response = await this.client.request('GET', '/api/v1/rewards/user-summary', null, {
        headers: { 
          'X-User-ID': userId,
          'X-Time-Period': timePeriod
        }
      });

      this.client.emit('rewards_retrieved', { 
        userId, 
        totalEarned: response.data.totalEarned 
      });

      return response.data;

    } catch (error) {
      console.error(`Failed to get user rewards for ${userId}:`, error);
      return {
        userId,
        timePeriod,
        totalEarned: '0.0',
        pendingRewards: '0.0',
        paidRewards: '0.0',
        attributionCount: 0,
        sources: {},
        paymentMethods: {}
      };
    }
  }

  /**
   * Get detailed reward history for a user.
   */
  async getRewardHistory(
    userId: string,
    options: { limit?: number; offset?: number } = {}
  ): Promise<RewardDistribution[]> {
    const { limit = 50, offset = 0 } = options;

    try {
      const response = await this.client.request('GET', '/api/v1/rewards/history', null, {
        headers: {
          'X-User-ID': userId,
          'X-Limit': limit.toString(),
          'X-Offset': offset.toString()
        }
      });

      const data = response.data;
      const distributions: RewardDistribution[] = [];

      for (const item of data.distributions || []) {
        distributions.push({
          distributionId: item.distributionId,
          userId: item.userId,
          amount: item.amount,
          currency: item.currency,
          source: item.source,
          attributionId: item.attributionId,
          paymentStatus: item.paymentStatus,
          paymentMethod: item.paymentMethod,
          transactionHash: item.transactionHash,
          timestamp: item.timestamp
        });
      }

      return distributions;

    } catch (error) {
      console.error(`Failed to get reward history for ${userId}:`, error);
      return [];
    }
  }

  /**
   * Estimate attribution value before content submission.
   */
  async estimateValue(
    contentType: string,
    contentSize: number,
    qualityScore?: number
  ): Promise<any> {
    const estimationRequest = {
      contentType,
      contentSize,
      qualityScore,
      estimationMode: true
    };

    try {
      const response = await this.client.request(
        'POST',
        '/api/v1/rewards/estimate',
        estimationRequest
      );

      return response.data;

    } catch (error) {
      console.error('Value estimation failed:', error);

      // Fallback estimation
      const baseValue = this.estimateBaseValue(contentType, contentSize, qualityScore);
      return {
        estimatedValue: baseValue,
        creatorReward: baseValue * 0.3,
        confidenceInterval: {
          low: baseValue * 0.7,
          high: baseValue * 1.3
        },
        factors: {
          contentType,
          sizeFactor: contentSize,
          qualityFactor: qualityScore || 0.7
        },
        method: 'fallback_estimation'
      };
    }
  }

  private estimateBaseValue(
    contentType: string,
    contentSize: number,
    qualityScore?: number
  ): number {
    const typeMultipliers: Record<string, number> = {
      text: 0.001,
      code: 0.005,
      image: 0.01,
      audio: 0.002,
      video: 0.005
    };

    const baseRate = typeMultipliers[contentType] || 0.001;
    const sizeFactor = Math.max(1, contentSize / 1000);
    const qualityFactor = qualityScore !== undefined ? qualityScore : 0.7;

    return baseRate * sizeFactor * qualityFactor;
  }

  /**
   * Request payout of accumulated rewards.
   */
  async requestPayout(options: {
    userId: string;
    amount: string;
    paymentMethod: string;
    currency?: string;
  }): Promise<any> {
    const { userId, amount, paymentMethod, currency = 'USD' } = options;

    const payoutRequest = {
      userId,
      amount,
      paymentMethod,
      currency,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request(
        'POST',
        '/api/v1/rewards/payout',
        payoutRequest
      );

      this.client.emit('payout_requested', { userId, amount });
      return response.data;

    } catch (error) {
      console.error(`Payout request failed for user ${userId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        payoutId: null,
        estimatedProcessingTime: null
      };
    }
  }

  /**
   * Get available payout methods for a user.
   */
  async getPayoutMethods(userId: string): Promise<any[]> {
    try {
      const response = await this.client.request('GET', '/api/v1/rewards/payout-methods', null, {
        headers: { 'X-User-ID': userId }
      });

      return response.data.methods || [];

    } catch (error) {
      console.error(`Failed to get payout methods for user ${userId}:`, error);
      return [
        {
          method: 'bank_transfer',
          currency: 'USD',
          minimumAmount: '10.00',
          feePercentage: 2.5,
          processingTime: '3-5 business days'
        }
      ];
    }
  }
}