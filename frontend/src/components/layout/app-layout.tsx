'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import { NotificationSystem } from '@/components/notifications/notification-system';
import { OnboardingBanner } from '@/components/onboarding/onboarding-banner';
import { DemoModeToggle } from '@/components/ui/demo-mode-toggle';
import {
  Globe,
  Database,
  Activity,
  LogOut,
  Menu,
  X,
  Brain,
  BarChart3
} from 'lucide-react';
import Link from 'next/link';

interface AppLayoutProps {
  children: React.ReactNode;
}

export type ViewType = 'home' | 'capsules' | 'system';

interface NavigationItem {
  id: ViewType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'home',
    label: 'Home',
    icon: Globe,
    description: 'Universal Autonomous Transaction Protocol'
  },
  {
    id: 'capsules',
    label: 'Capsules',
    icon: Database,
    description: 'Browse and verify transaction capsules'
  },
  {
    id: 'system',
    label: 'System',
    icon: Activity,
    description: 'System health and status'
  }
];

interface AppLayoutWithNavProps extends AppLayoutProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
}

export function AppLayoutWithNav({ children, currentView, onViewChange }: AppLayoutWithNavProps) {
  const { logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const currentItem = navigationItems.find(item => item.id === currentView);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0 lg:flex-shrink-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 border-b bg-white">
            <div className="flex items-center space-x-3">
              <Globe className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-lg font-bold text-gray-900">UATP</h1>
                <p className="text-xs text-gray-500">Capsule Engine</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          <nav className="flex-1 px-3 py-4 overflow-y-auto">
            <div className="space-y-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentView === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onViewChange(item.id);
                      setSidebarOpen(false);
                    }}
                    className={`
                      w-full flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-colors
                      ${isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }
                    `}
                  >
                    <Icon className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive ? 'text-blue-700' : 'text-gray-400'}`} />
                    <div className="text-left min-w-0">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs text-gray-500 truncate">{item.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>

          </nav>

          <div className="p-4 border-t bg-gray-50">
            <Button
              variant="outline"
              onClick={logout}
              className="w-full"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-0 lg:ml-0">
        {/* Top bar */}
        <header className="bg-white shadow-sm border-b">
          <div className="flex items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden"
              >
                <Menu className="h-5 w-5" />
              </Button>

              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {currentItem?.label}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {currentItem?.description}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <DemoModeToggle />
              <div className="hidden xl:block text-sm text-gray-500">
                Universal Autonomous Transaction Protocol
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className="p-4 sm:p-6 lg:p-8 max-w-full">
            <OnboardingBanner />
            {children}
          </div>
        </main>

        {/* Notification System */}
        <NotificationSystem />
      </div>
    </div>
  );
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-full mx-auto">
        {children}
      </div>
    </div>
  );
}
