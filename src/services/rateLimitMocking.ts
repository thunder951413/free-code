/**
 * Facade for rate limit header processing
 * This isolates mock logic from production code
 */

import { APIError } from '@anthropic-ai/sdk'
import {
  applyMockHeaders,
  checkMockFastModeRateLimit,
  getMockHeaderless429Message,
  getMockHeaders,
  isMockFastModeRateLimitScenario,
  shouldProcessMockLimits,
} from './mockRateLimits.js'

/**
 * Process headers, applying mocks if /mock-limits command is active
 */
export function processRateLimitHeaders(
  headers: globalThis.Headers,
): globalThis.Headers {
  // Only apply mocks for Ant employees using /mock-limits command
  if (shouldProcessMockLimits()) {
    return applyMockHeaders(headers)
  }
  return headers
}

/**
 * Check if we should process rate limits (either real subscriber or /mock-limits command)
 */
export function shouldProcessRateLimits(isSubscriber: boolean): boolean {
  return isSubscriber || shouldProcessMockLimits()
}

/**
 * Check if mock rate limits should throw a 429 error
 * Returns the error to throw, or null if no error should be thrown
 * @param currentModel The model being used for the current request
 * @param isFastModeActive Whether fast mode is currently active (for fast-mode-only mocks)
 */
export function checkMockRateLimitError(
  currentModel: string,
  isFastModeActive?: boolean,
): APIError | null {
  if (!shouldProcessMockLimits()) {
    return null
  }

  const headerlessMessage = getMockHeaderless429Message()
  if (headerlessMessage) {
    return new APIError(
      429,
      { error: { type: 'rate_limit_error', message: headerlessMessage } },
      headerlessMessage,
      // eslint-disable-next-line eslint-plugin-n/no-unsupported-features/node-builtins
      new globalThis.Headers(),
    )
  }

  const mockHeaders = getMockHeaders()
  if (!mockHeaders) {
    return null
  }

  // Check if we should throw a 429 error
  // Only throw if:
  // 1. Status is rejected AND
  // 2. Either no overage headers OR overage is also rejected
  // 3. For Ds-specific limits, only throw if actually using an Ds model
  const status = mockHeaders['anthropic-ratelimit-unified-status']
  const overageStatus =
    mockHeaders['anthropic-ratelimit-unified-overage-status']
  const rateLimitType =
    mockHeaders['anthropic-ratelimit-unified-representative-claim']

  // Check if this is an Ds-specific rate limit
  const isDsLimit = rateLimitType === 'seven_day_Ds'

  // Check if current model is an Ds model (handles all variants including aliases)
  const isUsingDs = currentModel.includes('Ds')

  // For Ds limits, only throw 429 if actually using Ds
  // This simulates the real API behavior where fallback to Sonnet succeeds
  if (isDsLimit && !isUsingDs) {
    return null
  }

  // Check for mock fast mode rate limits (handles expiry, countdown, etc.)
  if (isMockFastModeRateLimitScenario()) {
    const fastModeHeaders = checkMockFastModeRateLimit(isFastModeActive)
    if (fastModeHeaders === null) {
      return null
    }
    // Create a mock 429 error with the fast mode headers
    const error = new APIError(
      429,
      { error: { type: 'rate_limit_error', message: 'Rate limit exceeded' } },
      'Rate limit exceeded',
      // eslint-disable-next-line eslint-plugin-n/no-unsupported-features/node-builtins
      new globalThis.Headers(
        Object.entries(fastModeHeaders).filter(([_, v]) => v !== undefined) as [
          string,
          string,
        ][],
      ),
    )
    return error
  }

  const shouldThrow429 =
    status === 'rejected' && (!overageStatus || overageStatus === 'rejected')

  if (shouldThrow429) {
    // Create a mock 429 error with the appropriate headers
    const error = new APIError(
      429,
      { error: { type: 'rate_limit_error', message: 'Rate limit exceeded' } },
      'Rate limit exceeded',
      // eslint-disable-next-line eslint-plugin-n/no-unsupported-features/node-builtins
      new globalThis.Headers(
        Object.entries(mockHeaders).filter(([_, v]) => v !== undefined) as [
          string,
          string,
        ][],
      ),
    )
    return error
  }

  return null
}

/**
 * Check if this is a mock 429 error that shouldn't be retried
 */
export function isMockRateLimitError(error: APIError): boolean {
  return shouldProcessMockLimits() && error.status === 429
}

/**
 * Check if /mock-limits command is currently active (for UI purposes)
 */
export { shouldProcessMockLimits }
