/**
 * UATP JavaScript/TypeScript SDK - Federation Module
 * 
 * Provides global coordination and federation capabilities for planetary-scale UATP network.
 */

import { Timestamp } from './types';

export enum NodeStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SYNCING = 'syncing',
  MAINTENANCE = 'maintenance',
  UNREACHABLE = 'unreachable'
}

export enum NetworkHealth {
  HEALTHY = 'healthy',
  DEGRADED = 'degraded',
  CRITICAL = 'critical',
  PARTITIONED = 'partitioned'
}

export interface Node {
  nodeId: string;
  nodeName: string;
  endpoint: string;
  region: string;
  country: string;
  status: NodeStatus;
  lastSeen: Timestamp;

  // Network metrics
  latencyMs: number;
  throughputTps: number; // transactions per second
  reliabilityScore: number; // 0.0 to 1.0

  // Governance participation
  votingPower: number;
  governanceParticipation: number;

  // Economic metrics
  attributionsProcessed: number;
  rewardsDistributed: number;

  // Technical specifications
  version: string;
  capabilities: string[];
  supportedProtocols: string[];
}

export interface FederationMetrics {
  totalNodes: number;
  activeNodes: number;
  networkHealth: NetworkHealth;
  globalConsensusRate: number;
  averageLatencyMs: number;
  totalThroughputTps: number;

  // Geographic distribution
  nodesByRegion: Record<string, number>;
  nodesByCountry: Record<string, number>;

  // Economic metrics
  globalAttributionVolume: number;
  crossNodeTransactions: number;
  federationRewardsDistributed: number;

  // Governance metrics
  activeProposals: number;
  globalVotingParticipation: number;
  consensusProtocolsActive: string[];

  timestamp: Timestamp;
}

export interface JoinFederationOptions {
  nodeName: string;
  endpoint: string;
  region: string;
  country: string;
  capabilities: string[];
}

export interface SyncWithFederationOptions {
  targetNode?: string;
  syncType?: 'full' | 'incremental' | 'governance_only';
}

export interface SubmitGlobalProposalOptions {
  title: string;
  description: string;
  proposalType: string;
  impactRegions: string[];
  executionData: Record<string, any>;
}

export interface TriggerEmergencyProtocolOptions {
  protocolType: string;
  justification: string;
  durationHours: number;
}

/**
 * Client for interacting with the global UATP federation.
 */
export class FederationClient {
  private client: any;
  private federationNode: string;
  private nodeCache: Map<string, Node> = new Map();
  private metricsCache: Map<string, { data: any; timestamp: number }> = new Map();

  constructor(client: any, federationNode?: string) {
    this.client = client;
    this.federationNode = federationNode || 'global.uatp.network';
  }

