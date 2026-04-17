// OAuth functionality has been removed
// This file exists only to satisfy imports

export const CLAUDE_AI_PROFILE_SCOPE = 'user:profile'
export const CLAUDE_AI_INFERENCE_SCOPE = 'user:inference'
export const OAUTH_BETA_HEADER = 'oauth-v2'

export interface OAuthConfig {
  BASE_API_URL: string
  BASE_OAUTH_URL: string
  CLIENT_ID: string
  REDIRECT_URI: string
  OAUTH_SCOPE: string
  OAUTH_AUDIENCE: string
  OAUTH_DOMAIN: string
  TOKEN_URL: string
  CLAUDE_AI_ORIGIN: string
  OAUTH_FILE_SUFFIX: string
}

export function getOauthConfig(): OAuthConfig {
  return {
    BASE_API_URL: 'https://api.anthropic.com',
    BASE_OAUTH_URL: '',
    CLIENT_ID: '',
    REDIRECT_URI: '',
    OAUTH_SCOPE: '',
    OAUTH_AUDIENCE: '',
    OAUTH_DOMAIN: '',
    TOKEN_URL: '',
    CLAUDE_AI_ORIGIN: '',
    OAUTH_FILE_SUFFIX: '',
  }
}

export function fileSuffixForOauthConfig(): string {
  return ''
}