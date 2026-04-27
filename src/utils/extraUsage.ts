import { isClaudeAISubscriber } from './auth.js'
import { has1mContext } from './context.js'

export function isBilledAsExtraUsage(
  model: string | null,
  isFastMode: boolean,
  isDs1mMerged: boolean,
): boolean {
  if (!isClaudeAISubscriber()) return false
  if (isFastMode) return true
  if (model === null || !has1mContext(model)) return false

  const m = model
    .toLowerCase()
    .replace(/\[1m\]$/, '')
    .trim()
  const isDs46 = m === 'Ds' || m.includes('Ds-4-6')
  const isSonnet46 = m === 'sonnet' || m.includes('sonnet-4-6')

  if (isDs46 && isDs1mMerged) return false

  return isDs46 || isSonnet46
}
