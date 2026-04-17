/**
 * OpenAI API adapter for free-code.
 *
 * Converts between Anthropic Messages API format and OpenAI Chat Completions
 * format so the rest of the codebase (which speaks Anthropic protocol) can
 * transparently talk to OpenAI-compatible endpoints.
 *
 * Environment variables:
 * - CLAUDE_CODE_USE_OPENAI=1       — enable OpenAI provider
 * - OPENAI_API_KEY                 — API key (required)
 * - OPENAI_BASE_URL                — base URL (default: https://api.openai.com/v1)
 * - OPENAI_MODEL                   — model name override (default: gpt-4o)
 * - OPENAI_SMALL_FAST_MODEL        — small/fast model (default: gpt-4o-mini)
 */

import type Anthropic from '@anthropic-ai/sdk'
import type {
  BetaContentBlock,
  BetaMessage,
  BetaMessageStreamParams,
  BetaRawMessageStreamEvent,
  BetaStopReason,
  BetaToolChoiceAuto,
  BetaToolChoiceTool,
  BetaToolUnion,
  BetaUsage,
} from '@anthropic-ai/sdk/resources/beta/messages/messages.mjs'
import type { Stream } from '@anthropic-ai/sdk/streaming.mjs'
import { randomUUID } from 'crypto'
import OpenAI from 'openai'
import type {
  ChatCompletionChunk,
  ChatCompletionMessageParam,
  ChatCompletionTool,
} from 'openai/resources/chat/completions'
import type { Stream as OpenAIStream } from 'openai/streaming'
import { logForDebugging } from '../../utils/debug'
import { getInitialSettings } from '../../utils/settings/settings'
import { appendVisibleLog } from '../../utils/visibleLog.js'
import {
  getOpenAIModel,
  getOpenAISmallFastModel,
  mapModelToOpenAI,
} from '../../utils/model/openai'

// Model mapping is handled by utils/model/openai.ts

// ---------------------------------------------------------------------------
// Client creation
// ---------------------------------------------------------------------------

function maskApiKey(apiKey: string): string {
  if (apiKey.length <= 10) return '[redacted]'
  return `${apiKey.slice(0, 6)}...${apiKey.slice(-4)}`
}

function getChatCompletionsUrl(baseURL: string): string {
  return `${baseURL.replace(/\/+$/, '')}/chat/completions`
}

function emitVisibleOpenAILog(message: string): void {
  appendVisibleLog(message)
}

function describeOpenAIError(error: unknown): string {
  if (!(error instanceof Error)) {
    return String(error)
  }

  const details: string[] = [`name=${error.name}`, `message=${error.message}`]
  const errorWithDetails = error as Error & {
    status?: number
    code?: string
    type?: string
    request_id?: string
  }

  if (errorWithDetails.status !== undefined) {
    details.push(`status=${errorWithDetails.status}`)
  }
  if (errorWithDetails.code) {
    details.push(`code=${errorWithDetails.code}`)
  }
  if (errorWithDetails.type) {
    details.push(`type=${errorWithDetails.type}`)
  }
  if (errorWithDetails.request_id) {
    details.push(`request_id=${errorWithDetails.request_id}`)
  }

  return details.join(', ')
}

function describeToolChoice(
  toolChoice:
    | OpenAI.ChatCompletionCreateParamsStreaming['tool_choice']
    | OpenAI.ChatCompletionCreateParamsNonStreaming['tool_choice']
    | undefined,
): string {
  if (!toolChoice) {
    return 'default'
  }
  if (typeof toolChoice === 'string') {
    return toolChoice
  }
  if (toolChoice.type === 'function') {
    return `function:${toolChoice.function.name}`
  }
  return toolChoice.type
}

function resolveOpenAIToolChoice(
  toolChoice:
    | OpenAI.ChatCompletionCreateParamsStreaming['tool_choice']
    | OpenAI.ChatCompletionCreateParamsNonStreaming['tool_choice']
    | undefined,
  hasTools: boolean,
):
  | OpenAI.ChatCompletionCreateParamsStreaming['tool_choice']
  | OpenAI.ChatCompletionCreateParamsNonStreaming['tool_choice']
  | undefined {
  if (toolChoice) {
    return toolChoice
  }
  // OpenAI defaults to auto when tools are present, but some compatible
  // providers only trigger tool calling when the field is sent explicitly.
  return hasTools ? 'auto' : undefined
}

