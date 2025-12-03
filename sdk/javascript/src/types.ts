/**
 * Core TypeScript types for the UATP JavaScript SDK
 */

export interface BaseConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  retryAttempts?: number;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retryAttempts?: number;
  signal?: AbortSignal;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
  requestId?: string;
}

export class UATPError extends Error {
  public readonly code: string;
  public readonly statusCode?: number;
  public readonly details?: any;

  constructor(
    message: string,
    code: string = 'UATP_ERROR',
    statusCode?: number,
    details?: any
  ) {
    super(message);
    this.name = 'UATPError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }

  static fromResponse(response: any): UATPError {
    return new UATPError(
      response.message || 'Unknown error',
      response.code || 'UNKNOWN_ERROR',
      response.statusCode,
      response.details
    );
  }
}

// Common enums
export enum ContentType {
  TEXT = 'text',
  CODE = 'code',
  IMAGE = 'image',
  AUDIO = 'audio',
  VIDEO = 'video'
}

export enum Platform {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  HUGGINGFACE = 'huggingface',
  GOOGLE = 'google',
  META = 'meta',
  CUSTOM = 'custom'
}

export enum AttributionSource {
  HUMAN_INPUT = 'human_input',
  AI_GENERATION = 'ai_generation',
  COLLABORATIVE = 'collaborative',
  DERIVATIVE = 'derivative'
}

// Utility types
export type Timestamp = string; // ISO 8601 format
export type UUID = string;
export type Hash = string;

export interface TimestampedRecord {
  createdAt: Timestamp;
  updatedAt?: Timestamp;
}

export interface Identifiable {
  id: string;
}

export interface Verifiable {
  signature?: string;
  verified: boolean;
  verificationTimestamp?: Timestamp;
}

// Configuration interfaces
export interface RetryConfig {
  attempts: number;
  delay: number;
  backoff: 'linear' | 'exponential';
  maxDelay: number;
}

export interface CacheConfig {
  enabled: boolean;
  ttl: number; // seconds
  maxSize: number;
}

// HTTP client types
export interface HttpClientConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
  retry: RetryConfig;
}

export interface HttpResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

// Event system types
export interface UATPEvent<T = any> {
  type: string;
  data: T;
  timestamp: Timestamp;
  source: string;
}

export type EventListener<T = any> = (event: UATPEvent<T>) => void;

export interface EventEmitter {
  on<T>(event: string, listener: EventListener<T>): void;
  off<T>(event: string, listener: EventListener<T>): void;
  emit<T>(event: string, data: T): void;
}

// Pagination types
export interface PaginationOptions {
  limit?: number;
  offset?: number;
  cursor?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
    nextCursor?: string;
  };
}

// Validation types
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Metrics types
export interface PerformanceMetrics {
  requestCount: number;
  averageResponseTime: number;
  errorRate: number;
  cacheHitRate: number;
  lastUpdated: Timestamp;
}

// Feature flags
export interface FeatureFlags {
  enablePrivacy: boolean;
  enableWatermarking: boolean;
  enableGovernance: boolean;
  enableFederation: boolean;
  experimentalFeatures: string[];
}