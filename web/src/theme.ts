// DMDARK: the appearance resolver. The workspace had one appearance, and the
// analyst works long sessions on data - the reference is a modern IDE, where
// a dark surface is the default expectation, and the Tauri window's own chrome
// already follows the OS, so a light body under a dark macOS titlebar was a
// visible mismatch rather than a preference.
//
// ONE mechanism: a `data-theme` attribute on <html>. CSS redefines the same
// tokens under `[data-theme="dark"]`, and every surface reads a token - so
// this module is the only thing that decides which palette renders. There is
// deliberately no `@media (prefers-color-scheme)` rule anywhere in the
// stylesheet racing a class: one place to test, one place to be wrong.
//
// Three states, because two were both wrong. Auto-only would not let the
// analyst take dark without changing the whole system; toggle-only loses the
// zero-config default a native app whose chrome tracks the OS wants. System is
// the default, Light and Dark are the analyst's own, and System is the one
// state that can move after launch - the OS preference changing while the app
// is open re-themes it, which is the whole point of choosing System.
//
// Persistence is localStorage in the webview, not a store plugin and not a
// file: an appearance is a preference the window owns, DEC-001 keeps the
// browser side off the filesystem, and nothing the core serves depends on it.

/** The three states the Settings dialog offers. */
export type ThemeChoice = 'light' | 'dark' | 'system'

/** The two palettes that actually render; System resolves to one of these. */
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'dah-theme'
export const THEME_ATTRIBUTE = 'data-theme'
export const THEME_QUERY = '(prefers-color-scheme: dark)'
export const THEME_META_NAME = 'theme-color'

/** The meta theme-color for each resolved appearance. It is the page's own
 * background, so the chrome around the document - a PWA-style toolbar, an
 * installed web app - matches the document instead of framing it in the wrong
 * palette. index.html carries the light value and the bootstrap script and
 * `applyTheme` keep it moving; the visual harness asserts it agrees with the
 * `--color-bg` token rather than with a literal either side could drift from. */
export const THEME_META_COLORS: Record<ResolvedTheme, string> = {
  light: '#fafafa',
  dark: '#15171c',
}

export function isThemeChoice(value: unknown): value is ThemeChoice {
  return value === 'light' || value === 'dark' || value === 'system'
}

/** The stored choice, or System for anything the store does not hold -
 * including a value a future build names, which is the zero-config default
 * rather than a state to guess at. */
export function readThemeChoice(): ThemeChoice {
  if (typeof localStorage === 'undefined') return 'system'
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  return isThemeChoice(stored) ? stored : 'system'
}

/** System is the only choice that asks the OS. Light and Dark are the
 * analyst's own and override it, which is why the control exists at all. */
export function resolveDark(choice: ThemeChoice, prefersDark: boolean): boolean {
  if (choice === 'dark') return true
  if (choice === 'light') return false
  return prefersDark
}

export function resolveTheme(choice: ThemeChoice, prefersDark: boolean): ResolvedTheme {
  return resolveDark(choice, prefersDark) ? 'dark' : 'light'
}

function prefersDark(): boolean {
  return typeof matchMedia !== 'undefined' && matchMedia(THEME_QUERY).matches
}

function writeMeta(resolved: ResolvedTheme): void {
  document
    .querySelector(`meta[name="${THEME_META_NAME}"]`)
    ?.setAttribute('content', THEME_META_COLORS[resolved])
}

/**
 * Applies a choice: resolves it, writes the attribute the whole stylesheet
 * keys off, keeps the meta in step, and persists the choice itself. The
 * settings row calls this on change - the dialog saves on change - and
 * `initTheme` calls it once at boot.
 *
 * Returns the resolved appearance so a caller that needs to know which
 * palette actually rendered does not re-derive it.
 */
export function applyTheme(choice: ThemeChoice): ResolvedTheme {
  const resolved = resolveTheme(choice, prefersDark())
  document.documentElement.setAttribute(THEME_ATTRIBUTE, resolved)
  writeMeta(resolved)
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(THEME_STORAGE_KEY, choice)
  }
  return resolved
}

/**
 * The boot call: resolve the stored choice before the first render, and
 * subscribe so an OS switch re-themes a running app. The attribute is also
 * written by an inline script in index.html, which runs before the bundle
 * loads; this re-applies the same choice - idempotently - and adds the one
 * listener the bootstrap cannot, because a script that ends cannot hear.
 */
export function initTheme(): void {
  const choice = readThemeChoice()
  applyTheme(choice)
  if (typeof matchMedia === 'undefined') return
  const query = matchMedia(THEME_QUERY)
  const onChange = () => {
    // Only System tracks the OS. A store holding Light or Dark while the OS
    // flipped would be the analyst's stated preference, and honouring it is
    // the reason Light and Dark are separate states.
    if (readThemeChoice() === 'system') applyTheme('system')
  }
  query.addEventListener('change', onChange)
}