  /**
   * Get current status of the global UATP federation network.
   */
  async getNetworkStatus(): Promise<FederationMetrics> {
    try {
      const response = await this.client.request('GET', '/api/v1/federation/network-status');
      const data = response.data;

      const metrics: FederationMetrics = {
        totalNodes: data.totalNodes || 0,
        activeNodes: data.activeNodes || 0,
        networkHealth: (data.networkHealth as NetworkHealth) || NetworkHealth.HEALTHY,
        globalConsensusRate: data.globalConsensusRate || 0.0,
        averageLatencyMs: data.averageLatencyMs || 0.0,
        totalThroughputTps: data.totalThroughputTps || 0.0,
        nodesByRegion: data.nodesByRegion || {},
        nodesByCountry: data.nodesByCountry || {},
        globalAttributionVolume: data.globalAttributionVolume || 0,
        crossNodeTransactions: data.crossNodeTransactions || 0,
        federationRewardsDistributed: data.federationRewardsDistributed || 0.0,
        activeProposals: data.activeProposals || 0,
        globalVotingParticipation: data.globalVotingParticipation || 0.0,
        consensusProtocolsActive: data.consensusProtocolsActive || [],
        timestamp: new Date().toISOString()
      };

      this.client.emit('network_status_retrieved', {
        activeNodes: metrics.activeNodes,
        totalNodes: metrics.totalNodes
      });

      return metrics;

    } catch (error) {
      console.error('Failed to get network status:', error);

      // Return fallback metrics
      return {
        totalNodes: 0,
        activeNodes: 0,
        networkHealth: NetworkHealth.CRITICAL,
        globalConsensusRate: 0.0,
        averageLatencyMs: 0.0,
        totalThroughputTps: 0.0,
        nodesByRegion: {},
        nodesByCountry: {},
        globalAttributionVolume: 0,
        crossNodeTransactions: 0,
        federationRewardsDistributed: 0.0,
        activeProposals: 0,
        globalVotingParticipation: 0.0,
        consensusProtocolsActive: [],
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get list of federation nodes, optionally filtered by region.
   */
  async getNodes(region?: string): Promise<Node[]> {
    try {
      const headers: Record<string, string> = {};
      if (region) {
        headers['X-Region-Filter'] = region;
      }

      const response = await this.client.request('GET', '/api/v1/federation/nodes', null, { headers });
      const data = response.data;
      const nodes: Node[] = [];

      for (const item of data.nodes || []) {
        const node: Node = {
          nodeId: item.nodeId,
          nodeName: item.nodeName,
          endpoint: item.endpoint,
          region: item.region,
          country: item.country,
          status: item.status as NodeStatus,
          lastSeen: item.lastSeen,
          latencyMs: item.latencyMs || 0.0,
          throughputTps: item.throughputTps || 0.0,
          reliabilityScore: item.reliabilityScore || 0.0,
          votingPower: item.votingPower || 0.0,
          governanceParticipation: item.governanceParticipation || 0.0,
          attributionsProcessed: item.attributionsProcessed || 0,
          rewardsDistributed: item.rewardsDistributed || 0.0,
          version: item.version || 'unknown',
          capabilities: item.capabilities || [],
          supportedProtocols: item.supportedProtocols || []
        };
        nodes.push(node);

        // Cache the node
        this.nodeCache.set(node.nodeId, node);
      }

      this.client.emit('federation_nodes_retrieved', { count: nodes.length });
      return nodes;

    } catch (error) {
      console.error('Failed to get federation nodes:', error);
      return [];
    }
  }

  /**
   * Get information about a specific federation node.
   */
  async getNode(nodeId: string): Promise<Node | null> {
    // Check cache first
    if (this.nodeCache.has(nodeId)) {
      return this.nodeCache.get(nodeId)!;
    }

    try {
      const response = await this.client.request('GET', `/api/v1/federation/nodes/${nodeId}`);
      const data = response.data;

      const node: Node = {
        nodeId: data.nodeId,
        nodeName: data.nodeName,
        endpoint: data.endpoint,
        region: data.region,
        country: data.country,
        status: data.status as NodeStatus,
        lastSeen: data.lastSeen,
        latencyMs: data.latencyMs || 0.0,
        throughputTps: data.throughputTps || 0.0,
        reliabilityScore: data.reliabilityScore || 0.0,
        votingPower: data.votingPower || 0.0,
        governanceParticipation: data.governanceParticipation || 0.0,
        attributionsProcessed: data.attributionsProcessed || 0,
        rewardsDistributed: data.rewardsDistributed || 0.0,
        version: data.version || 'unknown',
        capabilities: data.capabilities || [],
        supportedProtocols: data.supportedProtocols || []
      };

      // Cache the node
      this.nodeCache.set(nodeId, node);
      return node;

    } catch (error) {
      console.error(`Failed to get node ${nodeId}:`, error);
      return null;
    }
  }

  /**
   * Request to join the UATP federation as a new node.
   */
  async joinFederation(options: JoinFederationOptions): Promise<any> {
    const joinRequest = {
      nodeName: options.nodeName,
      endpoint: options.endpoint,
      region: options.region,
      country: options.country,
      capabilities: options.capabilities,
      version: '7.0',
      supportedProtocols: ['UATP', 'C2PA', 'zkDL++'],
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/federation/join', joinRequest);
      const result = response.data;

      this.client.emit('federation_join_requested', { requestId: result.requestId });
      return result;

    } catch (error) {
      console.error('Federation join request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        requestId: null
      };
    }
  }

  /**
   * Synchronize data with the federation network.
   */
  async syncWithFederation(options: SyncWithFederationOptions = {}): Promise<any> {
    const syncRequest = {
      targetNode: options.targetNode,
      syncType: options.syncType || 'full',
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/federation/sync', syncRequest);
      const result = response.data;

      this.client.emit('federation_sync_completed', { 
        recordsSynced: result.recordsSynced 
      });

      return result;

    } catch (error) {
      console.error('Federation sync failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        recordsSynced: 0
      };
    }
  }

  /**
   * Submit a proposal for global federation governance.
   */
  async submitGlobalProposal(options: SubmitGlobalProposalOptions): Promise<any> {
    const proposalRequest = {
      title: options.title,
      description: options.description,
      proposalType: options.proposalType,
      scope: 'global_federation',
      impactRegions: options.impactRegions,
      executionData: options.executionData,
      requiresSupermajority: ['constitutional', 'protocol_upgrade'].includes(options.proposalType),
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/federation/proposals', proposalRequest);
      const result = response.data;

      this.client.emit('global_proposal_submitted', { proposalId: result.proposalId });
      return result;

    } catch (error) {
      console.error('Global proposal submission failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        proposalId: null
      };
    }
  }

  /**
   * Get current consensus status across the federation.
   */
  async getConsensusStatus(): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/federation/consensus');
      return response.data;

    } catch (error) {
      console.error('Failed to get consensus status:', error);
      return {
        consensusReached: false,
        participatingNodes: 0,
        agreementPercentage: 0.0,
        pendingDecisions: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get crisis management status for the federation.
   */
  async getCrisisStatus(): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/federation/crisis-status');
      return response.data;

    } catch (error) {
      console.error('Failed to get crisis status:', error);
      return {
        crisisLevel: 'none',
        activeProtocols: [],
        emergencyMeasures: [],
        recoveryTimeline: null,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Trigger an emergency protocol across the federation.
   */
  async triggerEmergencyProtocol(options: TriggerEmergencyProtocolOptions): Promise<any> {
    const emergencyRequest = {
      protocolType: options.protocolType,
      justification: options.justification,
      durationHours: options.durationHours,
      requesterNode: this.federationNode,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/federation/emergency', emergencyRequest);
      const result = response.data;

      this.client.emit('emergency_protocol_triggered', { 
        protocolType: options.protocolType 
      });

      return result;

    } catch (error) {
      console.error('Emergency protocol trigger failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        protocolId: null
      };
    }
  }

  /**
   * Get statistics for a specific region in the federation.
   */
  async getRegionalStats(region: string): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/federation/regional-stats', null, {
        headers: { 'X-Region': region }
      });

      return response.data;

    } catch (error) {
      console.error(`Failed to get regional stats for ${region}:`, error);
      return {
        region,
        activeNodes: 0,
        totalNodes: 0,
        attributionVolume: 0,
        governanceParticipation: 0.0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Clear all cached federation data.
   */
  clearCache(): void {
    this.nodeCache.clear();
    this.metricsCache.clear();
    this.client.emit('federation_cache_cleared', {});
  }
}