import axios, { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { logger } from './logger';
import { getCsrfToken, requiresCsrf } from './csrf';
import {
  CapsuleListResponse,
  CompressedCapsuleListResponse,
  ListCapsulesQuery,
  GetCapsuleQuery,
  CapsuleDetailResponse,
  CapsuleStatsResponse,
  VerificationResponse,
  HealthCheckResponse,
  CryptoStatusResponse,
  IndexResponse,
  AIGenerateRequest,
  AIGenerateResponse,
  ChainSealListResponse,
  SealChainRequest,
  SealChainResponse,
  VerifySealQuery,
  VerifySealResponse,
  AnyCapsule,
  TrustMetrics,
  ReasoningAnalysisRequest,
  ReasoningAnalysisResponse,
  ValidationResponse,
  ErrorResponse,
  FullTextSearchResponse,
  FullTextSearchQuery,
  VerifiedContextResponse,
  VerifiedContextQuery,
} from '@/types/api';
// Onboarding types removed

/**
 * SECURITY: Get API base URL with strict production checks.
 *
 * In development (browser): Uses empty string so requests go through Next.js proxy
 * In development (server): Falls back to localhost:8000
 * In production: NEXT_PUBLIC_UATP_API_URL must be set, or this throws.
 */
export function getApiBaseUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_UATP_API_URL;
  const isDev = process.env.NODE_ENV === 'development';
  const isBrowser = typeof window !== 'undefined';

  if (configuredUrl) {
    return configuredUrl;
  }

  if (isDev) {
    // In browser during development, use relative URLs for Next.js proxy
    // This makes API calls same-origin so cookies work
    if (isBrowser) {
      return '';
    }
    // Server-side still needs the full URL
    return 'http://localhost:8000';
  }

  // SECURITY: In production, missing config should fail loudly
  throw new Error(
    'NEXT_PUBLIC_UATP_API_URL is not configured. ' +
    'This is required in production. Set it in your deployment environment.'
  );
}

export class UATCapsuleEngineClient {
  private client: AxiosInstance;
  private authToken: string | null = null;
  private static readonly isDevelopment = process.env.NODE_ENV === 'development';

  /**
   * Create API client.
   *
   * SECURITY:
   * - Uses getApiBaseUrl() which fails in production if URL not configured
   * - API keys from NEXT_PUBLIC_UATP_API_KEY are only for development/demo
   * - Production browser auth should use HTTP-only cookies, not API keys
   */
  constructor(
    baseURL?: string,
    apiKey?: string
  ) {
    // Use provided baseURL or get from environment with strict checks
    const effectiveBaseUrl = baseURL || getApiBaseUrl();

    // SECURITY: Warn if using bundled API key in production
    const envApiKey = process.env.NEXT_PUBLIC_UATP_API_KEY;
    if (envApiKey && !UATCapsuleEngineClient.isDevelopment) {
      console.warn(
        '[SECURITY] NEXT_PUBLIC_UATP_API_KEY is set in production. ' +
        'This key is bundled into the client and visible to users. ' +
        'Ensure this is only a low-privilege demo/public key.'
      );
    }

    // SECURITY: Only use API key if explicitly provided or from environment
    // In production, prefer cookie-based auth over API keys in browser
    const effectiveApiKey = apiKey || envApiKey;

    this.client = axios.create({
      baseURL: effectiveBaseUrl,
      timeout: 30000,
      // SECURITY: withCredentials enables HTTP-only cookie auth
      // Cookies are set by backend login and sent automatically
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        ...(effectiveApiKey && { 'X-API-Key': effectiveApiKey }),
      },
    });

