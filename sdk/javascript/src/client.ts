/**
 * UATP JavaScript/TypeScript SDK - Main Client
 * 
 * The primary interface for developers to integrate with UATP infrastructure.
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { AttributionTracker, AttributionResult, TrackInteractionOptions } from './attribution';
import { EconomicEngine, RewardCalculator } from './economics';
import { GovernanceClient } from './governance';
import { PrivacyEngine } from './privacy';
import { WatermarkEngine } from './watermarking';
import { FederationClient } from './federation';
import { ApiResponse, UATPError, RequestOptions, EventEmitter, UATPEvent, EventListener } from './types';

export interface UATPConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  retryAttempts?: number;
  enablePrivacy?: boolean;
  enableWatermarking?: boolean;
  enableGovernance?: boolean;
  federationNode?: string;
}

export interface UATPOptions extends UATPConfig {}

/**
 * The main UATP SDK client for developers.
 * 
 * Provides a simple, unified interface to UATP's civilization-grade infrastructure
 * for AI attribution, economic coordination, and democratic governance.
 */
export class UATP implements EventEmitter {
  public readonly config: Required<UATPConfig>;
  private httpClient: AxiosInstance;
  private eventListeners: Map<string, EventListener[]> = new Map();

  // Specialized engines
  public readonly attribution: AttributionTracker;
  public readonly economics: EconomicEngine;
  public readonly rewards: RewardCalculator;
  public readonly governance?: GovernanceClient;
  public readonly privacy?: PrivacyEngine;
  public readonly watermarking?: WatermarkEngine;
  public readonly federation?: FederationClient;

