import { OnboardingComplete } from '@/components/onboarding/onboarding-complete';

export default function OnboardingCompletePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <OnboardingComplete />
    </div>
  );
}

export const metadata = {
  title: 'Setup Complete - UATP',
  description: 'Congratulations! Your UATP system is ready to use.',
};