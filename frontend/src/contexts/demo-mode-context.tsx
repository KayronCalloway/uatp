'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface DemoModeContextType {
  isDemoMode: boolean;
  toggleDemoMode: () => void;
  demoMessage: string | null;
}

const DemoModeContext = createContext<DemoModeContextType | undefined>(undefined);

export function DemoModeProvider({ children }: { children: React.ReactNode }) {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoMessage, setDemoMessage] = useState<string | null>(null);

  useEffect(() => {
    // Only access localStorage on client side
    if (typeof window !== 'undefined') {
      const savedDemoMode = localStorage.getItem('uatp-demo-mode');
      if (savedDemoMode === 'true') {
        setIsDemoMode(true);
        setDemoMessage('Demo Mode: Using mock data for presentation');
      }
    }
  }, []);

  const toggleDemoMode = () => {
    const newDemoMode = !isDemoMode;
    setIsDemoMode(newDemoMode);
    localStorage.setItem('uatp-demo-mode', newDemoMode.toString());

    if (newDemoMode) {
      setDemoMessage('Demo Mode: Using mock data for presentation');
    } else {
      setDemoMessage('Production Mode: Using real API data');
      // Clear the message after 3 seconds
      setTimeout(() => setDemoMessage(null), 3000);
    }
  };

  return (
    <DemoModeContext.Provider value={{
      isDemoMode,
      toggleDemoMode,
      demoMessage
    }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  const context = useContext(DemoModeContext);
  if (context === undefined) {
    throw new Error('useDemoMode must be used within a DemoModeProvider');
  }
  return context;
}
