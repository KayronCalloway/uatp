/**
 * Mock data utilities for demo mode
 * Provides realistic sample data for all dashboards when demo mode is enabled
 */

export interface LiveCaptureStats {
  status: string;
  active_sessions: number;
  total_captured: number;
  capture_rate: number;
  sources: Record<string, { active: boolean; captures: number }>;
  last_capture: string;
}

export interface LiveConversation {
  session_id: string;
  user_id: string;
  platform: string;
  last_activity: string;
  message_count: number;
  significance_score: number;
  should_create_capsule: boolean;
}

export interface LiveCaptureConversationsResponse {
  conversations: LiveConversation[];
  total: number;
}

/**
 * Generate mock live capture statistics
 */
export function getMockLiveCaptureStats(): LiveCaptureStats {
  return {
    status: 'active',
    active_sessions: 3,
    total_captured: 127,
    capture_rate: 2.4,
    sources: {
      'claude-code': { active: true, captures: 45 },
      'cursor-ide': { active: true, captures: 38 },
      'windsurf': { active: false, captures: 44 }
    },
    last_capture: new Date(Date.now() - 120000).toISOString() // 2 minutes ago
  };
}

/**
 * Generate mock live conversations
 */
export function getMockLiveConversations(): LiveCaptureConversationsResponse {
  const conversations: LiveConversation[] = [
    {
      session_id: 'session-demo-001-claude-code-capture',
      user_id: 'demo-user-alice',
      platform: 'Claude Code',
      last_activity: new Date(Date.now() - 30000).toISOString(), // 30 seconds ago
      message_count: 24,
      significance_score: 0.85,
      should_create_capsule: true
    },
    {
      session_id: 'session-demo-002-cursor-ide-capture',
      user_id: 'demo-user-bob',
      platform: 'Cursor IDE',
      last_activity: new Date(Date.now() - 180000).toISOString(), // 3 minutes ago
      message_count: 15,
      significance_score: 0.72,
      should_create_capsule: true
    },
    {
      session_id: 'session-demo-003-windsurf-capture',
      user_id: 'demo-user-carol',
      platform: 'Windsurf',
      last_activity: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago
      message_count: 8,
      significance_score: 0.45,
      should_create_capsule: false
    }
  ];

  return {
    conversations,
    total: conversations.length
  };
}

/**
 * Generate mock capsule data
 */
export function getMockCapsules() {
  return [
    {
      id: 'demo-capsule-001',
      capsule_id: 'demo-capsule-001',
      capsule_type: 'conversation',
      agent_id: 'claude-code-demo',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      confidence: 0.92,
      reasoning_trace: [
        'User initiated code review session',
        'Multiple file changes detected',
        'Applied UATP attribution metadata'
      ],
      metadata: {
        platform: 'Claude Code',
        session_length: '45 minutes',
        significance: 'high'
      },
      previous_capsule_id: null,
      signature: 'demo-sig-001',
      verified: true
    },
    {
      id: 'demo-capsule-002',
      capsule_id: 'demo-capsule-002',
      capsule_type: 'attribution',
      agent_id: 'cursor-demo',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      confidence: 0.88,
      reasoning_trace: [
        'Code generation detected',
        'AI contribution analyzed',
        'Attribution weights calculated'
      ],
      metadata: {
        platform: 'Cursor IDE',
        lines_generated: 234,
        significance: 'medium'
      },
      previous_capsule_id: 'demo-capsule-001',
      signature: 'demo-sig-002',
      verified: true
    }
  ];
}

/**
 * Generate mock trust metrics
 */
export function getMockTrustMetrics() {
  return {
    overall_score: 87.5,
    verification_rate: 0.94,
    signature_validity: 0.98,
    chain_integrity: 0.92,
    recent_violations: 0,
    trust_level: 'high'
  };
}

/**
 * Generate mock system health
 */
export function getMockSystemHealth() {
  return {
    status: 'healthy',
    uptime: 342156, // ~4 days in seconds
    capsules_processed: 1247,
    active_connections: 8,
    cpu_usage: 23.5,
    memory_usage: 45.2,
    last_backup: new Date(Date.now() - 14400000).toISOString() // 4 hours ago
  };
}

/**
 * Generate mock chain seals
 */
export function getMockChainSeals() {
  return {
    seals: [
      {
        seal_id: 'seal-demo-001',
        chain_id: 'main-chain',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        capsule_count: 156,
        merkle_root: 'demo-merkle-root-001',
        signature: 'demo-seal-sig-001',
        verified: true
      },
      {
        seal_id: 'seal-demo-002',
        chain_id: 'main-chain',
        timestamp: new Date(Date.now() - 172800000).toISOString(),
        capsule_count: 142,
        merkle_root: 'demo-merkle-root-002',
        signature: 'demo-seal-sig-002',
        verified: true
      }
    ],
    total: 2,
    latest_seal: 'seal-demo-001'
  };
}