function getOpenAIClientConfig() {
  const settings = getInitialSettings()
  const apiKey = process.env.OPENAI_API_KEY || settings.openaiApiKey
  const apiKeySource = process.env.OPENAI_API_KEY
    ? 'env'
    : settings.openaiApiKey
      ? 'settings'
      : 'missing'
  const baseURL =
    process.env.OPENAI_BASE_URL ||
    settings.openaiBaseUrl ||
    'https://api.openai.com/v1'

  return { apiKey, apiKeySource, baseURL }
}

export async function getOpenAIClient(): Promise<OpenAI> {
  const { apiKey, apiKeySource, baseURL } = getOpenAIClientConfig()
  if (!apiKey) {
    throw new Error(
      'OPENAI_API_KEY (env) or openaiApiKey (settings) is required when using CLAUDE_CODE_USE_OPENAI=1',
    )
  }

  emitVisibleOpenAILog(
    `[OpenAI] client config: baseURL=${baseURL} endpoint=${getChatCompletionsUrl(baseURL)} apiKeySource=${apiKeySource} apiKey=${maskApiKey(apiKey)}`,
  )

  return new OpenAI({
    apiKey,
    baseURL,
    defaultHeaders: {
      'User-Agent': 'free-code/openai-adapter',
    },
    maxRetries: 0, // Retry handled by withRetry in claude.ts
    timeout: parseInt(process.env.API_TIMEOUT_MS || String(600 * 1000), 10),
  })
}

// ---------------------------------------------------------------------------
// Anthropic → OpenAI request conversion
// ---------------------------------------------------------------------------

/**
 * Convert Anthropic system prompt blocks to a single OpenAI system message string.
 */
function convertSystemPrompt(
  system: BetaMessageStreamParams['system'],
): string {
  if (!system) return ''
  if (typeof system === 'string') return system

  return system
    .map(block => {
      if (block.type === 'text') return block.text
      return ''
    })
    .filter(Boolean)
    .join('\n\n')
}

/**
 * Convert Anthropic tool_choice to OpenAI tool_choice format.
 */
function convertToolChoice(
  toolChoice: BetaMessageStreamParams['tool_choice'],
): OpenAI.ChatCompletionCreateParamsStreaming['tool_choice'] | undefined {
  if (!toolChoice) return undefined

  if (typeof toolChoice === 'string') {
    // "auto" | "any" | "none"
    if (toolChoice === 'any') return 'required'
    return toolChoice // "auto" | "none" map directly
  }

  // { type: "tool", name: "..." } or { type: "auto" }
  const tc = toolChoice as BetaToolChoiceTool | BetaToolChoiceAuto
  if (tc.type === 'tool') {
    return { type: 'function', function: { name: tc.name } }
  }
  if (tc.type === 'auto') return 'auto'

  return undefined
}

/**
 * Convert Anthropic BetaToolUnion[] to OpenAI ChatCompletionTool[].
 */
function convertTools(
  tools: BetaMessageStreamParams['tools'],
): ChatCompletionTool[] | undefined {
  if (!tools || tools.length === 0) return undefined

  const openAITools = tools
    .map(tool => {
      if (!('input_schema' in tool) || !tool.input_schema || !('name' in tool)) {
        // Skip Anthropic-specific / server-side tools that have no OpenAI function equivalent.
        return null
      }

      return {
        type: 'function' as const,
        function: {
          name: tool.name,
          description: tool.description || '',
          parameters: tool.input_schema as Record<string, unknown>,
        },
      }
    })
    .filter(Boolean) as ChatCompletionTool[]

  return openAITools.length > 0 ? openAITools : undefined
}

/**
 * Convert Anthropic content blocks to a single string or content array for OpenAI.
 */
