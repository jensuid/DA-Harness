/**
 * Drives headless Chrome over the DevTools protocol: captures screenshots, or
 * reads the browser's computed styles to verify a restyle.
 *
 * Node 24 ships a built-in WebSocket client, so this needs no dependency
 * (DEC-001) - it talks CDP directly.
 *
 *   node drive_chrome.js shots   # list + workspace PNGs into shots/
 *   node drive_chrome.js verify  # computed styles, printed as JSON
 *
 * The shell's navigation is state-based - there is no route for a workspace -
 * so the workspace is reached by clicking the case row the list renders, the
 * way an analyst opens it.
 *
 * Three quirks this accounts for, each of which cost a session to find:
 *
 *   - Chrome answers its debug port on `localhost`, not 127.0.0.1 (the IPv6
 *     listener is what responds), so the debug URL uses localhost.
 *   - A Chrome that shares the default profile directory exits silently
 *     rather than binding the debug port, so a dedicated --user-data-dir is
 *     required. Choose a port nobody else owns: a long-lived Chrome on this
 *     machine already holds 9222.
 *   - CSS :hover does not engage from a dispatched MouseEvent, so hover
 *     checks go through Input.dispatchMouseEvent - a real pointer move.
 */
const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = Number(process.env.DAH_CHROME_DEBUG_PORT || 9333)
const APP = process.env.DAH_SHOTS_PORT || '5274'
const APP_URL = `http://localhost:${APP}/`
const OUT = path.resolve(__dirname, 'shots')

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

/** Waits for a selector, the way a user waits for the list to fetch. */
async function waitFor(sel, timeout = 10000) {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    const found = await evaluate(`!!document.querySelector('${sel}')`)
    if (found) return true
    await sleep(300)
  }
  return false
}

async function target() {
  for (let i = 0; i < 60; i++) {
    try {
      const res = await fetch(`http://localhost:${PORT}/json`)
      const list = await res.json()
      const page = list.find((t) => t.type === 'page')
      if (page) return page
    } catch {
      /* still booting */
    }
    await sleep(250)
  }
  throw new Error('chrome did not answer on the debug port')
}

let id = 0
const pending = new Map()
let ws

async function send(method, params = {}) {
  const mid = ++id
  return new Promise((resolve, reject) => {
    pending.set(mid, { resolve, reject })
    ws.send(JSON.stringify({ id: mid, method, params }))
  })
}

function wire() {
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data)
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id)
      pending.delete(msg.id)
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result)
    }
  })
}

async function launch() {
  const chrome = spawn(
    CHROME,
    [
      '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
      `--remote-debugging-port=${PORT}`, '--window-size=1440,1600',
      '--user-data-dir=/tmp/dah-visual-chrome',
      'about:blank',
    ],
    { stdio: ['ignore', 'pipe', 'pipe'] },
  )
  const log = fs.createWriteStream('/tmp/dah-visual-chrome.log')
  chrome.stdout.pipe(log)
  chrome.stderr.pipe(log)
  chrome.on('exit', (code) => console.log(`  chrome exited code=${code}`))
  const page = await target()
  ws = new WebSocket(page.webSocketDebuggerUrl)
  await new Promise((r, rej) => {
    ws.addEventListener('open', r)
    ws.addEventListener('error', rej)
  })
  wire()
  await send('Page.enable')
  await send('Runtime.enable')
  return chrome
}

async function evaluate(expr) {
  const { result } = await send('Runtime.evaluate', {
    expression: expr,
    returnByValue: true,
    awaitPromise: true,
  })
  return result.value
}

async function shot(name) {
  const { data } = await send('Page.captureScreenshot', { format: 'png' })
  const file = path.join(OUT, `${name}.png`)
  fs.writeFileSync(file, Buffer.from(data, 'base64'))
  console.log(`  shot: ${file} (${fs.statSync(file).size} bytes)`)
}

// DMDARK: the appearance block. The token reads and the control pass below are
// what turns "it looks right" into "it measured right" - a restyle is
// verified in the browser, not in the source, and a token that was
// misspelled resolves to nothing.
const failures = []

function checkMin(label, actual, min) {
  const ok = typeof actual === 'number' && actual >= min
  if (!ok) failures.push(`${label}: ${actual} is below ${min}`)
  console.log(`  ${ok ? 'PASS' : 'FAIL'} ${label} = ${actual}`)
}

