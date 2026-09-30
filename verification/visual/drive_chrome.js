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
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true })
  const chrome = await launch()
  try {
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
  } finally {
    chrome.kill()
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
