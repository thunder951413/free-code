// OAuth functionality has been removed
// This file exists only to satisfy imports

export interface OAuthTokens {
  accessToken: string
  refreshToken: string | null
  expiresAt: number
  scopes?: string[]
  subscriptionType?: string
  rateLimitTier?: string
}

export function getClaudeAIOAuthTokens(): OAuthTokens | null {
  return null
}

export function isOAuthTokenExpired(expiresAt: number): boolean {
  return true
}

export function refreshOAuthToken(): Promise<OAuthTokens | null> {
  return Promise.resolve(null)
}

export function shouldUseClaudeAIAuth(scopes?: string[]): boolean {
  return false
}

export function checkAndRefreshOAuthTokenIfNeeded(): Promise<boolean> {
  return Promise.resolve(false)
}

export function getOrganizationUUID(): string | null {
  return null
}

export function populateOAuthAccountInfoIfNeeded(): Promise<void> {
  return Promise.resolve()
}

export function handleOAuth401Error(failedAccessToken: string): Promise<void> {
  return Promise.resolve()
}