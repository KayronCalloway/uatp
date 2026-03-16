'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import {
  Vote,
  Users,
  Calendar,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Plus,
  MessageSquare,
  Scale,
  Shield,
  Gavel,
  Play
} from 'lucide-react';

interface Proposal {
  id: string;
  title: string;
  description: string;
  category: 'economic' | 'trust' | 'governance' | 'technical';
  status: 'active' | 'passed' | 'rejected' | 'pending';
  proposer: string;
  createdAt: string;
  votingEnds: string;
  votes: {
    for: number;
    against: number;
    abstain: number;
  };
  quorum: number;
  participationRate: number;
  comments: number;
}

interface VotingStats {
  activeProposals: number;
  totalVoters: number;
  averageParticipation: number;
  recentDecisions: number;
}

export function GovernanceDashboard() {
  const { isDemoMode } = useDemoMode();
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);
  const [showCreateProposal, setShowCreateProposal] = useState(false);
  const [newProposal, setNewProposal] = useState({
    title: '',
    description: '',
    category: 'governance' as const
  });

  // Fetch real data from API
  const { data: proposalsData, isLoading: proposalsLoading, error: proposalsError } = useQuery({
    queryKey: ['governance-proposals'],
    queryFn: api.getProposals,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: governanceStats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['governance-stats'],
    queryFn: api.getGovernanceStats,
    refetchInterval: 60000, // Refresh every minute
  });

  // Transform API data to match component interface
  const proposals: Proposal[] = proposalsData ? proposalsData.map((prop: any) => ({
    id: prop.proposal_id,
    title: prop.title,
    description: prop.description,
    category: prop.category,
    status: prop.status,
    proposer: prop.created_by,
    createdAt: prop.created_at,
    votingEnds: prop.voting_ends_at,
    votes: {
      for: prop.votes_for,
      against: prop.votes_against,
      abstain: prop.votes_abstain,
    },
    quorum: prop.quorum_required,
    participationRate: ((prop.votes_for + prop.votes_against + prop.votes_abstain) / prop.quorum_required) * 100,
    comments: 0 // Not available in API yet
  })) : [];

  const stats: VotingStats = governanceStats ? {
    activeProposals: governanceStats.active_proposals,
    totalVoters: governanceStats.unique_voters,
    averageParticipation: governanceStats.average_participation,
    recentDecisions: governanceStats.recent_activity?.last_7_days?.proposals_passed || 0
  } : {
    activeProposals: 0,
    totalVoters: 0,
    averageParticipation: 0,
    recentDecisions: 0
  };

  // Use real API data or show mock data only in demo mode
  const displayProposals = proposals.length > 0 ? proposals : (proposalsLoading ? [] : (isDemoMode ? [
    {
      id: 'prop-001',
      title: 'Adjust Trust Score Threshold for Economic Participation',
      description: 'Proposal to lower the minimum trust score required for economic participation from 0.85 to 0.80 to increase inclusion while maintaining security.',
      category: 'economic' as const,
      status: 'active' as const,
      proposer: 'governance-council',
      createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
      votingEnds: new Date(Date.now() + 86400000 * 4).toISOString(),
      votes: { for: 156, against: 23, abstain: 12 },
      quorum: 100,
      participationRate: 0.76,
      comments: 28
    },
    {
      id: 'prop-002',
      title: 'Implement Quarterly Trust Score Decay',
      description: 'Introduce a quarterly decay mechanism for trust scores to ensure active participation and prevent stagnation.',
      category: 'trust' as const,
      status: 'active' as const,
      proposer: 'trust-committee',
      createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
      votingEnds: new Date(Date.now() + 86400000 * 5).toISOString(),
      votes: { for: 89, against: 67, abstain: 15 },
      quorum: 100,
      participationRate: 0.68,
      comments: 42
    },
    {
      id: 'prop-003',
      title: 'Establish Multi-Node Federation Standards',
      description: 'Define technical and governance standards for federation between UATP instances across different organizations.',
      category: 'technical' as const,
      status: 'passed' as const,
      proposer: 'technical-committee',
      createdAt: new Date(Date.now() - 86400000 * 10).toISOString(),
      votingEnds: new Date(Date.now() - 86400000 * 3).toISOString(),
      votes: { for: 203, against: 18, abstain: 9 },
      quorum: 100,
      participationRate: 0.92,
      comments: 15
    },
    {
      id: 'prop-004',
      title: 'Increase Dividend Distribution Rate',
      description: 'Proposal to increase the common attribution fund dividend rate from 2% to 3% to better reward contributors.',
      category: 'economic' as const,
      status: 'rejected' as const,
      proposer: 'economic-council',
      createdAt: new Date(Date.now() - 86400000 * 15).toISOString(),
      votingEnds: new Date(Date.now() - 86400000 * 8).toISOString(),
      votes: { for: 78, against: 145, abstain: 22 },
      quorum: 100,
      participationRate: 0.98,
      comments: 67
    }
  ] : []));

  const getStatusIcon = (status: Proposal['status']) => {
    switch (status) {
      case 'active': return <Vote className="h-4 w-4 text-blue-600" />;
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'rejected': return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'pending': return <Clock className="h-4 w-4 text-gray-600" />;
      default: return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: Proposal['status']) => {
    switch (status) {
      case 'active': return 'bg-blue-100 text-blue-800';
      case 'passed': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category: Proposal['category']) => {
    switch (category) {
      case 'economic': return 'bg-yellow-100 text-yellow-800';
      case 'trust': return 'bg-purple-100 text-purple-800';
      case 'governance': return 'bg-indigo-100 text-indigo-800';
      case 'technical': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleVote = (proposalId: string, vote: 'for' | 'against' | 'abstain') => {
    // TODO: Implement voting via API
    // api.voteOnProposal(proposalId, vote);
  };

  const handleCreateProposal = () => {
    if (!newProposal.title || !newProposal.description) return;

    // TODO: Implement proposal creation via API
    // api.createProposal(newProposal);

    setNewProposal({ title: '', description: '', category: 'governance' });
    setShowCreateProposal(false);
  };

  const getVotePercentage = (votes: number, total: number) => {
    if (total === 0) return 0;
    return (votes / total) * 100;
  };

  const getTotalVotes = (proposal: Proposal) => {
    return proposal.votes.for + proposal.votes.against + proposal.votes.abstain;
  };

  return (
    <div className="space-y-6">
      {/* Header with Demo Mode Indicator */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Scale className="h-6 w-6 text-indigo-600" />
              <div>
                <h2 className="text-2xl font-bold">Governance Dashboard</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated governance proposals for demonstration'
                    : 'Democratic decision-making and proposal voting system'
                  }
                </p>
              </div>
              {isDemoMode && (
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                  <Play className="h-3 w-3 mr-1" />
                  Demo Data
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && displayProposals.length === 0 && !proposalsLoading && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Governance proposals will appear here when created. Toggle Demo Mode ON to see sample proposals.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Governance Overview - Only show if we have data */}
      {(displayProposals.length > 0 || proposalsLoading) && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Vote className="h-4 w-4 mr-2" />
              Active Proposals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold mb-1">{stats.activeProposals}</div>
            <p className="text-xs text-gray-500">Currently voting</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Users className="h-4 w-4 mr-2" />
              Eligible Voters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold mb-1">{stats.totalVoters}</div>
            <p className="text-xs text-gray-500">Qualified participants</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              Participation Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold mb-1">{(stats.averageParticipation * 100).toFixed(1)}%</div>
            <p className="text-xs text-gray-500">Average engagement</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Gavel className="h-4 w-4 mr-2" />
              Recent Decisions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold mb-1">{stats.recentDecisions}</div>
            <p className="text-xs text-gray-500">Past month</p>
          </CardContent>
        </Card>
      </div>
      )}

      {/* Proposals List - Only show if we have data */}
      {(displayProposals.length > 0 || proposalsLoading) && (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Scale className="h-5 w-5 mr-2" />
              Governance Proposals
            </CardTitle>
            <Button
              onClick={() => setShowCreateProposal(!showCreateProposal)}
              className="flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Proposal
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showCreateProposal && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium mb-3">Create New Proposal</h3>
              <div className="space-y-3">
                <Input
                  placeholder="Proposal title"
                  value={newProposal.title}
                  onChange={(e) => setNewProposal({...newProposal, title: e.target.value})}
                />
                <Textarea
                  placeholder="Detailed description of the proposal..."
                  value={newProposal.description}
                  onChange={(e) => setNewProposal({...newProposal, description: e.target.value})}
                  rows={4}
                />
                <select
                  className="w-full p-2 border rounded-md"
                  value={newProposal.category}
                  onChange={(e) => setNewProposal({...newProposal, category: e.target.value as any})}
                >
                  <option value="governance">Governance</option>
                  <option value="economic">Economic</option>
                  <option value="trust">Trust</option>
                  <option value="technical">Technical</option>
                </select>
                <div className="flex space-x-2">
                  <Button onClick={handleCreateProposal}>Submit Proposal</Button>
                  <Button variant="outline" onClick={() => setShowCreateProposal(false)}>Cancel</Button>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {displayProposals.map((proposal) => (
              <div
                key={proposal.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedProposal?.id === proposal.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                }`}
                onClick={() => setSelectedProposal(proposal)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(proposal.status)}
                    <h3 className="font-medium">{proposal.title}</h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getCategoryColor(proposal.category)}>
                      {proposal.category}
                    </Badge>
                    <Badge className={getStatusColor(proposal.status)}>
                      {proposal.status}
                    </Badge>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-3">{proposal.description}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span>Voting Progress</span>
                      <span>{getTotalVotes(proposal)} votes</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${getVotePercentage(proposal.votes.for, getTotalVotes(proposal))}%` }}
                          />
                        </div>
                        <span className="text-xs text-green-600">{proposal.votes.for} for</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-red-500 h-2 rounded-full"
                            style={{ width: `${getVotePercentage(proposal.votes.against, getTotalVotes(proposal))}%` }}
                          />
                        </div>
                        <span className="text-xs text-red-600">{proposal.votes.against} against</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Proposer:</span>
                      <span>{proposal.proposer}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Quorum:</span>
                      <span className={getTotalVotes(proposal) >= proposal.quorum ? 'text-green-600' : 'text-red-600'}>
                        {getTotalVotes(proposal)}/{proposal.quorum}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Participation:</span>
                      <span>{(proposal.participationRate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Comments:</span>
                      <span className="flex items-center">
                        <MessageSquare className="h-3 w-3 mr-1" />
                        {proposal.comments}
                      </span>
                    </div>
                  </div>
                </div>

                {proposal.status === 'active' && (
                  <div className="mt-4 pt-3 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">
                        Voting ends: {new Date(proposal.votingEnds).toLocaleDateString()}
                      </span>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          onClick={() => handleVote(proposal.id, 'for')}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Vote For
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleVote(proposal.id, 'against')}
                        >
                          Vote Against
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleVote(proposal.id, 'abstain')}
                        >
                          Abstain
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      )}

      {/* Selected Proposal Details */}
      {selectedProposal && (displayProposals.length > 0 || proposalsLoading) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Proposal Details: {selectedProposal.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Description</h4>
                <p className="text-gray-700">{selectedProposal.description}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">Voting Statistics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>For:</span>
                      <span className="font-medium text-green-600">{selectedProposal.votes.for}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Against:</span>
                      <span className="font-medium text-red-600">{selectedProposal.votes.against}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Abstain:</span>
                      <span className="font-medium text-gray-600">{selectedProposal.votes.abstain}</span>
                    </div>
                    <div className="flex justify-between font-medium">
                      <span>Total:</span>
                      <span>{getTotalVotes(selectedProposal)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Proposal Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <Badge className={getStatusColor(selectedProposal.status)}>
                        {selectedProposal.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Category:</span>
                      <Badge className={getCategoryColor(selectedProposal.category)}>
                        {selectedProposal.category}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Created:</span>
                      <span>{new Date(selectedProposal.createdAt).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Voting ends:</span>
                      <span>{new Date(selectedProposal.votingEnds).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
