'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors in child component tree and displays
 * a fallback UI instead of crashing the entire app.
 *
 * SECURITY: Error details are only shown in development mode.
 * In production, a generic error message is shown to prevent
 * information leakage.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <ComponentThatMightFail />
 *   </ErrorBoundary>
 *
 *   <ErrorBoundary fallback={<CustomFallback />}>
 *     <ComponentThatMightFail />
 *   </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  private static isDevelopment = process.env.NODE_ENV === 'development';

  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error in development
    if (ErrorBoundary.isDevelopment) {
      console.error('ErrorBoundary caught error:', error, errorInfo);
    }

    // Call optional error handler (e.g., for Sentry)
    this.props.onError?.(error, errorInfo);

    // TODO: In production, send to error tracking service
    // if (!ErrorBoundary.isDevelopment) {
    //   sendToErrorTracking(error, errorInfo);
    // }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <Card className="p-6 m-4 border-red-200 bg-red-50">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h2 className="text-lg font-semibold text-red-800">
                Something went wrong
              </h2>
            </div>

            <p className="text-red-700">
              {ErrorBoundary.isDevelopment
                ? this.state.error?.message || 'An unexpected error occurred'
                : 'An unexpected error occurred. Please try again.'}
            </p>

            {/* Show stack trace in development only */}
            {ErrorBoundary.isDevelopment && this.state.error?.stack && (
              <pre className="p-3 bg-red-100 rounded text-xs text-red-800 overflow-auto max-h-48">
                {this.state.error.stack}
              </pre>
            )}

            <div className="flex space-x-3">
              <Button
                onClick={this.handleReset}
                variant="outline"
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                Try Again
              </Button>
              <Button
                onClick={() => window.location.reload()}
                variant="outline"
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                Reload Page
              </Button>
            </div>
          </div>
        </Card>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component to wrap any component with error boundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}

/**
 * Hook-friendly error boundary wrapper
 * Note: Error boundaries must be class components, but this provides
 * a convenient wrapper for functional component usage.
 */
export function ErrorBoundaryWrapper({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>;
}
