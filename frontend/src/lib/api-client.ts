import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import {
  CapsuleListResponse,
  CompressedCapsuleListResponse,
  ListCapsulesQuery,
  GetCapsuleQuery,
  CapsuleDetailResponse,
  CapsuleStatsResponse,
  VerificationResponse,
  HealthCheckResponse,
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
} from '@/types/api';
import {
  OnboardingProgress,
  OnboardingApiResponse,
  UserPreferences,
  PlatformInfo,
  SystemHealth,
  SupportResponse
} from '@/types/onboarding';

export class UATCapsuleEngineClient {
  private client: AxiosInstance;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000', apiKey: string = process.env.NEXT_PUBLIC_UATP_API_KEY || 'test-api-key') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'X-API-Key': apiKey }),
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API request failed:', error.config?.url, error.response?.status || error.code);

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

  // Core endpoints
  async getIndex(): Promise<IndexResponse> {
    const response = await this.client.get('/');
    return response.data;
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async healthCheckDetailed(): Promise<HealthCheckResponse> {
    const response = await this.client.get('/health/detailed');
    return response.data;
  }

  async getRecentActivity(): Promise<any> {
    const response = await this.client.get('/health/activity');
    return response.data;
  }

  async getHealthMetrics(): Promise<any> {
    const response = await this.client.get('/health/metrics');
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
    const response = await this.client.get('/attribution/models');
    return response.data;
  }

  async getAttributionAnalysis(): Promise<any> {
    const response = await this.client.get('/attribution/analysis');
    return response.data;
  }

  async computeAttribution(config: any): Promise<any> {
    const response = await this.client.post('/attribution/compute', config);
    return response.data;
  }

  // Live capture endpoints
  async getLiveCaptureStats(): Promise<any> {
    const response = await this.client.get('/api/v1/live/monitor/status');
    const backendData = response.data;

    // Transform backend response to frontend expected format
    if (backendData.success && backendData.status) {
      return {
        status: 'active',
        active_sessions: backendData.status.active_conversations || 0,
        total_captured: 0, // Backend doesn't track this yet
        capture_rate: 0.0, // Backend doesn't track this yet
        sources: {
          'live-monitor': {
            active: true,
            captures: 0
          }
        },
        last_capture: new Date().toISOString()
      };
    }

    return response.data;
  }

  async getLiveCaptureConversations(): Promise<any> {
    const response = await this.client.get('/api/v1/live/capture/conversations');
    return response.data;
  }

  async startLiveCaptureMonitor(config: any): Promise<any> {
    const response = await this.client.post('/api/v1/live/monitor/start', config);
    return response.data;
  }

  async captureLiveMessage(message: any): Promise<any> {
    const response = await this.client.post('/api/v1/live/capture/message', message);
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
  async getMirrorModeConfig(): Promise<any> {
    const response = await this.client.get('/api/v1/mirror/config');
    return response.data;
  }

  async getMirrorModeAudits(): Promise<any> {
    const response = await this.client.get('/api/v1/mirror/audits');
    return response.data;
  }

  // Payment endpoints
  async getPaymentMethods(): Promise<any> {
    const response = await this.client.get('/payments');
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

  // Onboarding endpoints
  async startOnboarding(userId: string, preferences: UserPreferences): Promise<OnboardingApiResponse<OnboardingProgress>> {
    const response = await this.client.post('/onboarding/api/start', {
      user_id: userId,
      preferences
    });
    return response.data;
  }

  async continueOnboarding(userId: string, stepData?: Record<string, any>): Promise<OnboardingApiResponse<OnboardingProgress>> {
    const response = await this.client.post('/onboarding/api/continue', {
      user_id: userId,
      step_data: stepData || {}
    });
    return response.data;
  }

  async getOnboardingStatus(userId: string): Promise<OnboardingApiResponse<OnboardingProgress>> {
    const response = await this.client.get(`/onboarding/api/status/${userId}`);
    return response.data;
  }

  async getOnboardingSystemHealth(): Promise<OnboardingApiResponse<SystemHealth>> {
    const response = await this.client.get('/onboarding/api/health');
    return response.data;
  }

  async getOnboardingSupport(userId?: string, issueType?: string, message?: string): Promise<OnboardingApiResponse<SupportResponse>> {
    const response = await this.client.post('/onboarding/api/support', {
      user_id: userId,
      issue_type: issueType,
      message
    });
    return response.data;
  }

  async getAvailablePlatforms(): Promise<OnboardingApiResponse<Record<string, PlatformInfo>>> {
    const response = await this.client.get('/onboarding/api/platforms');
    return response.data;
  }

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
}

// Default client instance
export const apiClient = new UATCapsuleEngineClient(
  process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000',
  process.env.NEXT_PUBLIC_UATP_API_KEY || 'test-api-key'
);

// Hook-friendly wrapper functions
export const api = {
  // Capsules
  getCapsules: (query?: ListCapsulesQuery) => apiClient.listCapsules(query),
  getCapsule: (id: string, query?: GetCapsuleQuery) => apiClient.getCapsule(id, query),
  createCapsule: (capsule: Partial<AnyCapsule>) => apiClient.createCapsule(capsule),
  verifyCapsule: (id: string) => apiClient.verifyCapsule(id),
  getCapsuleStats: (demoMode?: boolean) => apiClient.getCapsuleStats(demoMode),

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
  getMetrics: () => apiClient.getMetrics(),
  ping: () => apiClient.ping(),

  // Onboarding
  startOnboarding: (userId: string, preferences: UserPreferences) => apiClient.startOnboarding(userId, preferences),
  continueOnboarding: (userId: string, stepData?: Record<string, any>) => apiClient.continueOnboarding(userId, stepData),
  getOnboardingStatus: (userId: string) => apiClient.getOnboardingStatus(userId),
  getOnboardingSystemHealth: () => apiClient.getOnboardingSystemHealth(),
  getOnboardingSupport: (userId?: string, issueType?: string, message?: string) => apiClient.getOnboardingSupport(userId, issueType, message),
  getAvailablePlatforms: () => apiClient.getAvailablePlatforms(),

  // Advanced Reasoning
  getReasoningChains: () => apiClient.getReasoningChains(),
  getReasoningStats: () => apiClient.getReasoningStats(),
  getReasoningSteps: (chainId: string) => apiClient.getReasoningSteps(chainId),

  // Capsule Creation
  createReasoningCapsule: (request: any) => apiClient.createReasoningCapsule(request),
  createGenericCapsule: (capsuleData: any) => apiClient.createGenericCapsule(capsuleData),
  createCapsuleFromConversation: (sessionId: string, conversationData?: any) => apiClient.createCapsuleFromConversation(sessionId, conversationData),
};

export default apiClient;
