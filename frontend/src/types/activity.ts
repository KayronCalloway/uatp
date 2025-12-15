/**
 * Activity Feed Types
 * Types for the live activity stream in Mission Control
 */

export type ActivityType =
  | 'capsule_created'
  | 'trust_verified'
  | 'chain_sealed'
  | 'attribution_paid'
  | 'reasoning_verified'
  | 'federation_sync'
  | 'spatial_capture'
  | 'governance_action'
  | 'compliance_check';

export type ActivityStatus = 'success' | 'warning' | 'error' | 'pending';

export interface ActivityItem {
  id: string;
  type: ActivityType;
  status: ActivityStatus;
  timestamp: Date;
  title: string;
  description: string;
  metadata: {
    agent?: string;
    provider?: string;
    amount?: number;
    chainId?: string;
    score?: number;
    signature?: string;
    itemCount?: number;
    [key: string]: any;
  };
}

export interface SystemHealthMetric {
  name: string;
  label: string;
  value: number; // 0-100
  status: 'healthy' | 'warning' | 'critical';
  icon: string;
}