function convertContentBlocks(
  content: BetaMessageStreamParams['messages'][number]['content'],
): string | OpenAI.ChatCompletionContentPart[] {
  if (typeof content === 'string') return content

  const parts: OpenAI.ChatCompletionContentPart[] = []
  for (const block of content) {
    switch (block.type) {
      case 'text':
        parts.push({ type: 'text', text: block.text })
        break
      case 'image':
        if (block.source.type === 'base64') {
          parts.push({
            type: 'image_url',
            image_url: {
              url: `data:${block.source.media_type};base64,${block.source.data}`,
            },
          })
        }
        break
      case 'tool_use':
        // Handled separately in message conversion
        break
      case 'tool_result':
        // Handled separately in message conversion
        break
      default:
        // Skip unsupported block types (thinking, redacted_thinking, etc.)
        break
    }
  }

  // If only text, return as string for efficiency
  if (parts.length === 1 && parts[0].type === 'text') {
    return parts[0].text
  }
  return parts
}

function convertToolResultContent(content: unknown): string {
  if (typeof content === 'string') {
    return content
  }
  if (!Array.isArray(content)) {
    return ''
  }
  return content
    .map(block => {
      if (typeof block !== 'object' || block === null || !('type' in block)) {
        return ''
      }
      if (block.type === 'text' && 'text' in block && typeof block.text === 'string') {
        return block.text
      }
      if (block.type === 'image') {
        return '[image]'
      }
      return ''
    })
    .filter(Boolean)
    .join('\n')
}

function parseToolArguments(
  toolName: string,
  toolCallId: string,
  rawArguments: string | undefined,
): Record<string, unknown> {
  if (!rawArguments) {
    return {}
  }
  try {
    const parsed = JSON.parse(rawArguments) as unknown
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>
    }
  } catch (error) {
    emitVisibleOpenAILog(
      `[OpenAI] tool argument parse error: tool=${toolName} toolCallId=${toolCallId} ${describeOpenAIError(error)}`,
    )
  }
  return {}
}

/**
 * Convert Anthropic messages array to OpenAI messages array.
 *
 * Key differences:
 * - Anthropic: system is separate; OpenAI: system is a message role
 * - Anthropic: tool_use is a content block in assistant; OpenAI: tool_calls array
 * - Anthropic: tool_result is a content block in user; OpenAI: role="tool" message
 */
function convertMessages(
  messages: BetaMessageStreamParams['messages'],
  systemText: string,
): ChatCompletionMessageParam[] {
  const result: ChatCompletionMessageParam[] = []

  // Add system message first
  if (systemText) {
    result.push({ role: 'system', content: systemText })
  }

  for (const msg of messages) {
    if (msg.role === 'user') {
      // User messages may contain tool_result blocks which need to become
      // separate role="tool" messages in OpenAI format
      const content = msg.content
      if (typeof content === 'string') {
        result.push({ role: 'user', content })
        continue
      }

      // Separate tool_result blocks from regular content
      const toolResults: Array<{
        tool_use_id: string
        content: string
      }> = []
      const regularParts: OpenAI.ChatCompletionContentPart[] = []

      for (const block of content) {
        if (block.type === 'tool_result') {
          toolResults.push({
            tool_use_id: block.tool_use_id,
            content: convertToolResultContent(block.content),
          })
        } else if (block.type === 'text') {
          regularParts.push({ type: 'text', text: block.text })
        } else if (block.type === 'image') {
          if (block.source.type === 'base64') {
            regularParts.push({
              type: 'image_url',
              image_url: {
                url: `data:${block.source.media_type};base64,${block.source.data}`,
              },
            })
          }
        }
      }

      // Tool results must immediately follow the assistant tool_calls message.
      // If the original Anthropic user message also contains normal text/media,
      // emit tool messages first and then a user message.
      for (const tr of toolResults) {
        result.push({
          role: 'tool',
          tool_call_id: tr.tool_use_id,
          content: tr.content,
        })
      }

      if (regularParts.length > 0) {
        if (regularParts.length === 1 && regularParts[0].type === 'text') {
          result.push({ role: 'user', content: regularParts[0].text })
        } else {
          result.push({ role: 'user', content: regularParts })
        }
      }
    } else if (msg.role === 'assistant') {
      const content = msg.content
      if (typeof content === 'string') {
        result.push({ role: 'assistant', content })
        continue
      }

      // Separate tool_use blocks from text content
      const toolCalls: OpenAI.ChatCompletionMessageToolCall[] = []
      let textContent = ''

      for (const block of content) {
        if (block.type === 'tool_use') {
          toolCalls.push({
            id: block.id,
            type: 'function',
            function: {
              name: block.name,
              arguments:
                typeof block.input === 'string'
                  ? block.input
                  : JSON.stringify(block.input),
            },
          })
        } else if (block.type === 'text') {
          textContent += block.text
        } else if (block.type === 'thinking' || block.type === 'redacted_thinking') {
          // Skip thinking blocks - OpenAI doesn't support them in messages
        }
      }

      const assistantMsg: OpenAI.ChatCompletionAssistantMessageParam = {
        role: 'assistant',
        ...(textContent && { content: textContent }),
        ...(toolCalls.length > 0 && { tool_calls: toolCalls }),
      }
      result.push(assistantMsg)
    }
  }

  return result
}

