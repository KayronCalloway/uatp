'use client';

import { useState } from 'react';
import { CapsuleOverview } from './capsule-overview';
import { CapsuleList } from './capsule-list';
import { CapsuleDetail } from './capsule-detail';
import { AnyCapsule } from '@/types/api';

type ViewType = 'overview' | 'list' | 'detail';

export function CapsuleExplorer() {
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [selectedCapsule, setSelectedCapsule] = useState<AnyCapsule | null>(null);

  const handleViewList = () => {
    setCurrentView('list');
  };

  const handleCapsuleSelect = (capsule: AnyCapsule) => {
    setSelectedCapsule(capsule);
    setCurrentView('detail');
  };

  const handleBackToList = () => {
    setSelectedCapsule(null);
    setCurrentView('list');
  };

  const handleBackToOverview = () => {
    setSelectedCapsule(null);
    setCurrentView('overview');
  };

  return (
    <div className="w-full h-full">
      {currentView === 'overview' && (
        <CapsuleOverview onViewList={handleViewList} />
      )}

      {currentView === 'list' && (
        <CapsuleList
          onCapsuleSelect={handleCapsuleSelect}
          onBack={handleBackToOverview}
        />
      )}

      {currentView === 'detail' && selectedCapsule && (
        <CapsuleDetail
          capsuleId={selectedCapsule.capsule_id || selectedCapsule.id}
          onBack={handleBackToList}
        />
      )}
    </div>
  );
}