  constructor(config: UATPOptions) {
    if (!config.apiKey) {
      throw new UATPError('UATP API key is required. Get one at https://uatp.global/developers', 'MISSING_API_KEY');
    }

    this.config = {
      apiKey: config.apiKey,
      baseUrl: config.baseUrl || 'https://api.uatp.global',
      timeout: config.timeout || 30000,
      retryAttempts: config.retryAttempts || 3,
      enablePrivacy: config.enablePrivacy !== false,
      enableWatermarking: config.enableWatermarking !== false,
      enableGovernance: config.enableGovernance !== false,
      federationNode: config.federationNode || undefined
    };

    // Initialize HTTP client
    this.httpClient = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'User-Agent': 'UATP-JavaScript-SDK/1.0.0',
        'Content-Type': 'application/json'
      }
    });

    // Add request/response interceptors
    this.setupInterceptors();

    // Initialize specialized engines
    this.attribution = new AttributionTracker(this);
    this.economics = new EconomicEngine(this);
    this.rewards = new RewardCalculator(this);

    if (this.config.enableGovernance) {
      this.governance = new GovernanceClient(this);
    }

    if (this.config.enablePrivacy) {
      this.privacy = new PrivacyEngine(this);
    }

    if (this.config.enableWatermarking) {
      this.watermarking = new WatermarkEngine(this);
    }

    if (this.config.federationNode) {
      this.federation = new FederationClient(this, this.config.federationNode);
    }

    this.emit('initialized', { config: this.config });
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.httpClient.interceptors.request.use(
      (config) => {
        this.emit('request', { url: config.url, method: config.method });
        return config;
      },
      (error) => {
        this.emit('error', { type: 'request', error });
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.httpClient.interceptors.response.use(
      (response) => {
        this.emit('response', { 
          url: response.config.url, 
          status: response.status,
          duration: Date.now() - (response.config as any).requestStartTime
        });
        return response;
      },
      (error) => {
        if (error.response) {
          this.emit('error', {
            type: 'response',
            status: error.response.status,
            message: error.response.data?.message || error.message
          });
          
          return Promise.reject(UATPError.fromResponse({
            message: error.response.data?.message || error.message,
            code: error.response.data?.code || 'HTTP_ERROR',
            statusCode: error.response.status,
            details: error.response.data
          }));
        }
        
        this.emit('error', { type: 'network', error: error.message });
        return Promise.reject(new UATPError(error.message, 'NETWORK_ERROR'));
      }
    );
  }

  /**
   * Make an HTTP request to the UATP API
   */
  async request<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    endpoint: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const config: AxiosRequestConfig = {
      method,
      url: endpoint,
      data,
      headers: options?.headers,
      timeout: options?.timeout,
      signal: options?.signal
    };

    // Add request timing
    (config as any).requestStartTime = Date.now();

    try {
      const response = await this.httpClient.request<T>(config);
      
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      if (error instanceof UATPError) {
        throw error;
      }
      
      throw new UATPError(
        error instanceof Error ? error.message : 'Unknown error',
        'REQUEST_FAILED'
      );
    }
  }

  /**
   * Track an AI interaction for attribution and economic rewards.
   */
  async trackAiInteraction(options: TrackInteractionOptions): Promise<AttributionResult> {
    return await this.attribution.trackInteraction(options);
  }

  /**
   * Get attribution rewards for a user.
   */
  async getAttributionRewards(userId: string, timePeriod: string = '30d'): Promise<any> {
    return await this.rewards.getUserRewards(userId, timePeriod);
  }

  /**
   * Create a UATP capsule with optional privacy and watermarking.
   */
  async createCapsule(options: {
    capsuleType: string;
    content: any;
    withPrivacy?: boolean;
    withWatermark?: boolean;
  }): Promise<any> {
    const { capsuleType, content, withPrivacy, withWatermark } = options;

    // Apply default privacy/watermarking settings
    const enablePrivacy = withPrivacy !== undefined ? withPrivacy : this.config.enablePrivacy;
    const enableWatermark = withWatermark !== undefined ? withWatermark : this.config.enableWatermarking;

    // Create base capsule
    const capsuleData: any = {
      capsuleType,
      content,
      timestamp: new Date().toISOString(),
      sdkVersion: '1.0.0'
    };

    // Add privacy proof if enabled
    if (enablePrivacy && this.privacy) {
      const privacyProof = await this.privacy.createProof(capsuleData);
      capsuleData.privacyProof = privacyProof;
    }

    // Add watermark if enabled
    if (enableWatermark && this.watermarking) {
      const watermarkResult = await this.watermarking.applyWatermark(content, 'text');
      capsuleData.watermark = watermarkResult;
    }

    // Submit to UATP network
    const response = await this.request('POST', '/api/v1/capsules', capsuleData);
    
    this.emit('capsule_created', { capsuleId: response.data?.capsuleId });
    
    return response.data;
  }

  /**
   * Verify a capsule's cryptographic integrity and authenticity.
   */
  async verifyCapsule(capsuleId: string): Promise<any> {
    const response = await this.request('GET', `/api/v1/capsules/${capsuleId}/verify`);
    return response.data;
  }

  /**
   * Participate in UATP democratic governance.
   */
  async participateInGovernance(options: {
    action: 'vote' | 'propose' | 'delegate';
    proposalId?: string;
    vote?: 'approve' | 'reject' | 'abstain';
    proposalData?: any;
  }): Promise<any> {
    if (!this.governance) {
      throw new UATPError('Governance is disabled in configuration', 'GOVERNANCE_DISABLED');
    }

    const { action, proposalId, vote, proposalData } = options;

    if (action === 'vote' && proposalId && vote) {
      return await this.governance.castVote(proposalId, vote);
    } else if (action === 'propose' && proposalData) {
      return await this.governance.createProposal(proposalData);
    } else {
      throw new UATPError(`Invalid governance action or missing parameters`, 'INVALID_GOVERNANCE_ACTION');
    }
  }

  /**
   * Get status of the global UATP network.
   */
  async getNetworkStatus(): Promise<any> {
    const response = await this.request('GET', '/api/v1/network/status');
    return response.data;
  }

  /**
   * Get global economic metrics from the UATP network.
   */
  async getEconomicMetrics(): Promise<any> {
    return await this.economics.getGlobalMetrics();
  }

  /**
   * Estimate the attribution value of content before submission.
   */
  async estimateAttributionValue(options: {
    contentType: string;
    contentSize: number;
    qualityScore?: number;
  }): Promise<any> {
    const { contentType, contentSize, qualityScore } = options;
    return await this.rewards.estimateValue(contentType, contentSize, qualityScore);
  }

  // Event emitter implementation
  on<T>(event: string, listener: EventListener<T>): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(listener as EventListener);
  }

  off<T>(event: string, listener: EventListener<T>): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener as EventListener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit<T>(event: string, data: T): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const eventObj: UATPEvent<T> = {
        type: event,
        data,
        timestamp: new Date().toISOString(),
        source: 'uatp-sdk'
      };

      listeners.forEach(listener => {
        try {
          listener(eventObj);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Clean up resources and close connections.
   */
  async close(): Promise<void> {
    this.eventListeners.clear();
    this.emit('closed', {});
  }
}

export { UATPConfig };