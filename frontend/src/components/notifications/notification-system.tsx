'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/use-websocket';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Bell,
  X,
  Database,
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';

interface NotificationMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  category: 'capsule' | 'trust' | 'economic' | 'system';
}

export function NotificationSystem() {
  const { isDemoMode } = useDemoMode();
  const [notifications, setNotifications] = useState<NotificationMessage[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Temporarily disable WebSocket to prevent console errors until backend WebSocket is implemented
  const { isConnected, lastMessage } = useWebSocket({
    url: '', // Disabled until backend WebSocket endpoint is implemented
    maxReconnectAttempts: 0,
    onMessage: (message) => {
      // Convert WebSocket message to notification
      const notification: NotificationMessage = {
        id: Date.now().toString(),
        type: getNotificationType(message.type),
        title: getNotificationTitle(message.type),
        message: getNotificationMessage(message.type, message.data),
        timestamp: message.timestamp,
        category: getNotificationCategory(message.type)
      };
      
      addNotification(notification);
    },
    onError: (error) => {
      // WebSocket not available, using polling for updates
    }
  });

  const addNotification = (notification: NotificationMessage) => {
    setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep only 10 notifications
    setUnreadCount(prev => prev + 1);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const markAsRead = () => {
    setUnreadCount(0);
  };

  // Simulate some notifications for demo purposes - ONLY in demo mode
  useEffect(() => {
    if (!isDemoMode) return; // Don't simulate notifications in live mode

    const interval = setInterval(() => {
      const mockNotifications: NotificationMessage[] = [
        {
          id: Date.now().toString(),
          type: 'success',
          title: 'New Capsule Created',
          message: 'A new capsule has been added to the chain by agent-001',
          timestamp: new Date().toISOString(),
          category: 'capsule'
        },
        {
          id: (Date.now() + 1).toString(),
          type: 'warning',
          title: 'Trust Score Alert',
          message: 'Agent trust score has dropped below threshold',
          timestamp: new Date().toISOString(),
          category: 'trust'
        },
        {
          id: (Date.now() + 2).toString(),
          type: 'info',
          title: 'Economic Update',
          message: 'Monthly dividend distribution completed',
          timestamp: new Date().toISOString(),
          category: 'economic'
        }
      ];

      if (Math.random() > 0.7) { // 30% chance every 30 seconds
        const randomNotification = mockNotifications[Math.floor(Math.random() * mockNotifications.length)];
        addNotification(randomNotification);
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [isDemoMode]);

  const getNotificationIcon = (type: string, category: string) => {
    if (type === 'success') return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (type === 'error') return <AlertTriangle className="h-4 w-4 text-red-600" />;
    if (type === 'warning') return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    
    switch (category) {
      case 'capsule': return <Database className="h-4 w-4 text-blue-600" />;
      case 'trust': return <Shield className="h-4 w-4 text-purple-600" />;
      case 'economic': return <TrendingUp className="h-4 w-4 text-green-600" />;
      default: return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-50 border-green-200';
      case 'error': return 'bg-red-50 border-red-200';
      case 'warning': return 'bg-yellow-50 border-yellow-200';
      default: return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Notification Bell */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => {
          setIsVisible(!isVisible);
          if (!isVisible) markAsRead();
        }}
        className="relative"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {/* Notification Panel */}
      {isVisible && (
        <Card className="absolute top-12 right-0 w-80 max-h-96 overflow-y-auto shadow-lg">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Notifications</h3>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
                  <span className="text-xs text-gray-500">
                    {isConnected ? 'Live' : 'Offline'}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllNotifications}
                  className="text-xs"
                >
                  Clear All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsVisible(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-l-4 ${getNotificationColor(notification.type)} last:border-b-0`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {getNotificationIcon(notification.type, notification.category)}
                      <div className="flex-1">
                        <h4 className="text-sm font-medium">{notification.title}</h4>
                        <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notification.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeNotification(notification.id)}
                      className="p-1 h-6 w-6"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}
    </div>
  );
}

// Helper functions
function getNotificationType(messageType: string): 'success' | 'error' | 'warning' | 'info' {
  switch (messageType) {
    case 'capsule_created':
    case 'economic_payout':
      return 'success';
    case 'trust_violation':
    case 'system_error':
      return 'error';
    case 'trust_warning':
    case 'quota_warning':
      return 'warning';
    default:
      return 'info';
  }
}

function getNotificationTitle(messageType: string): string {
  switch (messageType) {
    case 'capsule_created': return 'New Capsule';
    case 'capsule_updated': return 'Capsule Updated';
    case 'trust_updated': return 'Trust Score Update';
    case 'trust_violation': return 'Trust Violation';
    case 'economic_payout': return 'Economic Payout';
    case 'system_error': return 'System Error';
    default: return 'System Update';
  }
}

function getNotificationMessage(messageType: string, data: any): string {
  switch (messageType) {
    case 'capsule_created':
      return `New capsule created by ${data?.agent_id || 'unknown agent'}`;
    case 'capsule_updated':
      return `Capsule ${data?.capsule_id || 'unknown'} has been updated`;
    case 'trust_updated':
      return `Trust score updated for ${data?.agent_id || 'unknown agent'}`;
    case 'trust_violation':
      return `Trust violation detected for ${data?.agent_id || 'unknown agent'}`;
    case 'economic_payout':
      return `Payout of $${data?.amount || 0} processed`;
    default:
      return 'System notification';
  }
}

function getNotificationCategory(messageType: string): 'capsule' | 'trust' | 'economic' | 'system' {
  if (messageType.includes('capsule')) return 'capsule';
  if (messageType.includes('trust')) return 'trust';
  if (messageType.includes('economic') || messageType.includes('payout')) return 'economic';
  return 'system';
}