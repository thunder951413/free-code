// OAuth functionality has been removed
// This file exists only to satisfy imports

export class OAuthService {
  static async getCurrentUser() {
    return null
  }

  static async login() {
    throw new Error('OAuth functionality has been removed')
  }

  static async logout() {
    // No-op
  }
}