/**
 * OpenAI model configuration and utilities.
 *
 * Provides model name mapping, context window sizes, and token limits
 * for OpenAI models used through the native adapter.
 */

import { getAPIProvider } from './providers.js'
import { getInitialSettings } from '../settings/settings.js'

// ---------------------------------------------------------------------------
// Model defaults
// ---------------------------------------------------------------------------

const DEFAULT_OPENAI_MODEL = 'gpt-4o'

export function getOpenAIModel(): string {
  const settings = getInitialSettings()
  return process.env.OPENAI_MODEL || settings.openaiModel || DEFAULT_OPENAI_MODEL
}

export function getOpenAISmallFastModel(): string {
  const settings = getInitialSettings()
  return (
    process.env.OPENAI_SMALL_FAST_MODEL ||
    settings.openaiSmallFastModel ||
    getOpenAIModel()
  )
}

// ---------------------------------------------------------------------------
// Model mapping
// ---------------------------------------------------------------------------

/**
 * Map an Anthropic-style model alias or name to an OpenAI model name.
 * - Known Claude model strings → configured OPENAI_MODEL
 * - Known aliases (sonnet, Ds, haiku) → configured OPENAI_MODEL
 * - Everything else → pass through (user may set a custom model name)
 */
export function mapModelToOpenAI(model: string): string {
  if (getAPIProvider() !== 'openai') return model

  // Claude model strings
  if (model.startsWith('claude-')) {
    return getOpenAIModel()
  }
  // Aliases
  if (['sonnet', 'Ds', 'haiku'].includes(model)) {
    return getOpenAIModel()
  }
  // Pass through custom model names
  return model
}

// ---------------------------------------------------------------------------
// Context window and token limits
// ---------------------------------------------------------------------------

interface OpenAIModelConfig {
  contextWindow: number
  maxOutputTokens: number
}

const OPENAI_MODEL_CONFIGS: Record<string, OpenAIModelConfig> = {
  'deepseek-chat': { contextWindow: 128_000, maxOutputTokens: 8_192 },
  'deepseek-reasoner': { contextWindow: 128_000, maxOutputTokens: 8_192 },
  'gpt-4o': { contextWindow: 128_000, maxOutputTokens: 16_384 },
  'gpt-4o-mini': { contextWindow: 128_000, maxOutputTokens: 16_384 },
  'gpt-4o-2024-08-06': { contextWindow: 128_000, maxOutputTokens: 16_384 },
  'gpt-4o-2024-05-13': { contextWindow: 128_000, maxOutputTokens: 4_096 },
  'gpt-4-turbo': { contextWindow: 128_000, maxOutputTokens: 4_096 },
  'gpt-4-turbo-preview': { contextWindow: 128_000, maxOutputTokens: 4_096 },
  'gpt-4-0125-preview': { contextWindow: 128_000, maxOutputTokens: 4_096 },
  'gpt-4-1106-preview': { contextWindow: 128_000, maxOutputTokens: 4_096 },
  'gpt-4': { contextWindow: 8_192, maxOutputTokens: 8_192 },
  'gpt-4-32k': { contextWindow: 32_768, maxOutputTokens: 32_768 },
  'gpt-3.5-turbo': { contextWindow: 16_385, maxOutputTokens: 4_096 },
  'gpt-3.5-turbo-16k': { contextWindow: 16_385, maxOutputTokens: 4_096 },
  'o1': { contextWindow: 200_000, maxOutputTokens: 100_000 },
  'o1-mini': { contextWindow: 128_000, maxOutputTokens: 65_536 },
  'o1-preview': { contextWindow: 128_000, maxOutputTokens: 32_768 },
  'o3-mini': { contextWindow: 200_000, maxOutputTokens: 100_000 },
}

const DEFAULT_CONFIG: OpenAIModelConfig = {
  contextWindow: 128_000,
  maxOutputTokens: 16_384,
}

/**
 * Get the context window size for an OpenAI model.
 */
export function getOpenAIContextWindow(model: string): number {
  return OPENAI_MODEL_CONFIGS[model]?.contextWindow ?? DEFAULT_CONFIG.contextWindow
}

/**
 * Get the max output tokens for an OpenAI model.
 */
export function getOpenAIMaxOutputTokens(model: string): number {
  return OPENAI_MODEL_CONFIGS[model]?.maxOutputTokens ?? DEFAULT_CONFIG.maxOutputTokens
}

/**
 * Check if a model name looks like an OpenAI model.
 */
export function isOpenAIModel(model: string): boolean {
  return (
    model.startsWith('deepseek-') ||
    model.startsWith('gpt-') ||
    model.startsWith('o1') ||
    model.startsWith('o3') ||
    model.startsWith('chatgpt-')
  )
}