/** Records one resolved value. A check that does not match still prints, and
 *  fails the run at the end, so a pass is the record as well as the gate. */
function check(label, actual, expected) {
  const ok = actual === expected
  if (!ok) failures.push(`${label}: expected ${expected}, got ${actual}`)
  console.log(`  ${ok ? 'PASS' : 'FAIL'} ${label} = ${JSON.stringify(actual)}`)
}

/** What the browser resolved for the theme: the attribute the swap hangs on,
 *  the tokens the surfaces read, the surfaces themselves, and the chrome the
 *  host OS draws from the meta. */
async function readTheme() {
  return evaluate(`(() => {
    const root = document.documentElement
    const tok = (n) => getComputedStyle(root).getPropertyValue(n).trim()
    // WCAG contrast needs the sRGB->linear luminance, not the channel values.
    const parse = (text) => {
      const hex = /^#([0-9a-f]{6})$/i.exec((text || '').trim())
      if (hex) {
        const n = hex[1]
        return [parseInt(n.slice(0, 2), 16), parseInt(n.slice(2, 4), 16),
          parseInt(n.slice(4, 6), 16)]
      }
      const rgb = /^rgba?\\(/.test((text || '').trim())
        ? (text || '').match(/\\d+/g) : null
      return rgb ? rgb.slice(0, 3).map(Number) : null
    }
    const luminance = (text) => {
      const c = parse(text)
      if (!c) return null
      const lin = c.map((v) => {
        const s = v / 255
        return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
      })
      return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    }
    const ratio = (a, b) => {
      const la = luminance(a), lb = luminance(b)
      if (la == null || lb == null) return null
      return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
    }
    const panel = document.querySelector('.panel')
    return {
      attr: root.getAttribute('data-theme'),
      bg: tok('--color-bg'),
      surface: tok('--color-surface'),
      text: tok('--color-text'),
      accent: tok('--color-accent'),
      accentSurface: tok('--color-accent-surface'),
      danger: tok('--color-danger'),
      warn: tok('--color-warn'),
      ok: tok('--color-ok'),
      htmlBg: getComputedStyle(root).backgroundColor,
      panelBg: panel ? getComputedStyle(panel).backgroundColor : null,
      meta: document.querySelector('meta[name=theme-color]')?.content ?? null,
      stored: localStorage.getItem('dah-theme'),
      // AT-32 measured in both appearances: each surface's own text against
      // the first opaque colour behind it, which is what the analyst reads. A
      // transparent background walks up the tree, because a contrast against
      // rgba(0,0,0,0) is a contrast against nothing.
      contrast: ['.panel', '.chip', 'code', '.stage', '.decision',
        '.next-action-link', 'button.primary', '.skip-link', '.shell-notice',
        '.verdict', 'table.eda th', 'table.eda td', '.case-dataset',
        '.llm-status', '.quality-issue', '.quality-impact']
        .map((sel) => {
          const el = document.querySelector(sel)
          if (!el) return null
          const cs = getComputedStyle(el)
          let bg = cs.backgroundColor, cur = el
          while (bg === 'rgba(0, 0, 0, 0)' && cur.parentElement) {
            cur = cur.parentElement
            bg = getComputedStyle(cur).backgroundColor
          }
          return { sel, fg: cs.color, bg, ratio: ratio(cs.color, bg) }
        })
        .filter(Boolean),
      // Criterion 4's ramp: the severity climb keeps its meaning - neutral to
      // amber to red, in either appearance.
      ramp: [...document.querySelectorAll('.quality-issue')].map((el) => {
        const sev = (el.className.match(/severity-(\\w+)/) || [])[1] || 'medium'
        const cs = getComputedStyle(el)
        return { sev, border: cs.borderLeftColor, bg: cs.backgroundColor }
      }),
      // The same climb as the stylesheet renders it. The seeded case does not
      // always render an issue, so the ramp is put on the page itself and
      // read through the cascade - getComputedStyle resolves the tokens in
      // whichever appearance is active, which is what the analyst would see.
      rampRules: (() => {
        const host = document.createElement('ul')
        host.className = 'quality-issues'
        const sevs = [['quality-issue', 'medium'],
          ['quality-issue severity-high', 'high'],
          ['quality-issue severity-low', 'low']]
        sevs.forEach(([cls]) => {
          const li = document.createElement('li')
          li.className = cls
          host.appendChild(li)
        })
        document.body.appendChild(host)
        const read = [...host.children].map((li, i) => {
          const cs = getComputedStyle(li)
          return { sev: sevs[i][1], border: cs.borderLeftColor,
            bg: cs.backgroundColor }
        })
        host.remove()
        return read
      })(),
      // Every name a panel or a component rule reads. A name that was
      // misspelled resolves to an empty string and the surface falls back to
      // an inherited colour - the quiet failure a restyle can have.
      tokens: [
        '--color-bg', '--color-surface', '--color-surface-muted',
        '--color-border', '--color-text', '--color-text-muted',
        '--color-accent', '--color-accent-text', '--color-accent-surface',
        '--color-accent-strong', '--color-accent-strong-hover',
        '--color-ok', '--color-ok-bg', '--color-ok-border',
        '--color-warn', '--color-warn-bg', '--color-warn-border',
        '--color-danger', '--color-danger-bg', '--color-danger-border',
        '--color-fail', '--color-notice-ink', '--color-code-bg',
        '--color-chip-border', '--color-table-border', '--color-hairline',
        '--color-chart-grid', '--color-scrim', '--shadow-sm', '--shadow-lg',
      ].map(tok),
    }
  })()`)
}