// ---------------------------------------------------------------------------
// OpenAI → Anthropic response conversion (streaming)
// ---------------------------------------------------------------------------

type OpenAIStreamState = {
  nextContentBlockIndex: number
  currentTextBlockIndex: number | null
  messageStarted: boolean
  hasOpenTextBlock: boolean
  toolCallIndexMap: Map<number, number>
}

function createOpenAIStreamState(): OpenAIStreamState {
  return {
    nextContentBlockIndex: 0,
    currentTextBlockIndex: null,
    messageStarted: false,
    hasOpenTextBlock: false,
    toolCallIndexMap: new Map<number, number>(),
  }
}

/**
 * Convert an OpenAI streaming chunk into Anthropic BetaRawMessageStreamEvent(s).
 *
 * OpenAI sends events like:
 *   { choices: [{ delta: { role: "assistant" } }] }              — start
 *   { choices: [{ delta: { content: "Hello" } }] }               — text
 *   { choices: [{ delta: { tool_calls: [{ function: { name: "x", arguments: "{" }] } }] }] } — tool start
 *   { choices: [{ delta: { tool_calls: [{ function: { arguments: "..."} }] } }] }              — tool delta
 *   { choices: [{ finish_reason: "stop" }] }                      — end
 *
 * Anthropic events:
 *   message_start, content_block_start, content_block_delta,
 *   content_block_stop, message_delta, message_stop
 */
