import { beforeEach, afterEach, vi } from 'vitest'
import '@testing-library/jest-dom'
import { MOTION_PREFERENCE_KEY } from './lib/motion'

// P9-F3: jsdom has no `matchMedia`, and framer-motion's `useReducedMotion`
// reads the preference through it - without a stub the hook answers `null`
// (preference unknown) and every motion surface animates, which is the
// default a browser gives a user who has not asked for reduced motion.
//
// The stub is a shim the test controls: a test that sets
// `prefers-reduced-motion: reduce` in the query below gets a matching list,
// and every other test gets the default. It is restored between files, so a
// test that changes the preference does not leak into the accessibility audit
// or the measurement layer.
const motionPreference: { matches: boolean } = { matches: false }

beforeEach(() => {
  motionPreference.matches = localStorage.getItem(MOTION_PREFERENCE_KEY) === 'reduce'
  const matchMedia = (query: string): MediaQueryList => ({
    matches: query.includes('prefers-reduced-motion')
      ? motionPreference.matches
      : false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })
  vi.stubGlobal('matchMedia', matchMedia)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

// The shim's own setter, for the motion test: it changes the preference a
// mounted component sees, the way a browser's change event would.
export function setMotionPreference(reduce: boolean): void {
  motionPreference.matches = reduce
}
