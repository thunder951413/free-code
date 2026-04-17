// OAuth functionality has been removed
// This file exists only to satisfy imports

export class AuthenticationCancelledError extends Error {
  constructor() {
    super('Authentication cancelled')
  }
}

export class ClaudeAuthProvider {
  async getAccessToken(): Promise<string | null> {
    return null
  }
}

export async function performMCPOAuthFlow(): Promise<string> {
  throw new Error('OAuth functionality has been removed')
}

export async function revokeServerTokens(): Promise<void> {
  // No-op
}

export function hasMcpDiscoveryButNoToken(): boolean {
  return false
}

export function wrapFetchWithStepUpDetection(fetchFn: any): any {
  return fetchFn
}