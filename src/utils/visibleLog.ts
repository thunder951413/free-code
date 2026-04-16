import { appendFileSync } from 'fs'
import { join } from 'path'
import { getOriginalCwd } from '../bootstrap/state.js'
import { writeToStderr } from './process.js'

export function appendVisibleLog(message: string): void {
  writeToStderr(`${message}\n`)
  try {
    const logPath = join(getOriginalCwd(), 'log.txt')
    appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`)
  } catch {
    // Logging should never break application flow.
  }
}
