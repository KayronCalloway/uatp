'use client';

import { useState } from 'react';
import { AppLayoutWithNav, ViewType } from '@/components/layout/app-layout';
import { HomeView } from '@/components/home/home-view';
import { CapsuleExplorer } from '@/components/capsules/capsule-explorer';
import { ModelsView } from '@/components/models/models-view';
import { SystemView } from '@/components/system/system-view';

export function MainApp() {
  const [currentView, setCurrentView] = useState<ViewType>('home');

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <HomeView />;

      case 'capsules':
        return <CapsuleExplorer />;

      case 'models':
        return <ModelsView />;

      case 'system':
        return <SystemView />;

      default:
        return <HomeView />;
    }
  };

  return (
    <AppLayoutWithNav currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </AppLayoutWithNav>
  );
}
