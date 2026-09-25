// The shell's half of FIX-UPDATES-009 (W-005): the native Check for Updates
// menu item performed a check the core distinguishes three ways and then told
// only stderr about it, so on this private repository - where the feed always
// answers 404 - the item was permanently, silently dead. The shell is the only
// host with a menu bar, so it owns the delivery.
//
// The shell gains no dependency for this (DEC-001), and it uses no native
// dialog: `tauri-plugin-dialog` is a network-fetched plugin on Tauri 2, and
// the app is deliberately offline once installed. What the shell already has
// is the React bundle in its window, so the delivery is the bundle's own
// surface. The shell evaluates a script in the webview it already holds that
// posts an event the bundle listens for, and the bundle's own notice layer
// renders it. A browser host never receives the event, because a browser has
// no menu item to answer for.
//
// The status vocabulary is the core's own (`server/app/updates.py`): a status
// of `available` names the newer build, `current` is the claim the feed was
// reached and nothing newer exists, and `unknown` is the honest "could not
// tell" carrying a reason. The shell passes that vocabulary through to the
// window untouched - it does not reword an unreachable feed into "up to date",
// which is exactly the lie P6-UPDATE-005 built this check to avoid.

/** The custom event the shell dispatches. `notice_script` in
 * `desktop/src-tauri/src/updates.rs` builds this name into the script it
 * evaluates; a Rust test guards the agreement by reading this file as text. */
export const NOTICE_EVENT = 'dah-notice'

/** Where the shell stashes a notice that arrived before this bundle mounted -
 * the menu item can fire in the second between the window showing and the
 * bundle finishing. Read once on mount, never polled. */
export const NOTICE_ATTR = 'data-dah-notice'

/**
 * Turn the JSON body of `GET /updates/latest` into the sentence a window shows.
 *
 * Mirrors `update_summary` in the shell, so the window and the shell's log line
 * always say the same thing about the same answer.
 *
 * Everything degrades to a sentence rather than an error, for the same reason
 * logs.rs does: a body the shell cannot interpret is a state to report, and a
 * notice that renders "could not tell" is honest where one that panics leaves
 * the menu item looking dead a second time.
 */
export function describeUpdate(body: unknown): string {
  if (typeof body !== 'object' || body === null) {
    return 'Could not check for updates: the core sent a body this build does not recognise.'
  }
  const status = readString(body, 'status')
  const current = readString(body, 'current') || 'unknown'
  if (status === 'available') {
    const latest = readString(body, 'latest') || 'a newer build'
    const page = readString(body, 'page_url')
    return page
      ? `DAH ${current} is installed and ${latest} is available - download it at ${page}`
      : `DAH ${current} is installed and ${latest} is available, but the release did not name a download page.`
  }
  if (status === 'current') {
    const latest = readString(body, 'latest') || 'this build'
    return `DAH ${current} is up to date - ${latest} is latest published build.`
  }
  // `unknown`, and any status this build has never heard of: the reason is the
  // sentence to show, and a missing reason is itself reported rather than
  // swapped for a claim the check never made.
  const reason = readString(body, 'reason')
  return reason
    ? `Could not check for updates: ${reason}`
    : 'Could not check for updates: the core could not determine the latest build.'
}

function readString(body: object, key: string): string {
  const value = (body as Record<string, unknown>)[key]
  return typeof value === 'string' ? value : ''
}
