'use client';

import { useState } from 'react';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { logger } from '@/lib/logger';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Building,
  Users,
  UserPlus,
  Settings,
  Crown,
  Shield,
  TrendingUp,
  Plus,
  Edit,
  Trash2,
  Mail,
  Phone,
  Globe,
  Calendar,
  Award,
  AlertCircle,
  Play
} from 'lucide-react';

interface OrganizationMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joinedAt: string;
  lastActive: string;
  trustScore: number;
  contributionLevel: 'high' | 'medium' | 'low';
  permissions: string[];
}

interface Organization {
  id: string;
  name: string;
  description: string;
  type: 'enterprise' | 'research' | 'government' | 'nonprofit';
  createdAt: string;
  memberCount: number;
  tier: 'basic' | 'professional' | 'enterprise';
  settings: {
    publicProfile: boolean;
    allowInvites: boolean;
    requireApproval: boolean;
    trustThreshold: number;
  };
  metrics: {
    totalCapsules: number;
    monthlyContributions: number;
    averageTrustScore: number;
    economicValue: number;
  };
}

export function OrganizationDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeTab, setActiveTab] = useState<'overview' | 'members' | 'settings'>('overview');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [selectedMember, setSelectedMember] = useState<OrganizationMember | null>(null);

  // Mock organization data - only shown in demo mode
  const organization = isDemoMode ? {
    id: 'org-001',
    name: 'AI Research Collective',
    description: 'Advanced AI research organization focused on ethical AI development and attribution systems.',
    type: 'research' as const,
    createdAt: '2024-01-15T10:00:00Z',
    memberCount: 24,
    tier: 'enterprise' as const,
    settings: {
      publicProfile: true,
      allowInvites: true,
      requireApproval: false,
      trustThreshold: 0.75
    },
    metrics: {
      totalCapsules: 1547,
      monthlyContributions: 342,
      averageTrustScore: 0.87,
      economicValue: 45890.50
    }
  } : null;

  const members: OrganizationMember[] = isDemoMode ? [
    {
      id: 'member-001',
      name: 'Dr. Sarah Chen',
      email: 'sarah.chen@research.org',
      role: 'owner',
      joinedAt: '2024-01-15T10:00:00Z',
      lastActive: '2024-01-16T14:30:00Z',
      trustScore: 0.95,
      contributionLevel: 'high',
      permissions: ['admin', 'invite', 'manage_members', 'view_analytics']
    },
    {
      id: 'member-002',
      name: 'Alex Rodriguez',
      email: 'alex.r@research.org',
      role: 'admin',
      joinedAt: '2024-01-20T09:15:00Z',
      lastActive: '2024-01-16T12:45:00Z',
      trustScore: 0.89,
      contributionLevel: 'high',
      permissions: ['invite', 'manage_members', 'view_analytics']
    },
    {
      id: 'member-003',
      name: 'Dr. Michael Johnson',
      email: 'michael.j@research.org',
      role: 'member',
      joinedAt: '2024-02-01T11:30:00Z',
      lastActive: '2024-01-16T10:20:00Z',
      trustScore: 0.82,
      contributionLevel: 'medium',
      permissions: ['view_analytics']
    },
    {
      id: 'member-004',
      name: 'Emma Williams',
      email: 'emma.w@research.org',
      role: 'member',
      joinedAt: '2024-02-10T15:45:00Z',
      lastActive: '2024-01-15T16:30:00Z',
      trustScore: 0.78,
      contributionLevel: 'medium',
      permissions: []
    }
  ] : [];

  const getRoleIcon = (role: OrganizationMember['role']) => {
    switch (role) {
      case 'owner': return <Crown className="h-4 w-4 text-yellow-600" />;
      case 'admin': return <Shield className="h-4 w-4 text-blue-600" />;
      case 'member': return <Users className="h-4 w-4 text-green-600" />;
      case 'viewer': return <Users className="h-4 w-4 text-gray-600" />;
      default: return <Users className="h-4 w-4 text-gray-600" />;
    }
  };

  const getRoleColor = (role: OrganizationMember['role']) => {
    switch (role) {
      case 'owner': return 'bg-yellow-100 text-yellow-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'member': return 'bg-green-100 text-green-800';
      case 'viewer': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getContributionColor = (level: OrganizationMember['contributionLevel']) => {
    switch (level) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getTierColor = (tier: Organization['tier']) => {
    switch (tier) {
      case 'enterprise': return 'bg-purple-100 text-purple-800';
      case 'professional': return 'bg-blue-100 text-blue-800';
      case 'basic': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleInviteMember = () => {
    if (!newMemberEmail) return;

    // TODO: Implement member invitation via API
    // api.inviteOrganizationMember(newMemberEmail);

    setNewMemberEmail('');
    setShowInviteModal(false);
  };

  const handleRemoveMember = (memberId: string) => {
    // TODO: Implement member removal via API
    // api.removeOrganizationMember(memberId);
  };

  const handleUpdateRole = (memberId: string, newRole: OrganizationMember['role']) => {
    // TODO: Implement role update via API
    // api.updateMemberRole(memberId, newRole);
  };

  const handleSaveChanges = () => {
    // TODO: Implement settings save via API
    // api.updateOrganizationSettings(organization.id, updatedSettings);
    logger.debug('Saving organization settings...');
  };

  const handleEditMember = (memberId: string) => {
    // TODO: Implement member editing functionality
    // This could open a modal or navigate to an edit page
    logger.debug('Editing member:', memberId);
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Organization Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Users className="h-4 w-4 mr-2" />
              Members
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{organization.memberCount}</div>
            <p className="text-xs text-gray-500">Active contributors</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              Capsules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{organization.metrics.totalCapsules}</div>
            <p className="text-xs text-gray-500">Total contributions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Shield className="h-4 w-4 mr-2" />
              Trust Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(organization.metrics.averageTrustScore * 100).toFixed(1)}%</div>
            <p className="text-xs text-gray-500">Average team trust</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Award className="h-4 w-4 mr-2" />
              Economic Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${organization.metrics.economicValue.toLocaleString()}</div>
            <p className="text-xs text-gray-500">Total attribution value</p>
          </CardContent>
        </Card>
      </div>

      {/* Organization Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Building className="h-5 w-5 mr-2" />
            Organization Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Basic Information</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Name:</span>
                  <span>{organization.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Type:</span>
                  <span className="capitalize">{organization.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Tier:</span>
                  <Badge className={getTierColor(organization.tier)}>
                    {organization.tier}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Created:</span>
                  <span>{new Date(organization.createdAt).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-3">Settings</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Public Profile:</span>
                  <span>{organization.settings.publicProfile ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Allow Invites:</span>
                  <span>{organization.settings.allowInvites ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Require Approval:</span>
                  <span>{organization.settings.requireApproval ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Trust Threshold:</span>
                  <span>{(organization.settings.trustThreshold * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t">
            <h4 className="font-medium mb-2">Description</h4>
            <p className="text-sm text-gray-600">{organization.description}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderMembers = () => (
    <div className="space-y-4">
      {/* Member Management Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Team Members</h3>
          <p className="text-sm text-gray-500">{members.length} active members</p>
        </div>
        <Button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center"
        >
          <UserPlus className="h-4 w-4 mr-2" />
          Invite Member
        </Button>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="text-lg">Invite New Member</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Email Address</label>
                <Input
                  type="email"
                  placeholder="Enter email address"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleInviteMember}>Send Invite</Button>
                <Button variant="outline" onClick={() => setShowInviteModal(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Members List */}
      <Card>
        <CardContent className="p-0">
          <div className="space-y-0">
            {members.map((member) => (
              <div
                key={member.id}
                className={`p-4 border-b last:border-b-0 hover:bg-gray-50 cursor-pointer ${
                  selectedMember?.id === member.id ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelectedMember(member)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                      <Users className="h-5 w-5 text-gray-600" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{member.name}</h4>
                        {getRoleIcon(member.role)}
                      </div>
                      <p className="text-sm text-gray-500">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <div className="flex items-center space-x-2">
                        <Badge className={getRoleColor(member.role)}>
                          {member.role}
                        </Badge>
                        <span className={`text-sm font-medium ${getContributionColor(member.contributionLevel)}`}>
                          {member.contributionLevel}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">
                        Trust: {(member.trustScore * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="flex space-x-1">
                      <Button variant="outline" size="sm" onClick={() => handleEditMember(member.id)}>
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleRemoveMember(member.id)}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Organization Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Organization Name</label>
              <Input defaultValue={organization.name} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <Textarea defaultValue={organization.description} rows={3} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Trust Threshold</label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.01"
                defaultValue={organization.settings.trustThreshold}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="publicProfile"
                defaultChecked={organization.settings.publicProfile}
              />
              <label htmlFor="publicProfile" className="text-sm">Public Profile</label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="allowInvites"
                defaultChecked={organization.settings.allowInvites}
              />
              <label htmlFor="allowInvites" className="text-sm">Allow Member Invites</label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="requireApproval"
                defaultChecked={organization.settings.requireApproval}
              />
              <label htmlFor="requireApproval" className="text-sm">Require Approval for New Members</label>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t">
            <Button onClick={handleSaveChanges}>Save Changes</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-2xl font-bold flex items-center">
                  <Building className="h-6 w-6 mr-2" />
                  {organization ? organization.name : 'Organization Dashboard'}
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated organization data for demonstration'
                    : 'Manage your organization and team members'
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
            {organization && (
              <Badge className={getTierColor(organization.tier)}>
                {organization.tier.toUpperCase()}
              </Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !organization && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Organization data will appear here when available. Toggle Demo Mode ON to see sample organization.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Tabs and Content - Only show if we have organization data */}
      {organization && (
        <>
          {/* Navigation Tabs */}
          <div className="border-b">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('members')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'members'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Members ({members.length})
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'settings'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Settings
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'members' && renderMembers()}
          {activeTab === 'settings' && renderSettings()}
        </>
      )}
    </div>
  );
}
