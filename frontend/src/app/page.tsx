'use client';

import { useAuth } from '@/contexts/auth-context-simple';
import { LoginForm } from '@/components/auth/login-form';
import { MainApp } from '@/components/app/main-app';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return <MainApp />;
}
