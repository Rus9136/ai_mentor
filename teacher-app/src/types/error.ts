/**
 * Standardized API error types.
 *
 * These types match the backend ErrorResponse schema for consistent
 * error handling across the application.
 */

/**
 * Individual validation error for a field.
 */
export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

/**
 * Structured API error response.
 *
 * All API errors now return this format with an error code
 * that can be used for i18n translations.
 */
export interface APIError {
  /** Error code (e.g., "AUTH_001", "RES_001") */
  code: string;
  /** Human-readable error message (English) */
  message: string;
  /** Alias for message (backward compatibility) */
  detail: string;
  /** Field name for single-field validation errors */
  field?: string;
  /** Multiple validation errors (for 422 responses) */
  errors?: ValidationError[];
  /** Additional context (e.g., resource_id, retry_after) */
  meta?: Record<string, unknown>;
}

/**
 * Error code categories.
 *
 * Each category maps to specific HTTP status codes:
 * - AUTH: 401 Unauthorized
 * - ACCESS: 403 Forbidden
 * - VAL: 400/422 Bad Request
 * - RES: 404 Not Found
 * - SVC: 500/503 Server Error
 * - RATE: 429 Too Many Requests
 */
export type ErrorCategory = 'AUTH' | 'ACCESS' | 'VAL' | 'RES' | 'SVC' | 'RATE';

/**
 * Known error codes for type safety.
 * Use these constants when checking specific error codes.
 */
export const ErrorCodes = {
  // Authentication (401)
  AUTH_001: 'AUTH_001', // Invalid credentials
  AUTH_002: 'AUTH_002', // Token expired
  AUTH_003: 'AUTH_003', // Invalid token
  AUTH_004: 'AUTH_004', // Token type mismatch
  AUTH_005: 'AUTH_005', // User not found (from token)
  AUTH_006: 'AUTH_006', // Google OAuth error
  AUTH_007: 'AUTH_007', // Invalid refresh token

  // Authorization (403)
  ACCESS_001: 'ACCESS_001', // Insufficient permissions
  ACCESS_002: 'ACCESS_002', // Role not allowed
  ACCESS_003: 'ACCESS_003', // Resource belongs to another school
  ACCESS_004: 'ACCESS_004', // User account is inactive
  ACCESS_005: 'ACCESS_005', // Not resource owner

  // Validation (400/422)
  VAL_001: 'VAL_001', // Invalid input format
  VAL_007: 'VAL_007', // Invalid question type
  VAL_008: 'VAL_008', // Cannot modify after publishing

  // Resource (404/409)
  RES_001: 'RES_001', // Generic not found
  RES_003: 'RES_003', // Textbook not found
  RES_004: 'RES_004', // Chapter not found
  RES_005: 'RES_005', // Paragraph not found
  RES_008: 'RES_008', // Homework not found
  RES_009: 'RES_009', // Task not found
  RES_015: 'RES_015', // Class not found

  // Service (500/503)
  SVC_001: 'SVC_001', // Internal server error
  SVC_002: 'SVC_002', // LLM service unavailable
  SVC_005: 'SVC_005', // AI generation failed

  // Rate limit (429)
  RATE_001: 'RATE_001', // Rate limit exceeded
} as const;

export type ErrorCodeType = typeof ErrorCodes[keyof typeof ErrorCodes];
