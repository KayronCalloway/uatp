'use client';

import { useState } from 'react';
import { CapsuleList } from './capsule-list';
import { CapsuleDetail } from './capsule-detail';
import { AnyCapsule } from '@/types/api';

export function CapsuleExplorer() {
  const [selectedCapsule, setSelectedCapsule] = useState<AnyCapsule | null>(null);

  const handleCapsuleSelect = (capsule: AnyCapsule) => {
    setSelectedCapsule(capsule);
  };

  const handleBack = () => {
    setSelectedCapsule(null);
  };

  return (
    <div className="w-full h-full">
      {selectedCapsule ? (
        <CapsuleDetail 
          capsuleId={selectedCapsule.capsule_id || selectedCapsule.id} 
          onBack={handleBack}
        />
      ) : (
        <CapsuleList onCapsuleSelect={handleCapsuleSelect} />
      )}
    </div>
  );
}