function convertChunkToEvents(
  chunk: ChatCompletionChunk,
  model: string,
  state: OpenAIStreamState,
): BetaRawMessageStreamEvent[] {
  const events: BetaRawMessageStreamEvent[] = []
  const choice = chunk.choices?.[0]
  if (!choice) return events

  // --- message_start ---
  if (!state.messageStarted) {
    state.messageStarted = true
    events.push({
      type: 'message_start',
      message: {
        id: chunk.id || `msg_${randomUUID().replace(/-/g, '').slice(0, 24)}`,
        type: 'message',
        role: 'assistant',
        content: [],
        model,
        stop_reason: null,
        stop_sequence: null,
        usage: { input_tokens: 0, output_tokens: 0 },
      } as BetaMessage,
    })
  }

  const delta = choice.delta

  // --- text content ---
  if (delta?.content != null && delta.content !== '') {
    if (state.currentTextBlockIndex === null) {
      state.currentTextBlockIndex = state.nextContentBlockIndex++
      events.push({
        type: 'content_block_start',
        index: state.currentTextBlockIndex,
        content_block: { type: 'text', text: '', citations: null } as BetaContentBlock,
      })
      state.hasOpenTextBlock = true
    }

    events.push({
      type: 'content_block_delta',
      index: state.currentTextBlockIndex,
      delta: { type: 'text_delta', text: delta.content },
    })
  }

  // --- tool calls ---
  if (delta?.tool_calls) {
    for (const tc of delta.tool_calls) {
      const tcIndex = tc.index ?? 0
      const existingBlockIdx = state.toolCallIndexMap.get(tcIndex)

      // Tool call start (has a name)
      if (tc.function?.name) {
        if (existingBlockIdx !== undefined) {
          emitVisibleOpenAILog(
            `[OpenAI] tool call start reused: model=${model} index=${tcIndex} block_index=${existingBlockIdx} name=${tc.function.name} args_chars=${tc.function.arguments?.length ?? 0}`,
          )
          if (tc.function.arguments) {
            events.push({
              type: 'content_block_delta',
              index: existingBlockIdx,
              delta: {
                type: 'input_json_delta',
                partial_json: tc.function.arguments,
              },
            })
          }
          continue
        }
        emitVisibleOpenAILog(
          `[OpenAI] tool call start: model=${model} index=${tcIndex} id=${tc.id ?? 'generated'} name=${tc.function.name} args_chars=${tc.function.arguments?.length ?? 0}`,
        )
        // Close any open text block first
        if (state.hasOpenTextBlock && state.currentTextBlockIndex !== null) {
          events.push({
            type: 'content_block_stop',
            index: state.currentTextBlockIndex,
          })
          state.currentTextBlockIndex = null
          state.hasOpenTextBlock = false
        }

        const blockIdx = state.nextContentBlockIndex++
        const toolCallId = tc.id || `toolu_${randomUUID().replace(/-/g, '').slice(0, 24)}`

        // Map OpenAI tool call index to Anthropic content block index
        state.toolCallIndexMap.set(tcIndex, blockIdx)

        events.push({
          type: 'content_block_start',
          index: blockIdx,
          content_block: {
            type: 'tool_use',
            id: toolCallId,
            name: tc.function.name,
            input: {},
          },
        })

        // If arguments come with the start chunk
        if (tc.function.arguments) {
          events.push({
            type: 'content_block_delta',
            index: blockIdx,
            delta: {
              type: 'input_json_delta',
              partial_json: tc.function.arguments,
            },
          })
        }
      }
      // Tool call continuation (arguments only)
      else if (tc.function?.arguments) {
        if (existingBlockIdx === undefined) {
          emitVisibleOpenAILog(
            `[OpenAI] tool call continuation dropped: model=${model} index=${tcIndex} reason=missing_block_index args_chars=${tc.function.arguments.length}`,
          )
          continue
        }
        emitVisibleOpenAILog(
          `[OpenAI] tool call delta: model=${model} index=${tcIndex} block_index=${existingBlockIdx} args_chars=${tc.function.arguments.length}`,
        )
        events.push({
          type: 'content_block_delta',
          index: existingBlockIdx,
          delta: {
            type: 'input_json_delta',
            partial_json: tc.function.arguments,
          },
        })
      }
    }
  }

  return events
}

function choiceHasPayload(choice: ChatCompletionChunk['choices'][number] | undefined): boolean {
  if (!choice) {
    return false
  }

  return Boolean(
    (choice.delta?.content != null && choice.delta.content !== '') ||
      (choice.delta?.tool_calls && choice.delta.tool_calls.length > 0),
  )
}

function createFinishEvents(
  finishReason: NonNullable<ChatCompletionChunk['choices'][number]['finish_reason']>,
  state: OpenAIStreamState,
): BetaRawMessageStreamEvent[] {
  const events: BetaRawMessageStreamEvent[] = []
  const hadPendingToolCalls = state.toolCallIndexMap.size > 0

  // Close any open text block.
  if (state.hasOpenTextBlock && state.currentTextBlockIndex !== null) {
    events.push({
      type: 'content_block_stop',
      index: state.currentTextBlockIndex,
    })
    state.currentTextBlockIndex = null
    state.hasOpenTextBlock = false
  }

  for (const blockIdx of [...state.toolCallIndexMap.values()].sort((a, b) => a - b)) {
    events.push({
      type: 'content_block_stop',
      index: blockIdx,
    })
  }
  state.toolCallIndexMap.clear()

  const stopReason: BetaStopReason =
    finishReason === 'tool_calls' || hadPendingToolCalls ? 'tool_use' : 'end_turn'

  if (finishReason !== 'tool_calls' && hadPendingToolCalls) {
    emitVisibleOpenAILog(
      `[OpenAI] finish_reason compatibility override: finish_reason=${finishReason} pending_tool_calls=yes mapped_stop_reason=tool_use`,
    )
  }

  events.push({
    type: 'message_delta',
    context_management: null,
    delta: { container: null, stop_reason: stopReason, stop_sequence: null },
    usage: { output_tokens: 0 } as unknown as BetaUsage,
  })

  events.push({ type: 'message_stop' })
  return events
}

