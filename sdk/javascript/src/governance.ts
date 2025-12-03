/**
 * UATP JavaScript/TypeScript SDK - Governance Module
 * 
 * Provides democratic governance participation capabilities for UATP network decisions.
 */

import { Timestamp, UUID } from './types';

export enum ProposalStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  VOTING = 'voting',
  PASSED = 'passed',
  REJECTED = 'rejected',
  EXECUTED = 'executed',
  EXPIRED = 'expired'
}

export enum VoteChoice {
  APPROVE = 'approve',
  REJECT = 'reject',
  ABSTAIN = 'abstain'
}

export interface Proposal {
  proposalId: string;
  title: string;
  description: string;
  proposerId: string;
  proposalType: 'constitutional' | 'economic' | 'technical' | 'social';
  status: ProposalStatus;
  votingStart: Timestamp;
  votingEnd: Timestamp;
  requiredQuorum: number;
  requiredMajority: number;

  // Voting results
  votesApprove: number;
  votesReject: number;
  votesAbstain: number;
  totalVotingPower: number;

  // Execution details
  executionData?: Record<string, any>;
  impactAssessment?: Record<string, any>;

  createdAt: Timestamp;
  updatedAt: Timestamp;

  // Computed properties
  readonly totalVotes: number;
  readonly approvalPercentage: number;
  readonly isActive: boolean;
}

export interface Vote {
  voteId: string;
  proposalId: string;
  voterId: string;
  choice: VoteChoice;
  votingPower: number;
  reasoning?: string;
  timestamp: Timestamp;
}

export interface CreateProposalOptions {
  title: string;
  description: string;
  proposalType: 'constitutional' | 'economic' | 'technical' | 'social';
  executionData?: Record<string, any>;
  votingDurationHours?: number;
}

export interface CastVoteOptions {
  proposalId: string;
  choice: VoteChoice | string;
  reasoning?: string;
}

export interface DelegateVotingPowerOptions {
  delegateTo: string;
  amount?: number;
}

/**
 * Client for participating in UATP democratic governance.
 */
export class GovernanceClient {
  private client: any;
  private proposalCache: Map<string, Proposal> = new Map();
  private userVotes: Map<string, Map<string, Vote>> = new Map();

  constructor(client: any) {
    this.client = client;
  }

  /**
   * Get all currently active proposals for voting.
   */
  async getActiveProposals(): Promise<Proposal[]> {
    try {
      const response = await this.client.request('GET', '/api/v1/governance/proposals/active');
      const data = response.data;
      const proposals: Proposal[] = [];

      for (const item of data.proposals || []) {
        const proposal = this.createProposalFromData(item);
        proposals.push(proposal);
        this.proposalCache.set(proposal.proposalId, proposal);
      }

      this.client.emit('active_proposals_retrieved', { count: proposals.length });
      return proposals;

    } catch (error) {
      console.error('Failed to get active proposals:', error);
      return [];
    }
  }

  /**
   * Get a specific proposal by ID.
   */
  async getProposal(proposalId: string): Promise<Proposal | null> {
    // Check cache first
    if (this.proposalCache.has(proposalId)) {
      return this.proposalCache.get(proposalId)!;
    }

    try {
      const response = await this.client.request('GET', `/api/v1/governance/proposals/${proposalId}`);
      const data = response.data;

      const proposal = this.createProposalFromData(data);
      this.proposalCache.set(proposalId, proposal);
      return proposal;

    } catch (error) {
      console.error(`Failed to get proposal ${proposalId}:`, error);
      return null;
    }
  }

  private createProposalFromData(data: any): Proposal {
    const proposal = {
      proposalId: data.proposalId,
      title: data.title,
      description: data.description,
      proposerId: data.proposerId,
      proposalType: data.proposalType,
      status: data.status as ProposalStatus,
      votingStart: data.votingStart,
      votingEnd: data.votingEnd,
      requiredQuorum: data.requiredQuorum,
      requiredMajority: data.requiredMajority,
      votesApprove: data.votesApprove || 0,
      votesReject: data.votesReject || 0,
      votesAbstain: data.votesAbstain || 0,
      totalVotingPower: data.totalVotingPower || 0,
      executionData: data.executionData,
      impactAssessment: data.impactAssessment,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt,

      // Computed properties
      get totalVotes(): number {
        return this.votesApprove + this.votesReject + this.votesAbstain;
      },

      get approvalPercentage(): number {
        if (this.totalVotes === 0) return 0;
        return (this.votesApprove / this.totalVotes) * 100;
      },

      get isActive(): boolean {
        const now = new Date();
        const votingStart = new Date(this.votingStart);
        const votingEnd = new Date(this.votingEnd);
        return (
          this.status === ProposalStatus.VOTING &&
          votingStart <= now &&
          now <= votingEnd
        );
      }
    } as Proposal;

    return proposal;
  }

