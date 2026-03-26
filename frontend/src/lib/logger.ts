/**
 * Production-Safe Logger
 *
 * SECURITY: This logger only outputs to console in development mode.
 * In production, logs are suppressed to prevent information leakage.
 *
 * Usage:
 *   import { logger } from '@/lib/logger';
 *   logger.info('User logged in');
 *   logger.error('API call failed', { endpoint: '/api/data' });
 *   logger.debug('Debug info', someObject);
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: unknown;
}

class Logger {
  private readonly isDevelopment: boolean;
  private readonly isDebugEnabled: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
    this.isDebugEnabled =
      this.isDevelopment && process.env.NEXT_PUBLIC_DEBUG_MODE === 'true';
  }

  /**
   * Sanitize potentially sensitive data from log context
   */
  private sanitize(context: LogContext): LogContext {
    const sensitiveKeys = [
      'password',
      'token',
      'apiKey',
      'api_key',
      'secret',
      'authorization',
      'cookie',
      'session',
      'credit_card',
      'ssn',
      'private_key',
    ];

    const sanitized: LogContext = {};
    for (const [key, value] of Object.entries(context)) {
      const lowerKey = key.toLowerCase();
      if (sensitiveKeys.some((sk) => lowerKey.includes(sk))) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitize(value as LogContext);
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }

  /**
   * Format log message with optional context
   */
  private format(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

    if (context) {
      const sanitized = this.sanitize(context);
      return `${prefix} ${message} ${JSON.stringify(sanitized)}`;
    }
    return `${prefix} ${message}`;
  }

  /**
   * Log debug message (development only, when debug mode enabled)
   */
  debug(message: string, context?: LogContext): void {
    if (this.isDebugEnabled) {
      console.debug(this.format('debug', message, context));
    }
  }

  /**
   * Log info message (development only)
   */
  info(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.info(this.format('info', message, context));
    }
  }

  /**
   * Log warning message (development only)
   */
  warn(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      console.warn(this.format('warn', message, context));
    }
  }

  /**
   * Log error message (development only)
   * In production, consider sending to error tracking service instead
   */
  error(message: string, contextOrError?: LogContext | unknown): void {
    if (this.isDevelopment) {
      // Handle Error objects or unknown types from catch blocks
      let context: LogContext | undefined;
      if (contextOrError instanceof Error) {
        context = { error: contextOrError.message, stack: contextOrError.stack };
      } else if (contextOrError && typeof contextOrError === 'object') {
        context = contextOrError as LogContext;
      } else if (contextOrError !== undefined) {
        context = { error: String(contextOrError) };
      }
      console.error(this.format('error', message, context));
    }
    // TODO: In production, send to error tracking service (Sentry, etc.)
    // if (!this.isDevelopment) {
    //   sendToErrorTracking(message, context);
    // }
  }

  /**
   * Log API error with sanitized details
   */
  apiError(endpoint: string, status: number | string, error?: unknown): void {
    const context: LogContext = {
      endpoint: this.sanitizeUrl(endpoint),
      status,
    };

    if (error instanceof Error) {
      context.errorMessage = error.message;
      // Don't include stack trace in logs
    }

    this.error('API request failed', context);
  }

  /**
   * Sanitize URL to remove sensitive query parameters
   */
  private sanitizeUrl(url: string): string {
    try {
      const parsed = new URL(url, 'http://localhost');
      const sensitiveParams = ['token', 'key', 'api_key', 'password', 'secret'];

      for (const param of sensitiveParams) {
        if (parsed.searchParams.has(param)) {
          parsed.searchParams.set(param, '[REDACTED]');
        }
      }

      // Return path + sanitized query string only (no host in logs)
      return parsed.pathname + parsed.search;
    } catch {
      // If URL parsing fails, return sanitized version
      return url.replace(/[?&](token|key|api_key|password|secret)=[^&]*/gi, '$1=[REDACTED]');
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export for testing
export { Logger };