// ---------------------------------------------------------------------------
// Public API: create an Anthropic-compatible streaming interface
// ---------------------------------------------------------------------------

/**
 * Execute a streaming request against the OpenAI API and yield events
 * in Anthropic's BetaRawMessageStreamEvent format.
 *
 * This is the main entry point called from client.ts.
 */
export async function* streamWithOpenAI(
  params: BetaMessageStreamParams,
  signal: AbortSignal,
): AsyncGenerator<BetaRawMessageStreamEvent, void> {
  const client = await getOpenAIClient()
  const { baseURL } = getOpenAIClientConfig()
  const model = mapModelToOpenAI(params.model)

  const systemText = convertSystemPrompt(params.system)
  const messages = convertMessages(params.messages, systemText)
  const tools = convertTools(params.tools)
  const toolChoice = convertToolChoice(params.tool_choice)
  const resolvedToolChoice = resolveOpenAIToolChoice(toolChoice, Boolean(tools))

  const requestParams: OpenAI.ChatCompletionCreateParamsStreaming = {
    model,
    messages,
    stream: true,
    ...(params.max_tokens && { max_tokens: params.max_tokens }),
    ...(params.temperature !== undefined && { temperature: params.temperature }),
    ...(tools && { tools }),
    ...(resolvedToolChoice && { tool_choice: resolvedToolChoice }),
    ...(params.stop_sequences && { stop: params.stop_sequences }),
  }

  logForDebugging(`[OpenAI] Streaming request: model=${model}, messages=${messages.length}, tools=${tools?.length ?? 0}`)
  emitVisibleOpenAILog(
    `[OpenAI] streaming request: model=${model} endpoint=${getChatCompletionsUrl(baseURL)} messages=${messages.length} tools=${tools?.length ?? 0} tool_choice=${describeToolChoice(resolvedToolChoice)} max_tokens=${params.max_tokens ?? 'default'}`,
  )

  const streamState = createOpenAIStreamState()
  let pendingFinishReason:
    | NonNullable<ChatCompletionChunk['choices'][number]['finish_reason']>
    | undefined

  try {
    const stream = await client.chat.completions.create(requestParams, {
      signal,
    })

    for await (const chunk of stream) {
      const choice = chunk.choices?.[0]
      const hasPayload = choiceHasPayload(choice)
      if (pendingFinishReason && hasPayload) {
        emitVisibleOpenAILog(
          `[OpenAI] protocol violation: received payload after finish_reason=${pendingFinishReason}; deferring stream close`,
        )
        pendingFinishReason = undefined
      }
      if (choice?.finish_reason || choice?.delta?.tool_calls?.length) {
        emitVisibleOpenAILog(
          `[OpenAI] streaming chunk: model=${model} finish_reason=${choice?.finish_reason ?? 'none'} tool_calls=${choice?.delta?.tool_calls?.length ?? 0}`,
        )
      }
      const events = convertChunkToEvents(chunk, model, streamState)
      for (const event of events) {
        yield event
      }
      if (choice?.finish_reason) {
        pendingFinishReason = choice.finish_reason
      }
    }

    if (pendingFinishReason) {
      emitVisibleOpenAILog(
        `[OpenAI] finalizing deferred finish_reason=${pendingFinishReason}`,
      )
      for (const event of createFinishEvents(pendingFinishReason, streamState)) {
        yield event
      }
    }
  } catch (error) {
    emitVisibleOpenAILog(
      `[OpenAI] streaming error: model=${model} endpoint=${getChatCompletionsUrl(baseURL)} ${describeOpenAIError(error)}`,
    )
    throw error
  }
}

/**
 * Execute a non-streaming request against the OpenAI API and return
 * an Anthropic BetaMessage.
 */
