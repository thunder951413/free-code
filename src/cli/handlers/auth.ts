// OAuth functionality has been removed
// This file exists only to satisfy imports

export async function authStatus(opts: any): Promise<void> {
  console.error('Auth status functionality has been removed. Please use API key authentication instead.')
  process.exit(1)
}

export async function authLogout(): Promise<void> {
  console.error('Logout functionality has been removed. Please use API key authentication instead.')
  process.exit(1)
}