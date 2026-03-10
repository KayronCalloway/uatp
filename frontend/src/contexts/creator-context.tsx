'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

interface CreatorState {
  isCreator: boolean;
  creatorId: string | null;
  privileges: {
    adminAccess: boolean;
    bulkOperations: boolean;
    systemDebug: boolean;
    rawDataAccess: boolean;
    advancedTools: boolean;
  };
}

interface CreatorContextValue {
  state: CreatorState;
  enableCreatorMode: (creatorId?: string) => void;
  disableCreatorMode: () => void;
}

const initialState: CreatorState = {
  isCreator: false,
  creatorId: null,
  privileges: {
    adminAccess: false,
    bulkOperations: false,
    systemDebug: false,
    rawDataAccess: false,
    advancedTools: false,
  }
};

const CreatorContext = createContext<CreatorContextValue>({
  state: initialState,
  enableCreatorMode: () => {},
  disableCreatorMode: () => {},
});

const CREATOR_KEYS = [
  'kay-creator-key',
  'uatp-system-creator',
  'dev-creator-001'
];

const CREATOR_IDS = [
  'kay',
  'kay-user', 
  'kay-live-agent',
  'system-creator'
];

export function CreatorProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<CreatorState>(initialState);

  useEffect(() => {
    const checkCreatorStatus = async () => {
      // Check for creator key in localStorage first
      const creatorKey = localStorage.getItem('uatp_creator_key');
      const creatorId = localStorage.getItem('uatp_creator_id');
      
      // Auto-detect Kay as creator based on existing data patterns
      const isKayCreator = creatorId === 'kay' || creatorKey === 'kay-creator-key';
      
      // Check backend for creator status via the API client
      let backendCreatorCheck = false;
      try {
        // Import API client dynamically to avoid circular deps
        const { apiClient } = await import('@/lib/api-client');
        const response = await apiClient.healthCheck();
        
        // For now, we'll consider anyone who can reach the backend as a creator
        // In production, this would be a proper creator-check endpoint
        if (response) {
          backendCreatorCheck = true;
          
          // If backend confirms creator status, auto-enable creator mode
          if (backendCreatorCheck && !isKayCreator) {
            localStorage.setItem('uatp_creator_key', 'kay-creator-key');
            localStorage.setItem('uatp_creator_id', 'kay');
          }
        }
      } catch (error) {
        console.log('Could not check creator status from backend - API not available');
      }
      
      // Enable creator mode if local keys OR backend confirms creator status
      if ((creatorKey && CREATOR_KEYS.includes(creatorKey)) || isKayCreator || backendCreatorCheck) {
        setState({
          isCreator: true,
          creatorId: creatorId || creatorKey || 'kay',
          privileges: {
            adminAccess: true,
            bulkOperations: true,
            systemDebug: true,
            rawDataAccess: true,
            advancedTools: true,
          }
        });
      }
    };

    checkCreatorStatus();
  }, []);

  const enableCreatorMode = (creatorId: string = 'kay') => {
    const creatorKey = 'kay-creator-key';
    
    localStorage.setItem('uatp_creator_key', creatorKey);
    localStorage.setItem('uatp_creator_id', creatorId);
    
    setState({
      isCreator: true,
      creatorId,
      privileges: {
        adminAccess: true,
        bulkOperations: true,
        systemDebug: true,
        rawDataAccess: true,
        advancedTools: true,
      }
    });
  };

  const disableCreatorMode = () => {
    localStorage.removeItem('uatp_creator_key');
    localStorage.removeItem('uatp_creator_id');
    
    setState(initialState);
  };

  return (
    <CreatorContext.Provider value={{ state, enableCreatorMode, disableCreatorMode }}>
      {children}
    </CreatorContext.Provider>
  );
}

export function useCreator() {
  const context = useContext(CreatorContext);
  if (!context) {
    throw new Error('useCreator must be used within a CreatorProvider');
  }
  return context;
}

export function useIsCreator() {
  const { state } = useCreator();
  return state.isCreator;
}

export function useCreatorPrivileges() {
  const { state } = useCreator();
  return state.privileges;
}