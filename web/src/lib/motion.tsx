/**
 * The motion layer (P9-F3).
 *
 * Two things live here, and neither is an animation yet: the vocabulary of
 * variants the surfaces use, and the one gate that decides whether any of
 * them runs. The vocabulary is named the way the tokens name colour, so a
 * surface reads one name and the decision is made once for all of them; the
 * gate is `prefers-reduced-motion`, which the CSS has honoured for the shell
 * notice (`index.css`'s explicit `animation: none` rule) and the JS-driven
 * motion now honours too rather than only the CSS-driven kind.
 *
 * The discipline is a motion budget: an animation that costs a frame the
 * measurement layer counts (AT-27's 200ms interaction response, AT-30's
 * visible state) is a regression, not a polish. Every variant here is the
 * cheapest thing that reads - an opacity and a short slide over a spring -
 * and every transition is inside the budget, so a disclosure's open does not
 * outlast the interaction that opened it.
 */

import type { HTMLMotionProps, Variants } from 'framer-motion'
import { MotionConfig, motion, useReducedMotionConfig } from 'framer-motion'
import type { PropsWithChildren } from 'react'

/**
 * The transitions. One duration for the surfaces a click opens (the
 * disclosure speed AT-27 measures), a longer one for the content a case
 * loads, and a spring only where a verdict lands - the loop's exit deserves
 * more weight than a row opening, and a spring is the cheapest way to give
 * it that.
 *
 * Nothing here approaches the interaction budget: a disclosure that takes
 * 300ms to settle is a disclosure that costs the response time the
 * measurement layer pins, so the surfaces stay well under it.
 */
export const transitions = {
  // The surfaces a click opens: a run row's rows, a chart's controls, the
  // draft panel. The interaction that opened it is already done; the motion
  // is the confirmation, and it must not outlast the budget.
  surface: { duration: 0.18, ease: 'easeOut' },
  // The content a case loads: the panels appear as the case opens, once, and
  // a longer settle reads as a considered surface rather than a flicker. This
  // is the longest transition in the layer and it is still inside the budget,
  // because it runs once per open rather than per interaction.
  enter: { duration: 0.28, ease: 'easeOut' },
  // The loop's exit: a verdict or a decision landing. A spring carries more
  // weight than an ease, which is the right read for the sentence the
  // analyst has been working toward - and its settle is inside the budget.
  arrive: { type: 'spring', stiffness: 220, damping: 24, mass: 0.7 },
} as const

/**
 * The variant names, as a type so a surface's `variant` prop is the vocabulary
 * itself: a typo is a compile error rather than a silent default.
 */
export type VariantName = keyof typeof variants

/**
 * The variants. Each is framer-motion's own shape - the `hidden` state a
 * surface starts in and the `shown` state it comes to rest in - with the
 * transition riding inside the target, so a surface reads one name and both
 * the motion and its cost are decided once.
 *
 * The distances are small on purpose. A surface that slides its own height
 * pushes the panels below it, and layout shift is the cost the measurement
 * layer counts; 6px is a movement the eye reads as arrival without moving
 * anything else on the page.
 */
export const variants = {
  // A panel's content appearing as the case loads. The opacity is the whole
  // effect and the slide is the suggestion of it.
  enter: {
    hidden: { opacity: 0, y: 6 },
    shown: { opacity: 1, y: 0, transition: transitions.enter },
  } satisfies Variants,
  // A run row opening, a chart's controls appearing, a draft panel landing:
  // the disclosure vocabulary, and the shortest motion this layer uses.
  open: {
    hidden: { opacity: 0, y: 4 },
    shown: { opacity: 1, y: 0, transition: transitions.surface },
  } satisfies Variants,
  // A verdict or a decision arriving. The scale is the weight: it comes to
  // rest at 1 rather than undershooting, and the spring's settle is what
  // carries the arrival.
  arrive: {
    hidden: { opacity: 0, scale: 0.98 },
    shown: { opacity: 1, scale: 1, transition: transitions.arrive },
  } satisfies Variants,
} as const