export async function createWithOpenAI(
  params: BetaMessageStreamParams,
  signal: AbortSignal,
): Promise<BetaMessage> {
  const client = await getOpenAIClient()
  const { baseURL } = getOpenAIClientConfig()
  const model = mapModelToOpenAI(params.model)

  const systemText = convertSystemPrompt(params.system)
  const messages = convertMessages(params.messages, systemText)
  const tools = convertTools(params.tools)
  const toolChoice = convertToolChoice(params.tool_choice)
  const resolvedToolChoice = resolveOpenAIToolChoice(toolChoice, Boolean(tools))

  const requestParams: OpenAI.ChatCompletionCreateParamsNonStreaming = {
    model,
    messages,
    ...(params.max_tokens && { max_tokens: params.max_tokens }),
    ...(params.temperature !== undefined && { temperature: params.temperature }),
    ...(tools && { tools }),
    ...(resolvedToolChoice && { tool_choice: resolvedToolChoice }),
    ...(params.stop_sequences && { stop: params.stop_sequences }),
  }

  logForDebugging(`[OpenAI] Non-streaming request: model=${model}, messages=${messages.length}`)
  emitVisibleOpenAILog(
    `[OpenAI] non-streaming request: model=${model} endpoint=${getChatCompletionsUrl(baseURL)} messages=${messages.length} tools=${tools?.length ?? 0} tool_choice=${describeToolChoice(resolvedToolChoice)} max_tokens=${params.max_tokens ?? 'default'}`,
  )

  let response: OpenAI.ChatCompletion
  try {
    response = await client.chat.completions.create(requestParams, {
      signal,
    })
  } catch (error) {
    emitVisibleOpenAILog(
      `[OpenAI] non-streaming error: model=${model} endpoint=${getChatCompletionsUrl(baseURL)} ${describeOpenAIError(error)}`,
    )
    throw error
  }

  const choice = response.choices[0]
  if (!choice) throw new Error('No response from OpenAI')
  emitVisibleOpenAILog(
    `[OpenAI] non-streaming response: model=${model} finish_reason=${choice.finish_reason ?? 'none'} tool_calls=${choice.message.tool_calls?.length ?? 0} text=${choice.message.content ? 'yes' : 'no'}`,
  )

  // Convert OpenAI response to Anthropic BetaMessage
  const content: BetaContentBlock[] = []

  // Text content
  if (choice.message.content) {
    content.push({ type: 'text', text: choice.message.content, citations: null } as BetaContentBlock)
  }

  // Tool calls
  if (choice.message.tool_calls) {
    for (const tc of choice.message.tool_calls) {
      content.push({
        type: 'tool_use',
        id: tc.id,
        name: tc.function.name,
        input: parseToolArguments(tc.function.name, tc.id, tc.function.arguments),
      } as BetaContentBlock)
    }
  }

  let stopReason: BetaStopReason = 'end_turn'
  if (choice.message.tool_calls && choice.message.tool_calls.length > 0) {
    stopReason = 'tool_use'
    if (choice.finish_reason !== 'tool_calls') {
      emitVisibleOpenAILog(
        `[OpenAI] non-streaming finish_reason compatibility override: finish_reason=${choice.finish_reason ?? 'none'} tool_calls=${choice.message.tool_calls.length} mapped_stop_reason=tool_use`,
      )
    }
  }

  return {
    id: response.id || `msg_${randomUUID().replace(/-/g, '').slice(0, 24)}`,
    type: 'message',
    role: 'assistant',
    content,
    model: response.model || model,
    stop_reason: stopReason,
    stop_sequence: null,
    usage: {
      input_tokens: response.usage?.prompt_tokens ?? 0,
      output_tokens: response.usage?.completion_tokens ?? 0,
    },
  } as BetaMessage
}

// ---------------------------------------------------------------------------
// API key verification
// ---------------------------------------------------------------------------

/**
 * Verify the OpenAI API key by making a minimal request.
 */
export async function verifyOpenAIApiKey(): Promise<boolean> {
  const { baseURL } = getOpenAIClientConfig()
  try {
    const client = await getOpenAIClient()
    const model = getOpenAISmallFastModel()
    emitVisibleOpenAILog(
      `[OpenAI] verify request: model=${model} endpoint=${getChatCompletionsUrl(baseURL)}`,
    )
    await client.chat.completions.create({
      model,
      messages: [{ role: 'user', content: 'test' }],
      max_tokens: 1,
    })
    return true
  } catch (error) {
    emitVisibleOpenAILog(
      `[OpenAI] verify error: endpoint=${getChatCompletionsUrl(baseURL)} ${describeOpenAIError(error)}`,
    )
    return false
  }
}
