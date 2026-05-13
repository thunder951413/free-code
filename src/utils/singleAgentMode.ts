import { getInitialSettings } from './settings/settings.js'
import { isEnvTruthy } from './envUtils.js'

export const SINGLE_AGENT_MODE_ENV_VAR = 'CLAUDE_CODE_SINGLE_AGENT'

export function isSingleAgentModeEnabled(): boolean {
  return (
    isEnvTruthy(process.env[SINGLE_AGENT_MODE_ENV_VAR]) ||
    getInitialSettings().singleAgentMode === true
  )
}