  /**
   * Cast a vote on a governance proposal.
   */
  async castVote(proposalId: string, choice: VoteChoice | string, reasoning?: string): Promise<any> {
    // Normalize vote choice
    let voteChoice: VoteChoice;
    if (typeof choice === 'string') {
      const normalizedChoice = choice.toLowerCase() as VoteChoice;
      if (!Object.values(VoteChoice).includes(normalizedChoice)) {
        throw new Error(`Invalid vote choice: ${choice}. Must be 'approve', 'reject', or 'abstain'`);
      }
      voteChoice = normalizedChoice;
    } else {
      voteChoice = choice;
    }

    const voteRequest = {
      proposalId,
      choice: voteChoice,
      reasoning,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/governance/votes', voteRequest);
      const result = response.data;

      // Create vote record
      const vote: Vote = {
        voteId: result.voteId,
        proposalId,
        voterId: result.voterId,
        choice: voteChoice,
        votingPower: result.votingPower,
        reasoning,
        timestamp: new Date().toISOString()
      };

      // Cache user's vote
      if (!this.userVotes.has(result.voterId)) {
        this.userVotes.set(result.voterId, new Map());
      }
      this.userVotes.get(result.voterId)!.set(proposalId, vote);

      // Clear proposal cache to force refresh
      this.proposalCache.delete(proposalId);

      this.client.emit('vote_cast', { proposalId, choice: voteChoice });

      return {
        success: true,
        voteId: result.voteId,
        votingPower: result.votingPower,
        confirmation: result.confirmation,
        vote
      };

    } catch (error) {
      console.error(`Failed to cast vote on proposal ${proposalId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        voteId: null
      };
    }
  }

  /**
   * Create a new governance proposal.
   */
  async createProposal(options: CreateProposalOptions): Promise<any> {
    const proposalRequest = {
      title: options.title,
      description: options.description,
      proposalType: options.proposalType,
      executionData: options.executionData,
      votingDurationHours: options.votingDurationHours || 168, // 1 week default
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/governance/proposals', proposalRequest);
      const result = response.data;

      this.client.emit('proposal_created', { proposalId: result.proposalId });
      return result;

    } catch (error) {
      console.error('Failed to create proposal:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        proposalId: null
      };
    }
  }

  /**
   * Get voting history for a user.
   */
  async getUserVotes(userId: string, limit: number = 50): Promise<Vote[]> {
    try {
      const response = await this.client.request('GET', '/api/v1/governance/votes/user', null, {
        headers: {
          'X-User-ID': userId,
          'X-Limit': limit.toString()
        }
      });

      const data = response.data;
      const votes: Vote[] = [];

      for (const item of data.votes || []) {
        const vote: Vote = {
          voteId: item.voteId,
          proposalId: item.proposalId,
          voterId: item.voterId,
          choice: item.choice as VoteChoice,
          votingPower: item.votingPower,
          reasoning: item.reasoning,
          timestamp: item.timestamp
        };
        votes.push(vote);
      }

      return votes;

    } catch (error) {
      console.error(`Failed to get user votes for ${userId}:`, error);
      return [];
    }
  }

  /**
   * Get overall governance statistics.
   */
  async getGovernanceStats(): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/governance/stats');
      return response.data;

    } catch (error) {
      console.error('Failed to get governance stats:', error);
      return {
        totalProposals: 0,
        activeProposals: 0,
        totalVoters: 0,
        participationRate: 0,
        proposalsByType: {},
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get a user's voting power and eligibility.
   */
  async getVotingPower(userId: string): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/governance/voting-power', null, {
        headers: { 'X-User-ID': userId }
      });

      return response.data;

    } catch (error) {
      console.error(`Failed to get voting power for user ${userId}:`, error);
      return {
        userId,
        votingPower: 0,
        eligible: false,
        requirements: {},
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Delegate voting power to another user.
   */
  async delegateVotingPower(options: DelegateVotingPowerOptions): Promise<any> {
    const delegationRequest = {
      delegateTo: options.delegateTo,
      amount: options.amount,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/governance/delegate', delegationRequest);
      const result = response.data;

      this.client.emit('voting_power_delegated', { delegateTo: options.delegateTo });
      return result;

    } catch (error) {
      console.error(`Failed to delegate voting power to ${options.delegateTo}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get the current constitutional framework of UATP.
   */
  async getConstitutionalFramework(): Promise<any> {
    try {
      const response = await this.client.request('GET', '/api/v1/governance/constitution');
      return response.data;

    } catch (error) {
      console.error('Failed to get constitutional framework:', error);
      return {
        principles: [],
        articles: {},
        amendmentProcess: {},
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Clear all cached governance data.
   */
  clearCache(): void {
    this.proposalCache.clear();
    this.userVotes.clear();
    this.client.emit('governance_cache_cleared', {});
  }
}