/**
 * The gate. `prefers-reduced-motion` is the analyst's own setting, read the
 * same way the CSS reads it, so the JS-driven motion honours it rather than
 * only the CSS-driven kind.
 *
 * `reducedMotion="user"` is framer-motion's own resolution of the preference:
 * a child `motion` component animates normally until the analyst asks for
 * reduced motion, and then every variant collapses to its end state - the
 * content appears, nothing moves. That is the behaviour the CSS gives the
 * shell notice (`animation: none`), and this is the same rule for the motion
 * the JS drives.
 *
 * `useReducedMotion()` is framer-motion's own hook: it answers the OS setting,
 * resolved once and then fixed for the life of the element. `useReducedMotionConfig()`
 * folds the app's own `MotionConfig` in, so a component that has to know the
 * answer asks the same question the built-in motion components ask - and the
 * gate is one resolution rather than two a component can see differently.
 * The hook is for a transition a component composes by hand; the gate does
 * the work for everything else.
 */
export {
  useReducedMotion,
  useReducedMotionConfig,
} from 'framer-motion'

/**
 * The gate component: mount once, near the root, and every motion surface
 * below it resolves the analyst's preference through it.
 *
 * `reducedMotion="user"` is framer-motion's own resolution: it reads the OS
 * setting through `matchMedia` and hands it to every child. `"always"` and
 * `"never"` are the same resolution with the decision made by the app instead
 * - which is what makes the gate testable, because jsdom has no `matchMedia`
 * and a preference the test cannot set cannot be tested.
 */
export function ReducedMotion({ children }: PropsWithChildren) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>
}

/**
 * The motion surface: a `motion.div` pre-bound to this layer's vocabulary, so
 * a panel names a variant and the gate does the rest.
 *
 * The default variant is `enter`, because most surfaces are a panel's content
 * arriving as the case loads. The surface is a `div` - the wrapper the panels
 * already render - and a surface that is not one takes the wrapper rather than
 * a second tag type, so the vocabulary stays one component.
 *
 * The collapse is this layer's own, not framer-motion's: the library makes
 * positional keys instant under reduced motion but still fades opacity, and a
 * reduced-motion setting that still moves the surface is a setting the
 * surface is not honouring. `initial={false}` renders the variant's end state
 * with no animation at all, so an analyst who asks for reduced motion gets
 * content that is simply there - the same result the CSS gives the shell
 * notice.
 */
export function MotionSurface({
  children,
  variant = 'enter',
  ...rest
}: PropsWithChildren<{ variant?: VariantName }> & HTMLMotionProps<'div'>) {
  const reduce = useReducedMotionConfig()
  return (
    <motion.div
      data-motion-surface=""
      variants={variants[variant]}
      // A surface that starts hidden and is never animated to shown is
      // invisible content; under reduced motion the end state is the only
      // state, so `initial` points at it rather than at the hidden one.
      initial={reduce ? false : 'hidden'}
      animate="shown"
      {...rest}
    >
      {children}
    </motion.div>
  )
}

/**
 * The localStorage key the motion shim reads, and the one a test writes to
 * ask for reduced motion before the component mounts. jsdom has no
 * `matchMedia`, so the shim in `setup-tests.ts` is what makes the gate
 * testable - and this key is its interface, kept here so the motion layer
 * owns the name the test uses.
 */
export const MOTION_PREFERENCE_KEY = 'dah-prefers-reduced-motion'

/**
 * The gate is closed: a boolean for a component that composes its own
 * transition. `null` is "not determined yet" (the preference was never read),
 * which reads as motion allowed - the same default framer-motion's own hook
 * gives, and the same one the CSS gives a user who has not asked.
 */
export function motionAllowed(reduce: boolean | null): boolean {
  return reduce !== true
}