/** The OS preference, driven through the emulator. The System state resolves
 *  through this, so this is how the harness asks for the other appearance
 *  without a second profile or a stored choice. */
async function setAppearance(preference) {
  await send('Emulation.setEmulatedMedia', {
    features: [{ name: 'prefers-color-scheme', value: preference }],
  })
  await sleep(500)
}

/** Colour meaning is hue, not hex: a status keeps its family across the swap
 *  because the family is what the analyst reads, and a status that turned
 *  grey or swapped to another hue would say something it did not. */
function hueOf(text) {
  const n = (text || '').replace('#', '')
  let rgb = /^[0-9a-f]{6}$/i.test(n)
    ? [parseInt(n.slice(0, 2), 16), parseInt(n.slice(2, 4), 16),
      parseInt(n.slice(4, 6), 16)]
    : null
  if (!rgb && /^rgba?\(/.test((text || '').trim())) {
    const found = (text || '').match(/\d+/g)
    rgb = found ? found.slice(0, 3).map(Number) : null
  }
  if (!rgb) return { h: -1, s: -1 }
  const [r, g, b] = rgb.map((v) => v / 255)
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const d = max - min
  let h = 0
  if (d > 0) {
    if (max === r) h = ((g - b) / d) % 6
    else if (max === g) h = (b - r) / d + 2
    else h = (r - g) / d + 4
    h *= 60
    if (h < 0) h += 360
  }
  return { h, s: max === 0 ? 0 : d / max }
}

function family(hex) {
  const { h, s } = hueOf(hex)
  if (s < 0.2) return 'neutral'
  if (h <= 20 || h >= 335) return 'red'
  if (h >= 35 && h < 72) return 'amber'
  if (h >= 90 && h <= 165) return 'green'
  if (h >= 195 && h <= 255) return 'blue'
  return 'other'
}

/** The climb criterion 4 names: neutral below amber below red. A ramp that
 *  flattened or inverted its order lost its meaning even if every colour in
 *  it is still a colour. */
const RAMP_ORDER = { red: 3, amber: 2 }
const rampWarmth = (name) => RAMP_ORDER[name] ?? 1

function checkRamp(theme, label) {
  const at = (sev) => theme.rampRules.find((r) => r.sev === sev)
  check(`${label} ramp low is neutral`,
    rampWarmth(family(at('low')?.border)), 1)
  check(`${label} ramp medium is amber`, family(at('medium')?.border), 'amber')
  check(`${label} ramp high is red`, family(at('high')?.border), 'red')
  check(`${label} ramp climbs`,
    rampWarmth(family(at('low')?.border)) < rampWarmth(family(at('medium')?.border))
      && rampWarmth(family(at('medium')?.border))
        < rampWarmth(family(at('high')?.border)), true)
}

/** The rgb() string the browser reports for a computed colour, so a surface's
 *  resolved colour can be compared with the colour the token it reads
 *  decodes to. */
function rgbOf(hex) {
  const n = (hex || '').replace('#', '')
  if (n.length !== 6) return null
  return `rgb(${parseInt(n.slice(0, 2), 16)}, ${parseInt(n.slice(2, 4), 16)}, `
    + `${parseInt(n.slice(4, 6), 16)})`
}

/** A real pointer click, because :focus and change ignore dispatched events
 *  the same way :hover does. */
async function clickAt(sel) {
  const box = await evaluate(`(() => {
    const el = document.querySelector('${sel}')
    if (!el) return null
    const r = el.getBoundingClientRect()
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 }
  })()`)
  if (!box) return false
  for (const type of ['mousePressed', 'mouseReleased']) {
    await send('Input.dispatchMouseEvent', {
      type, x: box.x, y: box.y, button: 'left', clickCount: 1,
    })
  }
  return true
}

async function shots() {
  await send('Page.navigate', { url: APP_URL })
  await waitFor('button.case-open')
  await shot('01-list')
  // The workspace is state-based: open it the way an analyst does.
  await evaluate(`(() => {
    const rows = document.querySelectorAll('button.case-open')
    if (rows.length) rows[0].click()
  })()`)
  await waitFor('.workflow-rail')
  await sleep(5000)
  await shot('02-workspace')
  // The workspace is taller than the viewport; the rail and the decision sit
  // below the fold, so capture the full height.
  const height = await evaluate('document.documentElement.scrollHeight')
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: Math.min(height, 4800), deviceScaleFactor: 1, mobile: false,
  })
  await sleep(2500)
  await shot('03-workspace-full')

  // DMDARK: the same surfaces in dark, captured the same way. The DOM does not
  // change - the swap is the custom properties - so the dark set is the light
  // set told that the OS prefers dark, and a diff between the two PNGs is the
  // restyle.
  await setAppearance('dark')
  await send('Page.navigate', { url: APP_URL })
  await waitFor('button.case-open')
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: 1600, deviceScaleFactor: 1, mobile: false,
  })
  await sleep(1000)
  await shot('04-dark-list')
  await evaluate(`(() => {
    const rows = document.querySelectorAll('button.case-open')
    if (rows.length) rows[0].click()
  })()`)
  await waitFor('.workflow-rail')
  await sleep(5000)
  await shot('05-dark-workspace')
  const darkHeight = await evaluate('document.documentElement.scrollHeight')
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: Math.min(darkHeight, 4800),
    deviceScaleFactor: 1, mobile: false,
  })
  await sleep(2500)
  await shot('06-dark-workspace-full')

  // Leave the browser in the neutral state for the run that follows this one.
  await evaluate('localStorage.clear()')
  await setAppearance('light')
}

