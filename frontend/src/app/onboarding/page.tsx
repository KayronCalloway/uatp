import { OnboardingWizard } from '@/components/onboarding/onboarding-wizard';

export default function OnboardingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <OnboardingWizard />
    </div>
  );
}

export const metadata = {
  title: 'Get Started - UATP Onboarding',
  description: 'Welcome to UATP! Get started with AI trust and attribution in minutes.',
};
