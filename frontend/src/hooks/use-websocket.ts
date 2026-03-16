import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface UseWebSocketProps {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5
}: UseWebSocketProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  const connect = () => {
    // Don't connect if URL is empty or not provided
    if (!url || url === '') {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setReconnectAttempts(0);
        // WebSocket connected successfully
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle real-time updates by invalidating relevant queries
          switch (message.type) {
            case 'capsule_created':
            case 'capsule_updated':
              queryClient.invalidateQueries({ queryKey: ['capsules'] });
              queryClient.invalidateQueries({ queryKey: ['capsule-stats'] });
              break;
            case 'trust_updated':
              queryClient.invalidateQueries({ queryKey: ['trust-metrics'] });
              break;
            case 'violation_detected':
              queryClient.invalidateQueries({ queryKey: ['trust-violations'] });
              break;
            case 'health_update':
              queryClient.invalidateQueries({ queryKey: ['health'] });
              break;
            default:
              break;
          }

          if (onMessage) {
            onMessage(message);
          }
        } catch (error) {
          // Silently handle WebSocket message parsing errors
        }
      };

      wsRef.current.onerror = (error) => {
        console.warn('WebSocket error (this is expected if no WebSocket server is running):', error);
        if (onError) {
          onError(error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        // WebSocket disconnected

        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectInterval);
        }
        // Max reconnection attempts reached - this is expected if no WebSocket server is running
      };
    } catch (error) {
      // Silently handle WebSocket connection errors
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
    reconnectAttempts
  };
}