    // Add request interceptor for CSRF token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add CSRF token to mutation requests (POST, PUT, DELETE, PATCH)
        if (config.method && requiresCsrf(config.method)) {
          const csrfToken = getCsrfToken();
          if (csrfToken) {
            config.headers = config.headers || {};
            config.headers['X-CSRF-Token'] = csrfToken;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // SECURITY: Logger handles dev-only output
        logger.apiError(
          error.config?.url || 'unknown',
          error.response?.status || error.code || 'unknown',
          error
        );

        if (error.response?.data?.error) {
          throw new Error(error.response.data.error);
        }
        if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          throw new Error('Cannot connect to server. Please check if the backend is running.');
        }
        throw error;
      }
    );
  }

  // Authentication methods
  setApiKey(apiKey: string) {
    this.client.defaults.headers['X-API-Key'] = apiKey;
  }

  removeApiKey() {
    delete this.client.defaults.headers['X-API-Key'];
  }

  /**
   * Set JWT auth token for authenticated requests
   * Required for capsule operations under user-scoped isolation
   */
  setAuthToken(token: string) {
    this.authToken = token;
    this.client.defaults.headers['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Remove auth token
   */
  removeAuthToken() {
    this.authToken = null;
    delete this.client.defaults.headers['Authorization'];
  }

  /**
   * Check if client has auth token set
   */
  hasAuthToken(): boolean {
    return this.authToken !== null;
  }

  // Core endpoints
  async getIndex(): Promise<IndexResponse> {
    const response = await this.client.get('/');
    return response.data;
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * @deprecated Use healthCheck() instead - /health/detailed endpoint does not exist
   * Kept for backwards compatibility, delegates to /health
   */
  async healthCheckDetailed(): Promise<HealthCheckResponse> {
    // NOTE: /health/detailed does not exist in backend
    // Delegate to /health to prevent 404 errors
    return this.healthCheck();
  }

  async getRecentActivity(): Promise<any> {
    const response = await this.client.get('/health/activity');
    return response.data;
  }

  async getHealthMetrics(): Promise<any> {
    const response = await this.client.get('/health/metrics');
    return response.data;
  }

  async getCryptoStatus(): Promise<CryptoStatusResponse> {
    const response = await this.client.get('/health/crypto');
    return response.data;
  }

  // Helper method to normalize capsule data
  private normalizeCapsule(capsule: any): AnyCapsule {
    // Ensure both id and capsule_id fields are available
    return {
      ...capsule,
      id: capsule.id || capsule.capsule_id,
      capsule_id: capsule.capsule_id || capsule.id,
    };
  }

  private normalizeCapsuleResponse(response: CapsuleListResponse | CompressedCapsuleListResponse): CapsuleListResponse | CompressedCapsuleListResponse {
    if ('capsules' in response && Array.isArray(response.capsules)) {
      return {
        ...response,
        capsules: response.capsules.map(capsule => this.normalizeCapsule(capsule))
      };
    }
    return response;
  }

  // Capsule endpoints
  async listCapsules(query?: ListCapsulesQuery): Promise<CapsuleListResponse | CompressedCapsuleListResponse> {
    const response = await this.client.get('/capsules', { params: query });
    return this.normalizeCapsuleResponse(response.data);
  }

  /**
   * Full-text search across capsule content using FTS5/ts_vector
   */
  async searchCapsules(query: FullTextSearchQuery): Promise<FullTextSearchResponse> {
    const response = await this.client.get('/capsules/search', { params: query });
    return response.data;
  }

  /**
   * Verified Context Retrieval - Trusted RAG for LLM applications
   *
   * Returns search results with cryptographic verification status.
   * Use verified_only=true to only retrieve capsules with valid signatures.
   */
  async getVerifiedContext(query: VerifiedContextQuery): Promise<VerifiedContextResponse> {
    const response = await this.client.get('/capsules/context', { params: query });
    return response.data;
  }

  async getCapsule(id: string, query?: GetCapsuleQuery): Promise<CapsuleDetailResponse> {
    const response = await this.client.get(`/capsules/${id}`, { params: query });
    const data = response.data;
    if (data.capsule) {
      data.capsule = this.normalizeCapsule(data.capsule);
    }
    return data;
  }

  async createCapsule(capsule: Partial<AnyCapsule>): Promise<AnyCapsule> {
    const response = await this.client.post('/capsules', capsule);
    return response.data;
  }

  async verifyCapsule(id: string): Promise<VerificationResponse> {
    const response = await this.client.get(`/capsules/${id}/verify`);
    return response.data;
  }

  async getCapsuleStats(demoMode: boolean = false): Promise<CapsuleStatsResponse> {
    const response = await this.client.get('/capsules/stats', {
      params: { demo_mode: demoMode }
    });
    return response.data;
  }

  async getEthicsStatus(): Promise<any> {
    const response = await this.client.get('/capsules/ethics');
    return response.data;
  }

  // Chain endpoints
  async getChainSeals(): Promise<ChainSealListResponse> {
    const response = await this.client.get('/chain/seals');
    return response.data;
  }

  async sealChain(request: SealChainRequest): Promise<SealChainResponse> {
    const response = await this.client.post('/chain/seal', request);
    return response.data;
  }

  async verifySeal(chainId: string, query: VerifySealQuery): Promise<VerifySealResponse> {
    const response = await this.client.get(`/chain/verify-seal/${chainId}`, { params: query });
    return response.data;
  }

  // AI endpoints
  async generateAI(request: AIGenerateRequest): Promise<AIGenerateResponse> {
    const response = await this.client.post('/ai/generate', request);
    return response.data;
  }

  // Trust endpoints
  async getTrustStatus(agentId: string): Promise<any> {
    const response = await this.client.get(`/trust/agent/${agentId}/status`);
    return response.data;
  }

  async getTrustMetrics(): Promise<TrustMetrics[]> {
    const response = await this.client.get('/trust/metrics');
    return response.data;
  }

  async getTrustPolicies(): Promise<any> {
    const response = await this.client.get('/trust/policies');
    return response.data;
  }

  async getRecentViolations(): Promise<any> {
    const response = await this.client.get('/trust/violations/recent');
    return response.data;
  }

  async getQuarantinedAgents(): Promise<any> {
    const response = await this.client.get('/trust/agents/quarantined');
    // Normalize the response structure for frontend compatibility
    const data = response.data;
    return {
      ...data,
      agents: data.quarantined_agents || []
    };
  }

  // Reasoning endpoints
  async validateReasoning(request: ReasoningAnalysisRequest): Promise<ValidationResponse> {
    const response = await this.client.post('/reasoning/validate', request);
    return response.data;
  }

  async analyzeReasoning(request: ReasoningAnalysisRequest): Promise<ReasoningAnalysisResponse> {
    const response = await this.client.post('/reasoning/analyze', request);
    return response.data;
  }

  async compareReasoning(request: { traces: any[] }): Promise<any> {
    const response = await this.client.post('/reasoning/compare', request);
    return response.data;
  }

  async analyzeBatch(request: { items: any[] }): Promise<any> {
    const response = await this.client.post('/reasoning/analyze-batch', request);
    return response.data;
  }

  // Metrics endpoint
  async getMetrics(): Promise<string> {
    const response = await this.client.get('/metrics', {
      headers: { 'Accept': 'text/plain' },
    });
    return response.data;
  }

  // Federation endpoints
  async getFederationNodes(): Promise<any> {
    const response = await this.client.get('/federation/nodes');
    return response.data;
  }

  async addFederationNode(nodeData: { name: string; url: string; region: string }): Promise<any> {
    const response = await this.client.post('/federation/nodes', nodeData);
    return response.data;
  }

  async getFederationStats(): Promise<any> {
    const response = await this.client.get('/federation/stats');
    return response.data;
  }

  async syncFederationNode(nodeId: string): Promise<any> {
    const response = await this.client.post(`/federation/nodes/${nodeId}/sync`);
    return response.data;
  }

  // Governance endpoints
  async getProposals(): Promise<any> {
    const response = await this.client.get('/governance/proposals');
    return response.data;
  }

  async getProposal(proposalId: string): Promise<any> {
    const response = await this.client.get(`/governance/proposals/${proposalId}`);
    return response.data;
  }

  async createProposal(proposalData: { title: string; description: string; category: string }): Promise<any> {
    const response = await this.client.post('/governance/proposals', proposalData);
    return response.data;
  }

  async voteOnProposal(proposalId: string, vote: 'for' | 'against' | 'abstain'): Promise<any> {
    const response = await this.client.post(`/governance/proposals/${proposalId}/vote`, { vote });
    return response.data;
  }

  async getGovernanceStats(): Promise<any> {
    const response = await this.client.get('/governance/stats');
    return response.data;
  }

  // Analytics endpoints
  async getAnalytics(): Promise<any> {
    const response = await this.client.get('/analytics');
    return response.data;
  }

  async getEconomicMetrics(): Promise<any> {
    const response = await this.client.get('/economics/metrics');
    return response.data;
  }

  // Organization endpoints
  async getOrganization(): Promise<any> {
    const response = await this.client.get('/organization');
    return response.data;
  }

  async getOrganizationMembers(): Promise<any> {
    const response = await this.client.get('/organization/members');
    return response.data;
  }

  async inviteOrganizationMember(email: string): Promise<any> {
    const response = await this.client.post('/organization/invite', { email });
    return response.data;
  }

  // Advanced attribution endpoints
  async getAttributionModels(): Promise<any> {
    const response = await this.client.get('/economics/attribution/models');
    return response.data;
  }

  async getAttributionAnalysis(): Promise<any> {
    const response = await this.client.get('/economics/attribution/analysis');
    return response.data;
  }

  async computeAttribution(config: any): Promise<any> {
    const response = await this.client.post('/economics/attribution/compute', config);
    return response.data;
  }

  // Live capture endpoints
  async getLiveCaptureStats(): Promise<any> {
    const response = await this.client.get('/live/monitor/status');
    const backendData = response.data;

    // Return backend data as-is, only extract known fields
    // NOTE: Frontend should handle missing fields gracefully
    if (backendData.success && backendData.status) {
      return {
        status: 'active',
        active_sessions: backendData.status.active_conversations || 0,
        // Only return fields that backend actually provides
        ...backendData.status,
      };
    }

    return response.data;
  }

  async getLiveCaptureConversations(): Promise<any> {
    const response = await this.client.get('/live/capture/conversations');
    return response.data;
  }

  async startLiveCaptureMonitor(config: any): Promise<any> {
    const response = await this.client.post('/live/monitor/start', config);
    return response.data;
  }

  async captureLiveMessage(message: any): Promise<any> {
    const response = await this.client.post('/live/capture/message', message);
    return response.data;
  }

  // Chain sealing endpoints
  async getChainSealsList(): Promise<any> {
    const response = await this.client.get('/chain/seals');
    const backendData = response.data;

    // Transform backend response to frontend expected format
    if (backendData.success && backendData.seals) {
      const seals = backendData.seals;
      return {
        seals: seals,
        total_chains: seals.length,
        verified_seals: seals.filter((seal: any) => seal.status === 'sealed' || seal.status === 'verified').length,
        pending_seals: seals.filter((seal: any) => seal.status === 'pending').length
      };
    }

    return response.data;
  }

  // Rights evolution endpoints
  async getRightsEvolutionHistory(modelId: string): Promise<any> {
    const response = await this.client.get(`/rights-evolution/evolution/models/${modelId}/history`);
    return response.data;
  }

  async getRightsEvolutionAlerts(): Promise<any> {
    const response = await this.client.get('/rights-evolution/evolution/alerts');
    return response.data;
  }

  async createCitizenshipApplication(data: any): Promise<any> {
    const response = await this.client.post('/bonds-citizenship/citizenship/applications', data);
    return response.data;
  }

  async getCitizenshipApplications(): Promise<any> {
    const response = await this.client.get('/bonds-citizenship/citizenship/applications');
    return response.data;
  }

  // Hallucination detection endpoints
  async detectHallucinations(request: { text: string; context?: string }): Promise<any> {
    const response = await this.client.post('/reasoning/hallucination-detection', request);
    return response.data;
  }

  async getHallucinationStats(): Promise<any> {
    const response = await this.client.get('/reasoning/hallucination-stats');
    return response.data;
  }

  async getUniverseVisualizationData(): Promise<any> {
    const response = await this.client.get('/universe/visualization-data');
    return response.data;
  }

  // Utility methods
  async ping(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }

  // Configuration methods
  updateConfig(config: Partial<AxiosRequestConfig>) {
    Object.assign(this.client.defaults, config);
  }

  getBaseURL(): string {
    return this.client.defaults.baseURL || '';
  }

  // AKC endpoints
  async getAKCSources(): Promise<any> {
    const response = await this.client.get('/akc/sources');
    return response.data;
  }

  async getAKCClusters(): Promise<any> {
    const response = await this.client.get('/akc/clusters');
    return response.data;
  }

  async getAKCStats(): Promise<any> {
    const response = await this.client.get('/akc/stats');
    return response.data;
  }

  // Mirror Mode endpoints
  // NOTE: Backend endpoints not implemented. These throw to prevent silent failures.
  async getMirrorModeConfig(): Promise<any> {
    throw new Error('Mirror mode API not implemented. Use demo mode toggle instead.');
  }

  async getMirrorModeAudits(): Promise<any> {
    throw new Error('Mirror mode API not implemented. Use demo mode toggle instead.');
  }

  // Payment endpoints
  async getPaymentMethods(): Promise<any> {
    const response = await this.client.get('/economics/payments');
    return response.data;
  }

  async getTransactions(): Promise<any> {
    const response = await this.client.get('/economics/transactions');
    return response.data;
  }

  // Compliance endpoints
  async getComplianceFrameworks(): Promise<any> {
    const response = await this.client.get('/compliance/frameworks');
    return response.data;
  }

  async getComplianceViolations(): Promise<any> {
    const response = await this.client.get('/compliance/violations');
    return response.data;
  }

  // Platform endpoints
  async getPlatforms(): Promise<any> {
    const response = await this.client.get('/platform');
    return response.data;
  }

  async getPlatformAPIKeys(): Promise<any> {
    const response = await this.client.get('/platform/keys');
    return response.data;
  }

  // Onboarding endpoints removed

  // Reasoning API methods
  async getReasoningChains(): Promise<any> {
    const response = await this.client.get('/reasoning/chains');
    return response.data;
  }

  async getReasoningStats(): Promise<any> {
    const response = await this.client.get('/reasoning/stats');
    return response.data;
  }

  async getReasoningSteps(chainId: string): Promise<any> {
    const response = await this.client.get(`/reasoning/chains/${chainId}/steps`);
    return response.data;
  }

  // Capsule Creation endpoints
  async createReasoningCapsule(request: {
    reasoning_trace: {
      query: string;
      steps: Array<{
        step_type: string;
        content: string;
        confidence: number;
        evidence: string[];
        metadata?: Record<string, any>;
      }>;
      conclusion: string;
      confidence_score: number;
      metadata?: Record<string, any>;
    };
    status?: string;
  }): Promise<any> {
    const response = await this.client.post('/capsules', request);
    return response.data;
  }

  async createGenericCapsule(capsuleData: AnyCapsule): Promise<any> {
    const response = await this.client.post('/capsules/generic', capsuleData);
    return response.data;
  }

  // Quick capsule creation for live conversations
  async createCapsuleFromConversation(sessionId: string, conversationData?: any): Promise<any> {
    const response = await this.client.post('/capsules/from-conversation', {
      session_id: sessionId,
      conversation_data: conversationData
    });
    return response.data;
  }

  // User Encryption Keys endpoints
  async getMyEncryptionKey(): Promise<{
    key: string;
    algorithm: string;
    key_id: string;
    usage: { encrypt: string; decrypt: string };
  }> {
    const response = await this.client.get('/user-keys/my-encryption-key');
    return response.data;
  }

  async getKeyInfo(): Promise<{
    key_id: string;
    algorithm: string;
    key_derivation: string;
    key_size_bits: number;
    iv_size_bits: number;
    tag_size_bits: number;
  }> {
    const response = await this.client.get('/user-keys/key-info');
    return response.data;
  }

  // Encrypted capsule creation
  async createEncryptedCapsule(capsuleData: {
    type: string;
    encrypted_payload: string;
    encryption_metadata: {
      iv: string;
      algorithm: string;
      key_id?: string;
    };
    payload?: Record<string, any>; // Optional minimal metadata
    verification?: any;
  }): Promise<any> {
    const response = await this.client.post('/capsules', capsuleData);
    return response.data;
  }

  // User-scoped export endpoints
  async exportMyCapsules(format: 'json' | 'jsonl' = 'json', includePayloads: boolean = true): Promise<any> {
    const response = await this.client.get('/export/my-capsules', {
      params: { format, include_payloads: includePayloads }
    });
    return response.data;
  }

  async getVerificationBundle(capsuleId: string): Promise<{
    capsule_id: string;
    capsule_type: string;
    version: string;
    timestamp: string;
    status: string;
    verification: {
      signature: string;
      verify_key: string;
      signer: string;
      hash: string;
      algorithm: string;
    };
    encryption: {
      is_encrypted: boolean;
      metadata: any;
    };
    bundle_generated_at: string;
    instructions: {
      verify: string;
      hash_algorithm: string;
      signature_algorithm: string;
    };
  }> {
    const response = await this.client.get(`/export/verification-bundle/${capsuleId}`);
    return response.data;
  }

  // Lineage endpoints
  async getCapsuleAncestors(capsuleId: string, depth?: number): Promise<{
    capsule_id: string;
    ancestors: string[];
    count: number;
    depth: number | null;
  }> {
    const response = await this.client.get(`/capsules/${capsuleId}/ancestors`, {
      params: depth ? { depth } : {}
    });
    return response.data;
  }

  async getCapsuleDescendants(capsuleId: string, depth?: number): Promise<{
    capsule_id: string;
    descendants: string[];
    count: number;
    depth: number | null;
  }> {
    const response = await this.client.get(`/capsules/${capsuleId}/descendants`, {
      params: depth ? { depth } : {}
    });
    return response.data;
  }

  async getCapsuleLineage(capsuleId: string): Promise<{
    capsule_id: string;
    lineage: string[];
    depth: number;
  }> {
    const response = await this.client.get(`/capsules/${capsuleId}/lineage`);
    return response.data;
  }

  async getChainCapsules(chainId: string): Promise<{
    chain_id: string;
    capsule_ids: string[];
    capsule_count: number;
    merkle_root: string | null;
  }> {
    const response = await this.client.get(`/chain/${chainId}/capsules`);
    return response.data;
  }

  async getChainSealerStatus(): Promise<{
    status: string;
    seals_dir: string;
    verify_key: string;
    seal_count: number;
  }> {
    const response = await this.client.get('/chain/status');
    return response.data;
  }

  // Admin endpoints
  async getAdminCapsuleStats(): Promise<{
    total_capsules: number;
    by_type: Record<string, number>;
    by_outcome: Record<string, number>;
    ownership: {
      total_owners: number;
      legacy_capsules: number;
      user_owned: number;
    };
    encryption: {
      encrypted_capsules: number;
      unencrypted_capsules: number;
    };
    recent_activity: {
      last_24h: number;
    };
    message: string;
  }> {
    const response = await this.client.get('/capsules/admin/stats');
    return response.data;
  }
}

// Default client instance
// SECURITY: Uses getApiBaseUrl() which enforces configuration in production
// API key only used if NEXT_PUBLIC_UATP_API_KEY is set (dev/demo only)
export const apiClient = new UATCapsuleEngineClient();

// Hook-friendly wrapper functions
export const api = {
  // Capsules
  getCapsules: (query?: ListCapsulesQuery) => apiClient.listCapsules(query),
  getCapsule: (id: string, query?: GetCapsuleQuery) => apiClient.getCapsule(id, query),
  createCapsule: (capsule: Partial<AnyCapsule>) => apiClient.createCapsule(capsule),
  verifyCapsule: (id: string) => apiClient.verifyCapsule(id),
  getCapsuleStats: (demoMode?: boolean) => apiClient.getCapsuleStats(demoMode),
  searchCapsules: (query: FullTextSearchQuery) => apiClient.searchCapsules(query),

  // Chain
  getChainSeals: () => apiClient.getChainSeals(),
  sealChain: (request: SealChainRequest) => apiClient.sealChain(request),
  verifySeal: (chainId: string, query: VerifySealQuery) => apiClient.verifySeal(chainId, query),

  // AI
  generateAI: (request: AIGenerateRequest) => apiClient.generateAI(request),

  // Trust
  getTrustStatus: (agentId: string) => apiClient.getTrustStatus(agentId),
  getTrustMetrics: () => apiClient.getTrustMetrics(),
  getTrustPolicies: () => apiClient.getTrustPolicies(),
  getRecentViolations: () => apiClient.getRecentViolations(),
  getQuarantinedAgents: () => apiClient.getQuarantinedAgents(),

  // Reasoning
  validateReasoning: (request: ReasoningAnalysisRequest) => apiClient.validateReasoning(request),
  analyzeReasoning: (request: ReasoningAnalysisRequest) => apiClient.analyzeReasoning(request),
  compareReasoning: (request: { traces: any[] }) => apiClient.compareReasoning(request),

  // Federation
  getFederationNodes: () => apiClient.getFederationNodes(),
  addFederationNode: (nodeData: { name: string; url: string; region: string }) => apiClient.addFederationNode(nodeData),
  getFederationStats: () => apiClient.getFederationStats(),
  syncFederationNode: (nodeId: string) => apiClient.syncFederationNode(nodeId),

  // Governance
  getProposals: () => apiClient.getProposals(),
  getProposal: (proposalId: string) => apiClient.getProposal(proposalId),
  createProposal: (proposalData: { title: string; description: string; category: string }) => apiClient.createProposal(proposalData),
  voteOnProposal: (proposalId: string, vote: 'for' | 'against' | 'abstain') => apiClient.voteOnProposal(proposalId, vote),
  getGovernanceStats: () => apiClient.getGovernanceStats(),

  // Analytics
  getAnalytics: () => apiClient.getAnalytics(),
  getEconomicMetrics: () => apiClient.getEconomicMetrics(),

  // Organization
  getOrganization: () => apiClient.getOrganization(),
  getOrganizationMembers: () => apiClient.getOrganizationMembers(),
  inviteOrganizationMember: (email: string) => apiClient.inviteOrganizationMember(email),

  // Advanced attribution
  getAttributionModels: () => apiClient.getAttributionModels(),
  getAttributionAnalysis: () => apiClient.getAttributionAnalysis(),
  computeAttribution: (config: any) => apiClient.computeAttribution(config),

  // Hallucination detection
  detectHallucinations: (request: { text: string; context?: string }) => apiClient.detectHallucinations(request),
  getHallucinationStats: () => apiClient.getHallucinationStats(),

  // Universe visualization
  getUniverseVisualizationData: () => apiClient.getUniverseVisualizationData(),

  // Live capture
  getLiveCaptureStats: () => apiClient.getLiveCaptureStats(),
  getLiveCaptureConversations: () => apiClient.getLiveCaptureConversations(),
  startLiveCaptureMonitor: (config: any) => apiClient.startLiveCaptureMonitor(config),
  captureLiveMessage: (message: any) => apiClient.captureLiveMessage(message),

  // Chain sealing
  getChainSealsList: () => apiClient.getChainSealsList(),

  // Rights evolution
  getRightsEvolutionHistory: (modelId: string) => apiClient.getRightsEvolutionHistory(modelId),
  getRightsEvolutionAlerts: () => apiClient.getRightsEvolutionAlerts(),
  createCitizenshipApplication: (data: any) => apiClient.createCitizenshipApplication(data),
  getCitizenshipApplications: () => apiClient.getCitizenshipApplications(),

  // System
  healthCheck: () => apiClient.healthCheck(),
  getCryptoStatus: () => apiClient.getCryptoStatus(),
  getMetrics: () => apiClient.getMetrics(),
  ping: () => apiClient.ping(),

  // Onboarding
  // Onboarding methods removed

  // Advanced Reasoning
  getReasoningChains: () => apiClient.getReasoningChains(),
  getReasoningStats: () => apiClient.getReasoningStats(),
  getReasoningSteps: (chainId: string) => apiClient.getReasoningSteps(chainId),

  // Capsule Creation
  createReasoningCapsule: (request: any) => apiClient.createReasoningCapsule(request),
  createGenericCapsule: (capsuleData: any) => apiClient.createGenericCapsule(capsuleData),
  createCapsuleFromConversation: (sessionId: string, conversationData?: any) => apiClient.createCapsuleFromConversation(sessionId, conversationData),

  // Authentication
  setAuthToken: (token: string) => apiClient.setAuthToken(token),
  removeAuthToken: () => apiClient.removeAuthToken(),
  hasAuthToken: () => apiClient.hasAuthToken(),

  // User Encryption Keys
  getMyEncryptionKey: () => apiClient.getMyEncryptionKey(),
  getKeyInfo: () => apiClient.getKeyInfo(),
  createEncryptedCapsule: (capsuleData: any) => apiClient.createEncryptedCapsule(capsuleData),

  // User-scoped Export
  exportMyCapsules: (format?: 'json' | 'jsonl', includePayloads?: boolean) => apiClient.exportMyCapsules(format, includePayloads),
  getVerificationBundle: (capsuleId: string) => apiClient.getVerificationBundle(capsuleId),

  // Admin
  getAdminCapsuleStats: () => apiClient.getAdminCapsuleStats(),

  // Lineage
  getCapsuleAncestors: (capsuleId: string, depth?: number) => apiClient.getCapsuleAncestors(capsuleId, depth),
  getCapsuleDescendants: (capsuleId: string, depth?: number) => apiClient.getCapsuleDescendants(capsuleId, depth),
  getCapsuleLineage: (capsuleId: string) => apiClient.getCapsuleLineage(capsuleId),
  getChainCapsules: (chainId: string) => apiClient.getChainCapsules(chainId),
  getChainSealerStatus: () => apiClient.getChainSealerStatus(),
};

export default apiClient;
