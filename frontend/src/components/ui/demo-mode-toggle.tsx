'use client';

import { useDemoMode } from '@/contexts/demo-mode-context';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Play, Database, AlertCircle } from 'lucide-react';

export function DemoModeToggle() {
  const { isDemoMode, toggleDemoMode, demoMessage } = useDemoMode();

  return (
    <div className="flex items-center space-x-3">
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2 text-sm">
          {isDemoMode ? (
            <Play className="h-4 w-4 text-orange-500" />
          ) : (
            <Database className="h-4 w-4 text-green-500" />
          )}
          <span className="hidden sm:inline">
            {isDemoMode ? 'Demo' : 'Live'}
          </span>
        </div>
        
        <Switch
          checked={isDemoMode}
          onCheckedChange={toggleDemoMode}
          aria-label="Toggle demo mode"
        />
      </div>
      
      {isDemoMode && (
        <Badge variant="secondary" className="hidden md:flex bg-orange-100 text-orange-800 border-orange-300">
          <Play className="h-3 w-3 mr-1" />
          Demo Mode
        </Badge>
      )}
      
      {demoMessage && (
        <div className="fixed top-4 right-4 z-50 max-w-sm">
          <div className={`p-3 rounded-lg shadow-lg border ${
            isDemoMode 
              ? 'bg-orange-50 text-orange-800 border-orange-300'
              : 'bg-green-50 text-green-800 border-green-300'
          }`}>
            <div className="flex items-center space-x-2">
              {isDemoMode ? (
                <Play className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">{demoMessage}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}