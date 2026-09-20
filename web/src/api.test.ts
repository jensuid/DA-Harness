// The typed client's one job at the boundary: turn whatever the core sent into
// an error the UI can show, without throwing a second error inside the handler.

import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, getCase } from './api'
import { messageOf } from './CaseList'

// The desktop bundle talks to an absolute URL and the browser bundle to /api;
// either way, fetch is what stands between the UI and the core.
function respond(status: number, body: string, contentType: string) {
  return Promise.resolve(
    new Response(body, { status, headers: { 'content-type': contentType } }),
  )
}

// A rejection the caller can read by name. await + instanceof keeps the type
// honest, which is what lets the assertions below talk about ApiError fields.
async function failureOf(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    if (error instanceof ApiError) return error
    throw error
  }
  throw new Error('expected the request to fail, and it did not')
}

const ORIGINAL_FETCH = globalThis.fetch

afterEach(() => {
  globalThis.fetch = ORIGINAL_FETCH
  vi.restoreAllMocks()
})

describe('api client', () => {
  it('carries a 500 envelope id so the UI can quote it', async () => {
    // The id is the key to that fault's traceback in the core's log.
    globalThis.fetch = vi
      .fn()
      .mockReturnValue(
        respond(500, '{"detail":"internal error","request_id":"abc123"}', 'application/json'),
      )

    const error = await failureOf(getCase('nope'))
    expect(error.status).toBe(500)
    expect(error.message).toBe('internal error')
    expect(error.requestId).toBe('abc123')
  })

  it('keeps a 4xx detail and never invents an id', async () => {
    globalThis.fetch = vi
      .fn()
      .mockReturnValue(respond(404, '{"detail":"case not found"}', 'application/json'))

    const error = await failureOf(getCase('nope'))
    expect(error.status).toBe(404)
    expect(error.message).toBe('case not found')
    expect(error.requestId).toBeUndefined()
  })

  it('unwraps a nested detail the agent 409 sends as an object', async () => {
    // The agent's approve and reject answer 409 with an object as the detail -
    // {"detail": {...}, "expected": ..., "given": ...} - because the refusal
    // names the pending step the approval should have carried. The inner
    // sentence is the actionable one; without this the UI would show
    // "[object Object]" for a stale approval.
    globalThis.fetch = vi.fn().mockReturnValue(
      respond(
        409,
        JSON.stringify({
          detail: {
            detail: "the step id is not this case's pending step",
            expected: 's8',
            given: 's7',
          },
        }),
        'application/json',
      ),
    )

    const error = await failureOf(getCase('c1'))
    expect(error.status).toBe(409)
    expect(error.message).toBe("the step id is not this case's pending step")
  })

  it('survives a 500 that is not JSON', async () => {
    // A proxy, a timeout, or an older core can still answer plain text. The
    // message is the text and the id is absent - but nothing throws twice.
    globalThis.fetch = vi.fn().mockReturnValue(respond(502, 'Bad Gateway', 'text/plain'))

    const error = await failureOf(getCase('nope'))
    expect(error.status).toBe(502)
    expect(error.message).toBe('Bad Gateway')
    expect(error.requestId).toBeUndefined()
  })

  it('surfaces the id in the message a user reads', () => {
    // "error 3f239488" is quotable and "HTTP 500" is not.
    const error = new ApiError(500, 'internal error', '3f239488576c453cb61b9f38716d1bb7')
    expect(messageOf(error)).toBe('internal error (HTTP 500 error 3f239488)')
    expect(messageOf(new ApiError(404, 'case not found'))).toBe('case not found (HTTP 404)')
  })
})
