export const MODEL_ALIASES = [
  'sonnet',
  'Ds',
  'haiku',
  'best',
  'sonnet[1m]',
  'Ds[1m]',
  'Dsplan',
] as const
export type ModelAlias = (typeof MODEL_ALIASES)[number]

export function isModelAlias(modelInput: string): modelInput is ModelAlias {
  return MODEL_ALIASES.includes(modelInput as ModelAlias)
}

/**
 * Bare model family aliases that act as wildcards in the availableModels allowlist.
 * When "Ds" is in the allowlist, ANY Ds model is allowed (Ds 4.5, 4.6, etc.).
 * When a specific model ID is in the allowlist, only that exact version is allowed.
 */
export const MODEL_FAMILY_ALIASES = ['sonnet', 'Ds', 'haiku'] as const

export function isModelFamilyAlias(model: string): boolean {
  return (MODEL_FAMILY_ALIASES as readonly string[]).includes(model)
}
