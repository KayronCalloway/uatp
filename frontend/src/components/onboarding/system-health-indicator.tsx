'use client';

import React from 'react';
import { SystemHealth } from '@/types/onboarding';

interface SystemHealthIndicatorProps {
  health: SystemHealth | null;
}

export function SystemHealthIndicator({ health }: SystemHealthIndicatorProps) {
  if (!health) {
    return (
      <div className="flex items-center space-x-2 text-gray-500 text-sm">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
        <span>Checking system...</span>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent':
      case 'good':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getHealthText = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'System Excellent';
      case 'good':
        return 'System Healthy';
      case 'warning':
        return 'System Warning';
      case 'critical':
        return 'System Critical';
      default:
        return 'System Unknown';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'excellent':
        return '🟢';
      case 'good':
        return '🟡';
      case 'warning':
        return '🟠';
      case 'critical':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div className="flex items-center space-x-3">
      {/* Health Status */}
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${getHealthColor(health.overall_status)}`} />
        <span className="text-sm font-medium text-gray-700">
          {getHealthText(health.overall_status)}
        </span>
      </div>

      {/* Health Score */}
      <div className="flex items-center space-x-1 text-xs text-gray-500">
        <span>{getHealthIcon(health.overall_status)}</span>
        <span>{Math.round(health.score * 100)}%</span>
      </div>

      {/* Detailed Tooltip */}
      <div className="relative group">
        <div className="cursor-help text-gray-400 hover:text-gray-600">
          ⓘ
        </div>
        
        {/* Tooltip */}
        <div className="absolute right-0 top-full mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg p-3 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
          <div className="text-sm">
            <div className="font-medium text-gray-900 mb-2">{health.summary}</div>
            <div className="space-y-1">
              {Object.entries(health.components).map(([component, details]) => (
                <div key={component} className="flex items-center justify-between">
                  <span className="text-gray-600 capitalize">
                    {component.replace('_', ' ')}:
                  </span>
                  <div className="flex items-center space-x-1">
                    <div className={`w-2 h-2 rounded-full ${getHealthColor(details.status)}`} />
                    <span className="text-xs">{Math.round(details.score * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}