/**
 * Generate mock economic data
 */
export function getMockEconomicData() {
  return {
    total_value_distributed: 15420.50,
    active_contributors: 34,
    pending_payouts: 2340.75,
    average_payout: 453.25,
    top_contributors: [
      { agent_id: 'claude-code-001', contribution: 4250.00, capsules: 89 },
      { agent_id: 'cursor-ai-002', contribution: 3180.50, capsules: 67 },
      { agent_id: 'windsurf-003', contribution: 2890.25, capsules: 58 }
    ]
  };
}

/**
 * Generate mock reasoning analysis
 */
export function getMockReasoningAnalysis() {
  return {
    analysis_id: 'demo-analysis-001',
    step_count: 12,
    average_confidence: 0.87,
    coherence_score: 0.91,
    logical_flow: 'strong',
    identified_patterns: [
      'Sequential reasoning',
      'Evidence-based conclusions',
      'Multi-step verification'
    ],
    suggestions: [
      'Consider adding intermediate validation steps',
      'Expand context for edge cases'
    ]
  };
}

/**
 * Generate mock health check data
 */
export function getMockHealthCheck() {
  return {
    status: 'healthy',
    version: '7.0.0-alpha',
    uptime: 342156,
    timestamp: new Date().toISOString(),
    database: 'connected',
    storage: 'operational'
  };
}

/**
 * Generate mock capsule statistics
 */
export function getMockCapsuleStats() {
  return {
    total_capsules: 1247,
    unique_agents: 23,
    types: {
      'conversation': 456,
      'attribution': 324,
      'reasoning': 289,
      'joint': 178
    },
    recent_activity: {
      last_24h: 47,
      last_7d: 298,
      last_30d: 1124
    },
    average_confidence: 0.87
  };
}

/**
 * Generate mock trust metrics (different from getMockTrustMetrics for consistency)
 */
export function getMockTrustMetricsData() {
  return {
    overall_score: 87.5,
    verification_rate: 0.94,
    signature_validity: 0.98,
    chain_integrity: 0.92,
    recent_violations: 0,
    trust_level: 'high',
    verified_capsules: 1173,
    total_capsules: 1247
  };
}

/**
 * Generate mock trust policies
 */
export function getMockTrustPolicies() {
  return {
    policies: [
      {
        id: 'policy-001',
        name: 'Signature Verification',
        description: 'All capsules must have valid cryptographic signatures',
        enabled: true,
        severity: 'critical',
        violations: 0
      },
      {
        id: 'policy-002',
        name: 'Chain Integrity',
        description: 'Capsule chain must maintain proper ordering and references',
        enabled: true,
        severity: 'high',
        violations: 0
      },
      {
        id: 'policy-003',
        name: 'Attribution Accuracy',
        description: 'Attribution data must be verifiable and accurate',
        enabled: true,
        severity: 'medium',
        violations: 2
      }
    ],
    total_policies: 3,
    active_policies: 3
  };
}

/**
 * Generate mock recent violations
 */
export function getMockRecentViolations() {
  return {
    violations: [
      {
        id: 'viol-001',
        agent_id: 'agent-003',
        violation_type: 'attribution_mismatch',
        severity: 'medium',
        timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        description: 'Attribution data does not match capsule content',
        status: 'resolved',
        resolution: 'Agent re-submitted with corrected attribution'
      },
      {
        id: 'viol-002',
        agent_id: 'agent-005',
        violation_type: 'signature_invalid',
        severity: 'high',
        timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        description: 'Capsule signature validation failed',
        status: 'pending_review',
        resolution: null
      }
    ],
    total_violations: 2,
    pending_violations: 1,
    resolved_violations: 1
  };
}

/**
 * Generate mock quarantined agents
 */
export function getMockQuarantinedAgents() {
  return {
    quarantined_agents: [
      {
        agent_id: 'agent-003',
        reason: 'Multiple attribution violations',
        quarantined_at: new Date(Date.now() - 10800000).toISOString(), // 3 hours ago
        violation_count: 3,
        severity: 'medium',
        status: 'under_review',
        expected_release: new Date(Date.now() + 82800000).toISOString() // 23 hours from now
      }
    ],
    total_quarantined: 1,
    total_violations: 3
  };
}

/**
 * Simulate API delay for realistic demo mode experience
 */
export async function simulateApiDelay(minMs: number = 200, maxMs: number = 800): Promise<void> {
  const delay = Math.random() * (maxMs - minMs) + minMs;
  return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * Generic mock API response wrapper
 */
export async function mockApiCall<T>(data: T): Promise<T> {
  await simulateApiDelay();
  return data;
}
