// DMDARK: the resolver is the one thing that decides which palette renders, so
// it is the one thing this task's contract pins in the suite. What is under
// test here is the decision, not the palette - the palette is what the visual
// harness measures against a real browser - so these tests drive the three
// states, the System resolution, the persistence and the meta, and they stub
// `matchMedia` because jsdom has no preference of its own.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import {
  THEME_ATTRIBUTE,
  THEME_META_COLORS,
  THEME_STORAGE_KEY,
  applyTheme,
  initTheme,
  isThemeChoice,
  readThemeChoice,
  resolveDark,
  resolveTheme,
} from './theme'

/** A `matchMedia` the test can flip, because the whole point of the System
 *  state is that the OS preference moves while the app is open. The object is
 *  a shape shim rather than a class, the way `setup-tests.ts`'s own stub is,
 *  because jsdom has no preference of its own. */
function stubMatchMedia(initial: boolean) {
  let matches = initial
  const listeners: Array<(event: { matches: boolean }) => void> = []
  const mql = {
    get matches() {
      return matches
    },
    media: '(prefers-color-scheme: dark)',
    onchange: null,
    addEventListener: (_type: string, listener: (event: { matches: boolean }) => void) =>
      listeners.push(listener),
    removeEventListener: (
      _type: string,
      listener: (event: { matches: boolean }) => void,
    ) => {
      const at = listeners.indexOf(listener)
      if (at >= 0) listeners.splice(at, 1)
    },
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  } as unknown as MediaQueryList
  vi.stubGlobal('matchMedia', () => mql)
  return {
    mql,
    flip: (next: boolean) => {
      matches = next
      listeners.forEach((listener) => listener({ matches: next }))
    },
  }
}

describe('theme resolver', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute(THEME_ATTRIBUTE)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('treats an empty store as System, and a stored choice as itself', () => {
    expect(readThemeChoice()).toBe('system')

    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    expect(readThemeChoice()).toBe('dark')
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(readThemeChoice()).toBe('light')
  })

  it('falls back to System for a value this build does not name', () => {
    // A future build's value in the store is the zero-config default, not a
    // state to guess at.
    localStorage.setItem(THEME_STORAGE_KEY, 'oled-when')
    expect(readThemeChoice()).toBe('system')
  })

  it('resolves Light and Dark as the analyst stated them, and System as the OS', () => {
    expect(resolveDark('light', true)).toBe(false)
    expect(resolveDark('dark', false)).toBe(true)
    // System is the one state that asks the OS - the whole reason it exists.
    expect(resolveDark('system', true)).toBe(true)
    expect(resolveDark('system', false)).toBe(false)
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
  })

  it('writes the attribute and persists the choice', () => {
    stubMatchMedia(false)
    expect(applyTheme('dark')).toBe('dark')

    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })

  it('resolves System through the OS preference at apply time', () => {
    const media = stubMatchMedia(true)

    expect(applyTheme('system')).toBe('dark')
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('dark')

    media.flip(false)
    // A re-apply reads the preference again, which is what a running app needs
    // when the OS moves.
    expect(applyTheme('system')).toBe('light')
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')
  })

  it('keeps the meta theme-color on the resolved appearance', () => {
    stubMatchMedia(false)
    document.head.innerHTML = `<meta name="theme-color" content="${THEME_META_COLORS.light}" />`

    applyTheme('light')
    const light = document.querySelector('meta[name="theme-color"]')
    expect(light && (light as HTMLMetaElement).content).toBe(THEME_META_COLORS.light)

    applyTheme('dark')
    const dark = document.querySelector('meta[name="theme-color"]')
    expect(dark && (dark as HTMLMetaElement).content).toBe(THEME_META_COLORS.dark)
  })

  it('leaves the meta alone when the document does not carry one', () => {
    // The bootstrap writes it and index.html ships it, but a host without one
    // must not crash the resolver over a chrome detail.
    stubMatchMedia(false)
    expect(() => applyTheme('dark')).not.toThrow()
  })

  it('re-themes on an OS change while System is held, and holds a stated choice', () => {
    const media = stubMatchMedia(false)
    localStorage.setItem(THEME_STORAGE_KEY, 'system')
    initTheme()
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')

    media.flip(true)
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('dark')

    media.flip(false)
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')

    // The analyst's own choice does not move with the OS - that is why Light
    // and Dark are separate states from System.
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    media.flip(true)
    expect(document.documentElement.getAttribute(THEME_ATTRIBUTE)).toBe('light')
  })

  it('isThemeChoice admits only the three states', () => {
    expect(isThemeChoice('light')).toBe(true)
    expect(isThemeChoice('dark')).toBe(true)
    expect(isThemeChoice('system')).toBe(true)
    expect(isThemeChoice(null)).toBe(false)
    expect(isThemeChoice('oled')).toBe(false)
  })
})
