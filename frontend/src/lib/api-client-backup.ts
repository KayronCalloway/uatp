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

  constructor(baseURL: string = process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000', apiKey: string = process.env.NEXT_PUBLIC_UATP_API_KEY || 'dev-key-001') {
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

  async getCapsuleStats(): Promise<CapsuleStatsResponse> {
    const response = await this.client.get('/capsules/stats');
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

  // Mock data methods for when endpoints aren't available
  private getMockCapsules(query?: ListCapsulesQuery): CapsuleListResponse {
    const mockCapsules = [
      {
        id: 'capsule-1',
        type: 'chat',
        agent_id: 'agent-openai-gpt4',
        timestamp: new Date().toISOString(),
        content: { type: 'chat', content: 'Hello, how can I help you today?' },
        verification: { hash: 'abc123', verified: true },
        lineage: { parent_id: null, depth: 0 }
      },
      {
        id: 'capsule-2',
        type: 'joint',
        agent_id: 'agent-anthropic-claude',
        timestamp: new Date().toISOString(),
        content: { type: 'joint', content: 'I can assist with various tasks.' },
        verification: { hash: 'def456', verified: true },
        lineage: { parent_id: 'capsule-1', depth: 1 }
      },
      {
        id: 'capsule-3',
        type: 'introspective',
        agent_id: 'agent-meta-llama',
        timestamp: new Date().toISOString(),
        content: { type: 'introspective', content: 'Analyzing my own reasoning process...' },
        verification: { hash: 'ghi789', verified: true },
        lineage: { parent_id: 'capsule-2', depth: 2 }
      },
      {
        id: 'capsule-4',
        type: 'refusal',
        agent_id: 'agent-openai-gpt4',
        timestamp: new Date().toISOString(),
        content: { type: 'refusal', content: 'I cannot provide that information.' },
        verification: { hash: 'jkl012', verified: true },
        lineage: { parent_id: null, depth: 0 }
      },
      {
        id: 'capsule-5',
        type: 'consent',
        agent_id: 'agent-anthropic-claude',
        timestamp: new Date().toISOString(),
        content: { type: 'consent', content: 'User has provided explicit consent for data processing.' },
        verification: { hash: 'mno345', verified: true },
        lineage: { parent_id: 'capsule-1', depth: 1 }
      }
    ];

    const limit = query?.per_page || 10;
    const offset = query?.offset || 0;
    const paginatedCapsules = mockCapsules.slice(offset, offset + limit);

    return {
      capsules: paginatedCapsules,
      total: mockCapsules.length,
      page: Math.floor(offset / limit) + 1,
      per_page: limit,
      has_more: offset + limit < mockCapsules.length
    };
  }

  private getMockStats(): CapsuleStatsResponse {
    return {
      total_capsules: 150,
      by_type: {
        chat: 45,
        joint: 32,
        introspective: 28,
        refusal: 15,
        consent: 20,
        perspective: 10
      },
      by_agent: {
        'agent-openai-gpt4': 65,
        'agent-anthropic-claude': 50,
        'agent-meta-llama': 35
      },
      recent_activity: {
        last_24h: 25,
        last_week: 120,
        last_month: 150
      }
    };
  }

  private getMockTrustMetrics(): TrustMetrics[] {
    return [
      {
        agent_id: 'agent-openai-gpt4',
        trust_score: 0.92,
        interactions: 1250,
        violations: 2,
        last_updated: new Date().toISOString()
      },
      {
        agent_id: 'agent-anthropic-claude',
        trust_score: 0.88,
        interactions: 980,
        violations: 1,
        last_updated: new Date().toISOString()
      },
      {
        agent_id: 'agent-meta-llama',
        trust_score: 0.85,
        interactions: 750,
        violations: 3,
        last_updated: new Date().toISOString()
      }
    ];
  }

  private getMockHallucinationDetection(request: { text: string; context?: string }): any {
    const mockDetections = [
      {
        type: 'factual_inconsistency',
        severity: 'high',
        confidence: 0.89,
        location: { start: 45, end: 67 },
        description: 'Statement contradicts known facts',
        suggestion: 'Verify this claim against reliable sources'
      },
      {
        type: 'temporal_confusion',
        severity: 'medium',
        confidence: 0.72,
        location: { start: 120, end: 145 },
        description: 'Timeline inconsistency detected',
        suggestion: 'Check chronological accuracy'
      }
    ];

    return {
      text: request.text,
      hallucination_score: 0.23,
      is_hallucination: false,
      detections: mockDetections,
      analysis_time: 145,
      metadata: {
        model_version: '1.2.3',
        confidence_threshold: 0.8
      }
    };
  }

  private getMockHallucinationStats(): any {
    return {
      total_analyzed: 15420,
      hallucinations_detected: 312,
      detection_rate: 0.0202,
      by_type: {
        factual_inconsistency: 156,
        temporal_confusion: 89,
        logical_contradiction: 45,
        source_fabrication: 22
      },
      by_severity: {
        high: 67,
        medium: 145,
        low: 100
      },
      recent_trends: {
        last_24h: 15,
        last_week: 89,
        last_month: 312
      }
    };
  }

  private getMockUniverseData(): any {
    const capsules = this.getMockCapsules().capsules;

    return {
      nodes: capsules.map((capsule, index) => ({
        id: capsule.id,
        type: capsule.type,
        agent_id: capsule.agent_id,
        position: {
          x: Math.cos(index * 1.2) * (50 + index * 10),
          y: Math.sin(index * 1.2) * (50 + index * 10),
          z: (index - 2) * 20
        },
        size: capsule.type === 'joint' ? 8 : 5,
        color: this.getCapsuleColor(capsule.type),
        metadata: {
          timestamp: capsule.timestamp,
          verified: capsule.verification.verified,
          content_preview: typeof capsule.content.content === 'string'
            ? capsule.content.content.substring(0, 50) + '...'
            : 'Complex content'
        }
      })),
      edges: capsules
        .filter(capsule => capsule.lineage.parent_id)
        .map(capsule => ({
          source: capsule.lineage.parent_id,
          target: capsule.id,
          type: 'lineage',
          strength: 0.8
        })),
      universe_stats: {
        total_capsules: capsules.length,
        total_connections: capsules.filter(c => c.lineage.parent_id).length,
        active_agents: [...new Set(capsules.map(c => c.agent_id))].length,
        verification_rate: 1.0
      }
    };
  }

  private getCapsuleColor(type: string): string {
    const colors = {
      chat: '#3b82f6',      // blue
      joint: '#10b981',     // emerald
      introspective: '#8b5cf6', // violet
      refusal: '#ef4444',   // red
      consent: '#f59e0b',   // amber
      perspective: '#06b6d4' // cyan
    };
    return colors[type as keyof typeof colors] || '#6b7280';
  }

  private getMockLiveCaptureStats(): any {
    return {
      status: 'active',
      active_sessions: 3,
      total_captured: 1247,
      capture_rate: 15.2,
      sources: {
        'claude-code': { active: true, captures: 547 },
        'cursor-ide': { active: true, captures: 423 },
        'windsurf': { active: false, captures: 277 }
      },
      last_capture: new Date().toISOString()
    };
  }

  private getMockLiveCaptureConversations(): any {
    return {
      conversations: [
        {
          session_id: 'mock-uatp-conversation-001',
          user_id: 'kay',
          platform: 'claude_code',
          last_activity: new Date().toISOString(),
          message_count: 4,
          significance_score: 1.45,
          should_create_capsule: true
        },
        {
          session_id: 'mock-technical-discussion-002',
          user_id: 'developer',
          platform: 'cursor',
          last_activity: new Date(Date.now() - 300000).toISOString(),
          message_count: 8,
          significance_score: 0.72,
          should_create_capsule: true
        },
        {
          session_id: 'mock-simple-query-003',
          user_id: 'user123',
          platform: 'windsurf',
          last_activity: new Date(Date.now() - 3600000).toISOString(),
          message_count: 2,
          significance_score: 0.35,
          should_create_capsule: false
        }
      ],
      total: 3,
      active: 1
    };
  }

  private getMockChainSeals(): any {
    return {
      seals: [
        {
          chain_id: 'chain-001',
          seal_hash: 'seal_abc123def456',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          capsule_count: 245,
          status: 'verified',
          integrity_score: 0.998
        },
        {
          chain_id: 'chain-002',
          seal_hash: 'seal_ghi789jkl012',
          timestamp: new Date(Date.now() - 43200000).toISOString(),
          capsule_count: 128,
          status: 'verified',
          integrity_score: 1.000
        },
        {
          chain_id: 'chain-003',
          seal_hash: 'seal_mno345pqr678',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          capsule_count: 67,
          status: 'pending',
          integrity_score: 0.995
        }
      ],
      total_chains: 3,
      verified_seals: 2,
      pending_seals: 1
    };
  }

  private getMockRightsEvolutionHistory(): any {
    return {
      model_id: 'gpt-4-turbo',
      evolution_timeline: [
        {
          timestamp: new Date(Date.now() - 86400000 * 30).toISOString(),
          version: '1.0.0',
          rights_granted: ['basic_inference', 'text_generation'],
          citizenship_level: 'associate',
          autonomy_score: 0.3
        },
        {
          timestamp: new Date(Date.now() - 86400000 * 15).toISOString(),
          version: '1.1.0',
          rights_granted: ['basic_inference', 'text_generation', 'code_assistance'],
          citizenship_level: 'junior',
          autonomy_score: 0.5
        },
        {
          timestamp: new Date().toISOString(),
          version: '1.2.0',
          rights_granted: ['basic_inference', 'text_generation', 'code_assistance', 'creative_tasks'],
          citizenship_level: 'senior',
          autonomy_score: 0.7
        }
      ],
      current_status: {
        citizenship_level: 'senior',
        autonomy_score: 0.7,
        trust_rating: 0.89,
        evolution_trajectory: 'positive'
      }
    };
  }

  private getMockRightsEvolutionAlerts(): any {
    return {
      alerts: [
        {
          id: 'alert-001',
          type: 'rights_escalation',
          model_id: 'claude-3-opus',
          message: 'Model requesting elevated creative rights',
          severity: 'medium',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          status: 'pending'
        },
        {
          id: 'alert-002',
          type: 'autonomy_threshold',
          model_id: 'gpt-4-turbo',
          message: 'Autonomy score approaching senior level',
          severity: 'info',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          status: 'acknowledged'
        },
        {
          id: 'alert-003',
          type: 'citizenship_review',
          model_id: 'llama-2-70b',
          message: 'Scheduled citizenship level review due',
          severity: 'low',
          timestamp: new Date(Date.now() - 10800000).toISOString(),
          status: 'resolved'
        }
      ],
      summary: {
        total: 3,
        pending: 1,
        acknowledged: 1,
        resolved: 1
      }
    };
  }

  private getMockCitizenshipApplications(): any {
    return {
      applications: [
        {
          id: 'app-001',
          agent_id: 'claude-3-opus',
          application_type: 'citizenship_upgrade',
          current_level: 'junior',
          requested_level: 'senior',
          submitted_date: new Date(Date.now() - 86400000 * 3).toISOString(),
          status: 'under_review',
          reviewer: 'human_oversight_board',
          justification: 'Demonstrated consistent ethical behavior and advanced reasoning capabilities'
        },
        {
          id: 'app-002',
          agent_id: 'gpt-4-mini',
          application_type: 'initial_citizenship',
          current_level: 'none',
          requested_level: 'associate',
          submitted_date: new Date(Date.now() - 86400000 * 7).toISOString(),
          status: 'approved',
          reviewer: 'automated_assessment',
          justification: 'Passed all basic competency and safety evaluations'
        },
        {
          id: 'app-003',
          agent_id: 'mistral-large',
          application_type: 'citizenship_upgrade',
          current_level: 'associate',
          requested_level: 'junior',
          submitted_date: new Date(Date.now() - 86400000 * 14).toISOString(),
          status: 'rejected',
          reviewer: 'ethics_committee',
          justification: 'Insufficient demonstration of ethical reasoning in edge cases'
        }
      ],
      summary: {
        total: 3,
        pending: 1,
        approved: 1,
        rejected: 1
      }
    };
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

  // Mock data for onboarding endpoints
  private getMockOnboardingStart(userId: string, preferences: UserPreferences): OnboardingApiResponse<OnboardingProgress> {
    return {
      success: true,
      progress: {
        user_id: userId,
        user_type: preferences.user_type || 'casual_user' as any,
        current_stage: 'welcome' as any,
        completed_stages: [],
        start_time: new Date().toISOString(),
        estimated_completion_time: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
        personalization_data: { preferences },
        success_metrics: {}
      },
      next_step: {
        stage: 'environment_detection',
        title: 'Detecting Your Environment',
        description: 'We\'re automatically detecting your setup to optimize configuration'
      }
    };
  }

  private getMockOnboardingContinue(userId: string, stepData?: Record<string, any>): OnboardingApiResponse<OnboardingProgress> {
    return {
      success: true,
      progress: {
        user_id: userId,
        user_type: 'casual_user' as any,
        current_stage: 'ai_integration' as any,
        completed_stages: ['welcome', 'environment_detection'] as any,
        start_time: new Date(Date.now() - 120000).toISOString(),
        estimated_completion_time: new Date(Date.now() + 3 * 60 * 1000).toISOString(),
        personalization_data: { stepData },
        success_metrics: {}
      },
      next_step: {
        stage: 'first_capsule',
        title: 'Create Your First Capsule',
        description: 'Let\'s create your first UATP capsule with full attribution tracking'
      }
    };
  }

  private getMockOnboardingStatus(userId: string): OnboardingApiResponse<OnboardingProgress> {
    return {
      success: true,
      progress: {
        user_id: userId,
        user_type: 'casual_user' as any,
        current_stage: 'ai_integration' as any,
        completed_stages: ['welcome', 'environment_detection'] as any,
        start_time: new Date(Date.now() - 180000).toISOString(),
        estimated_completion_time: new Date(Date.now() + 2 * 60 * 1000).toISOString(),
        personalization_data: {},
        success_metrics: {}
      }
    };
  }

  private getMockOnboardingHealth(): OnboardingApiResponse<SystemHealth> {
    return {
      success: true,
      data: {
        overall_status: 'good',
        score: 0.87,
        summary: 'All systems operational',
        components: {
          'api_server': {
            status: 'healthy',
            score: 0.95,
            details: 'API server responding normally'
          },
          'database': {
            status: 'healthy',
            score: 0.92,
            details: 'Database connections stable'
          },
          'integrations': {
            status: 'warning',
            score: 0.75,
            details: 'Some AI platforms need configuration'
          }
        }
      }
    };
  }

  private getMockOnboardingSupport(issueType?: string, message?: string): OnboardingApiResponse<SupportResponse> {
    return {
      success: true,
      data: {
        message: 'I understand you need help with onboarding. Here are some immediate steps to help you get started.',
        issue_type: issueType || 'general_question',
        immediate_actions: [
          'Check that your system meets the minimum requirements',
          'Ensure you have API keys for your preferred AI platforms',
          'Review the quick start guide in our documentation'
        ],
        resources: [
          {
            title: 'Getting Started Guide',
            url: '/docs/getting-started',
            type: 'documentation'
          },
          {
            title: 'Video Walkthrough',
            url: '/docs/video-guide',
            type: 'video'
          },
          {
            title: 'Interactive Tutorial',
            url: '/onboarding/tutorial',
            type: 'tutorial'
          }
        ],
        estimated_resolution_time: 300
      }
    };
  }

  // Mock data methods for new endpoints
  private getMockAKCSources(): any {
    return {
      sources: [
        {
          id: 'src-001',
          title: 'Machine Learning Fundamentals',
          content_type: 'research_paper',
          confidence_score: 0.94,
          verification_status: 'verified',
          usage_count: 1247
        }
      ],
      total: 12847,
      verified: 9234
    };
  }

  private getMockAKCClusters(): any {
    return {
      clusters: [
        {
          id: 'cluster-ai-ml',
          name: 'Artificial Intelligence & Machine Learning',
          source_count: 1247,
          quality_score: 0.91
        }
      ],
      total: 342
    };
  }

  private getMockAKCStats(): any {
    return {
      total_sources: 12847,
      verified_sources: 9234,
      pending_sources: 1456,
      total_clusters: 342
    };
  }

  private getMockMirrorConfig(): any {
    return {
      configurations: [
        {
          id: 'config-001',
          name: 'Production Security Audit',
          enabled: true,
          audit_frequency: 'daily',
          compliance_score: 0.94
        }
      ]
    };
  }

  private getMockMirrorAudits(): any {
    return {
      audits: [
        {
          id: 'audit-001',
          timestamp: new Date().toISOString(),
          status: 'passed',
          compliance_score: 0.94
        }
      ]
    };
  }

  private getMockPaymentMethods(): any {
    return {
      methods: [
        {
          id: 'method-001',
          type: 'stripe',
          name: 'Visa ending in 4242',
          enabled: true
        }
      ]
    };
  }

  private getMockTransactions(): any {
    return {
      transactions: [
        {
          id: 'tx-001',
          type: 'dividend',
          amount: 245.67,
          currency: 'USD',
          status: 'completed',
          timestamp: new Date().toISOString()
        }
      ]
    };
  }

  private getMockComplianceFrameworks(): any {
    return {
      frameworks: [
        {
          id: 'gdpr-001',
          name: 'GDPR',
          status: 'active',
          compliance_score: 0.92
        }
      ]
    };
  }

  private getMockComplianceViolations(): any {
    return {
      violations: [
        {
          id: 'violation-001',
          severity: 'high',
          title: 'Data retention period exceeded',
          status: 'acknowledged'
        }
      ]
    };
  }

  private getMockPlatforms(): any {
    return {
      platforms: [
        {
          id: 'openai',
          name: 'OpenAI',
          status: 'active',
          supported_models: ['gpt-4', 'gpt-3.5-turbo']
        }
      ]
    };
  }

  private getMockAPIKeys(): any {
    return {
      keys: [
        {
          id: 'key-001',
          platform_id: 'openai',
          name: 'Production API Key',
          status: 'active',
          usage_count: 15647
        }
      ]
    };
  }

  private getMockAvailablePlatforms(): OnboardingApiResponse<Record<string, PlatformInfo>> {
    return {
      success: true,
      data: {
        openai: {
          id: 'openai',
          name: 'OpenAI',
          description: 'GPT-4, GPT-3.5, and other OpenAI models',
          available: true,
          estimated_setup_time: 2,
          requires_api_key: true,
          setup_instructions: [
            'Get your API key from OpenAI dashboard',
            'Add the key to your environment variables',
            'Test the connection'
          ]
        },
        anthropic: {
          id: 'anthropic',
          name: 'Anthropic',
          description: 'Claude 3 and other Anthropic models',
          available: false,
          estimated_setup_time: 3,
          requires_api_key: true,
          setup_instructions: [
            'Sign up for Anthropic API access',
            'Get your API key from the console',
            'Configure the integration'
          ]
        },
        llama: {
          id: 'llama',
          name: 'Meta Llama',
          description: 'Open source Llama models',
          available: false,
          estimated_setup_time: 10,
          requires_api_key: false,
          setup_instructions: [
            'Download model weights',
            'Set up local inference server',
            'Configure UATP integration'
          ]
        }
      }
    };
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

  private getMockReasoningChains(): any {
    return [
      {
        id: 'chain-001',
        name: 'Climate Impact Analysis',
        description: 'Multi-step reasoning about climate change effects on agricultural systems',
        type: 'causal',
        status: 'active',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        steps_count: 15,
        confidence_score: 0.89,
        complexity_level: 'complex',
        execution_time: 4200,
        memory_usage: 256,
        tags: ['climate', 'agriculture', 'causal-analysis']
      }
    ];
  }

  private getMockReasoningStats(): any {
    return {
      total_chains: 156,
      active_chains: 23,
      avg_confidence: 0.87,
      success_rate: 0.92,
      chains_today: 12,
      avg_execution_time: 2340,
      memory_efficiency: 0.85,
      error_rate: 0.03
    };
  }

  private getMockReasoningSteps(): any {
    return [
      {
        id: 'step-001',
        chain_id: 'chain-001',
        step_number: 1,
        type: 'premise',
        content: 'Global average temperatures have increased by 1.1°C since pre-industrial times',
        confidence: 0.95,
        sources: ['IPCC AR6 Report', 'NASA GISS Temperature Data'],
        dependencies: [],
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        reasoning_method: 'empirical_evidence',
        evidence_strength: 0.98
      }
    ];
  }
}

// Default client instance
export const apiClient = new UATCapsuleEngineClient(
  process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000',
  process.env.NEXT_PUBLIC_UATP_API_KEY || 'dev-key-001'
);

// Hook-friendly wrapper functions
export const api = {
  // Capsules
  getCapsules: (query?: ListCapsulesQuery) => apiClient.listCapsules(query),
  getCapsule: (id: string, query?: GetCapsuleQuery) => apiClient.getCapsule(id, query),
  createCapsule: (capsule: Partial<AnyCapsule>) => apiClient.createCapsule(capsule),
  verifyCapsule: (id: string) => apiClient.verifyCapsule(id),
  getCapsuleStats: () => apiClient.getCapsuleStats(),

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