/**
 * Reads what the browser actually resolved. A restyle is verified here, not in
 * the source: `getComputedStyle` is the difference between a token that
 * resolves and one that was misspelled.
 *
 * Extend this block when a new surface lands - each check is one line, and
 * the output is the record of what a pass changed.
 */
async function verify() {
  const checks = await evaluate(`(() => {
    const get = (el, ...props) => Object.fromEntries(
      props.map((p) => [p, getComputedStyle(el).getPropertyValue(p)]))
    const out = {}

    // T1: the bundled face is what renders - document.fonts.check is only
    // true when a matching face has actually been fetched and is usable.
    out.fontFamily = getComputedStyle(document.body).getPropertyValue('font-family')
    out.geistLoaded = document.fonts.check('16px Geist')

    // T2: the workspace's own question carries the display weight.
    const h1 = document.querySelector('h1')
    out.h1 = h1 ? get(h1, 'font-size', 'line-height', 'letter-spacing') : null

    // I1: a base button has a transition and reacts to the pointer.
    const btn = document.querySelector(
      'button:not(.primary):not(.link):not(.next-action-link):not(.chip)')
    out.buttonTransition = btn ? get(btn, 'transition').transition : null

    // I3: the primary verb is filled with the accent.
    const primary = document.querySelector('button.primary')
    out.primary = primary ? get(primary, 'background-color', 'color', 'font-weight') : null
    out.primaryCount = document.querySelectorAll('button.primary').length

    // L1: the two anchor surfaces carry the accent's tint.
    const rail = document.querySelector('.workflow-rail')
    out.rail = rail ? getComputedStyle(rail).getPropertyValue('background-color') : null
    const decision = document.querySelector('.decision')
    out.decision = decision
      ? getComputedStyle(decision).getPropertyValue('background-color') : null

    // L2: the spine, and the marks that mask it.
    const list = document.querySelector('.stage-list')
    out.spine = list ? getComputedStyle(list).getPropertyValue('position') : null
    out.markCount = document.querySelectorAll('.stage-mark').length
    const mark = document.querySelector('.stage-mark')
    out.mark = mark ? get(mark, 'background-color', 'width', 'height') : null

    // S1: the skip link is present and off-canvas until focused.
    const skip = document.querySelector('.skip-link')
    out.skip = skip
      ? { text: skip.textContent,
          transform: getComputedStyle(skip).getPropertyValue('transform') }
      : null

    // P2: the document metadata.
    out.icon = !!document.querySelector('link[rel=icon]')
    out.description =
      document.querySelector('meta[name=description]')?.content ?? null
    out.title = document.title
    return out
  })()`)
  console.log(JSON.stringify(checks, null, 2))

  // I1 in action: a real pointer move, because :hover ignores dispatched
  // events. Two cases - a plain button reacts, and a link-styled action keeps
  // its link character (no tint box behind inline text).
  const plain = 'button:not(.primary):not(.link):not(.next-action-link):not(.chip)'
  const hover = async (sel, label) => {
    const box = await evaluate(`(() => {
      const btn = document.querySelector('${sel}')
      if (!btn) return null
      const r = btn.getBoundingClientRect()
      return { x: r.x + r.width / 2, y: r.y + r.height / 2,
               cls: btn.className,
               before: getComputedStyle(btn).backgroundColor }
    })()`)
    if (!box) return
    await send('Input.dispatchMouseEvent', {
      type: 'mouseMoved', x: box.x, y: box.y, button: 'none',
    })
    await sleep(400)
    const after = await evaluate(`(() => {
      const btn = document.querySelector('${sel}')
      return getComputedStyle(btn).backgroundColor
    })()`)
    console.log(`hover ${label}:`, JSON.stringify(
      { cls: box.cls, before: box.before, after }))
  }
  await hover(plain, 'plain')
  await hover('.next-action-link', 'link')

  // DMDARK criterion 1: light is the appearance it was. The harness's profile
  // holds no stored choice at this point, so System resolves to the OS
  // preference, which a headless Chrome reports as light.
  let theme = await readTheme()
  check('light attr', theme.attr, 'light')
  check('light bg token', theme.bg, '#fafafa')
  check('light surface token', theme.surface, '#ffffff')
  check('light text token', theme.text, '#1a1a1a')
  // The wiring, not the values: a surface's resolved colour is the colour the
  // token it reads decodes to, which is what a misspelled property name or a
  // class that still held a hex breaks.
  check('light html wears the bg token', theme.htmlBg, rgbOf(theme.bg))
  check('light panel wears its token', theme.panelBg, rgbOf(theme.accentSurface))
  check('light meta theme-color', theme.meta, '#fafafa')
  // Criterion 5: the token set is complete and named - every name resolves.
  check('light tokens resolve',
    theme.tokens.every((t) => t.length > 0), true)
  // Criterion 4: the three statuses are their hues, in either appearance -
  // meaning is what has to survive the swap, and hue is how it is read.
  check('light danger is red', family(theme.danger), 'red')
  check('light warn is amber', family(theme.warn), 'amber')
  check('light ok is green', family(theme.ok), 'green')
  // AT-32 in this appearance: every surface the analyst reads meets 4.5:1
  // against the first opaque colour behind it, measured here rather than
  // eyeballed - the bar the light surfaces set is the bar the dark ones keep.
  for (const c of theme.contrast) {
    checkMin(`light contrast ${c.sel}`, Math.round(c.ratio * 100) / 100, 4.5)
  }
  // Criterion 4's ramp: the severity climb keeps its meaning - a low issue is
  // neutral, a default one is amber, a high one is red.
  for (const r of theme.ramp) {
    const want = r.sev === 'high' ? 'red' : r.sev === 'low' ? 'neutral' : 'amber'
    check(`light ramp ${r.sev}`, family(r.border), want)
  }
  if (!theme.ramp.length) console.log('  NOTE light ramp: no quality issues rendered')
  checkRamp(theme, 'light')

  // DMDARK criterion 2: the dark palette resolves through the same property
  // names - every surface follows the swap, and the meta tracks it, with no
  // reload and no re-render of the DOM.
  await setAppearance('dark')
  theme = await readTheme()
  check('dark attr', theme.attr, 'dark')
  check('dark bg token', theme.bg, '#15171c')
  check('dark surface token', theme.surface, '#1c1f25')
  check('dark text token', theme.text, '#e9eaee')
  check('dark html wears the bg token', theme.htmlBg, rgbOf(theme.bg))
  check('dark panel wears its token', theme.panelBg, rgbOf(theme.accentSurface))
  check('dark meta theme-color', theme.meta, '#15171c')
  check('dark tokens resolve',
    theme.tokens.every((t) => t.length > 0), true)
  check('dark danger is red', family(theme.danger), 'red')
  check('dark warn is amber', family(theme.warn), 'amber')
  check('dark ok is green', family(theme.ok), 'green')
  for (const c of theme.contrast) {
    checkMin(`dark contrast ${c.sel}`, Math.round(c.ratio * 100) / 100, 4.5)
  }
  for (const r of theme.ramp) {
    const want = r.sev === 'high' ? 'red' : r.sev === 'low' ? 'neutral' : 'amber'
    check(`dark ramp ${r.sev}`, family(r.border), want)
  }
  if (!theme.ramp.length) console.log('  NOTE dark ramp: no quality issues rendered')
  checkRamp(theme, 'dark')

  // DMDARK criterion 3: the control reaches the resolver. The banner's
  // Configure verb opens the only dialog the shell has, and the appearance
  // row is in it - the row applies on change, and System re-resolves when the
  // OS preference moves while the app is open.
  await clickAt('.llm-status button')
  check('settings dialog opens',
    await waitFor('[name="dah-appearance"]', 5000), true)

  await clickAt('input[name="dah-appearance"][value="dark"]')
  await sleep(500)
  theme = await readTheme()
  check('choice dark applies', theme.attr, 'dark')
  check('choice dark persists', theme.stored, 'dark')

  await clickAt('input[name="dah-appearance"][value="system"]')
  await sleep(500)
  check('choice system persists', (await readTheme()).stored, 'system')
  // System resolves through the emulated dark, so the surface stays dark -
  // this is the pair to the next check, and the two together are the
  // difference between System and Light.
  check('system follows the os', (await readTheme()).attr, 'dark')

  // The OS moves while the app is open: no reload, no re-render, the token
  // swap follows the preference.
  await setAppearance('light')
  check('os change re-resolves', (await readTheme()).attr, 'light')

  // The analyst's own choice does not follow the OS - that is why Light is a
  // state separate from System.
  await clickAt('input[name="dah-appearance"][value="light"]')
  await sleep(500)
  await setAppearance('dark')
  check('a stated choice holds', (await readTheme()).attr, 'light')

  await evaluate(`(() => {
    const btns = [...document.querySelectorAll('.llm-settings-actions button')]
    btns.find((b) => /Close/.test(b.textContent))?.click()
  })()`)
  await sleep(400)

  // Leave the browser as the next run expects it: the neutral state, so a
  // pass that follows this one starts from System and the OS's own light.
  await evaluate('localStorage.clear()')
  await setAppearance('light')
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true })
  const chrome = await launch()
  try {
    // The profile directory is reused across runs, so start from the
    // zero-config state - System on the OS's own preference - and clear the
    // appearance a previous run may have chosen.
    await send('Page.navigate', { url: APP_URL })
    await waitFor('button.case-open')
    await evaluate('localStorage.clear()')
    await setAppearance('light')

    if (process.argv[2] === 'verify') {
      // Verify reads the workspace, so open it the way an analyst does.
      await send('Page.navigate', { url: APP_URL })
      await waitFor('button.case-open')
      await evaluate(`(() => {
        const rows = document.querySelectorAll('button.case-open')
        if (rows.length) rows[0].click()
      })()`)
      await waitFor('.workflow-rail')
      await sleep(5000)
      await verify()
    } else {
      await shots()
    }
    console.log('  done')
    if (failures.length) {
      console.error('VERIFY FAILED:')
      failures.forEach((f) => console.error('  ' + f))
      chrome.kill()
      process.exit(1)
    }
  } finally {
    chrome.kill()
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
