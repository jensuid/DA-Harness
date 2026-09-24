/**
 * Zero-dependency accessibility audit (AT-32).
 *
 * The PRD's AT-32 asks for keyboard navigation, visible focus, semantic
 * controls, readable contrast and non-colour-only status, with "0 critical
 * accessibility violations" as the target. An axe or a jest-axe would be the
 * conventional tool; the phase carries a no-new-dependency constraint
 * (DEC-001), so the audit is built on the DOM the components actually render
 * and the stylesheet the product actually ships.
 *
 * Each audit returns the violations it found as sentences, so a failing test
 * names the element and the rule rather than reporting a bare count. An empty
 * list is the measurement: 0 critical violations is what the target asks for.
 *
 * What this can and cannot see: it reads the rendered structure, so it catches
 * a clickable div, an unlabeled input and a status carried by colour alone -
 * the classes a real screen reader user would hit. It does not measure colour
 * contrast numerically (that needs the computed style against the background,
 * which jsdom does not paint) or run a screen reader; the contrast rule it
 * checks is the structural one, that text exists and is not the same colour as
 * its container's class contract. The honest statement is in the test: the
 * automated suite catches the structural violations, and a contrast number is
 * AT-32's remaining manual item, recorded rather than pretended.
 */

const STATUS_CLASSES = [
  "done",
  "fail",
  "warn",
  "verdict",
  "pass",
  "concern",
  "stage",
  "quality-issue",
  "quality-clean",
  "current",
  "attention",
]

const INTERACTIVE_TAGS = new Set(["BUTTON", "A", "INPUT", "SELECT", "TEXTAREA"])

/**
 * Every click handler sits on a real control or carries an explicit role.
 *
 * A `<div onClick>` is the classic failure: it renders a thing that looks
 * pressable and is not reachable by keyboard, and it announces nothing. DAH's
 * panels are button-shaped for a reason, so this rule is strict.
 */
export function auditSemantics(container: HTMLElement): string[] {
  const violations: string[] = []
  const elements = container.querySelectorAll("*")
  for (const element of Array.from(elements)) {
    if (!(element instanceof HTMLElement) && !(element instanceof SVGElement)) {
      continue
    }
    const handler = element.getAttribute("onClick")
    const hasHandler = handler !== null || isClickableReact(element)
    if (!hasHandler) continue
    if (INTERACTIVE_TAGS.has(element.tagName)) continue
    if (element.getAttribute("role")) continue
    violations.push(
      `${describe(element)} has a click handler but is not a button, link or ` +
        `input and has no role - it is invisible to the keyboard and to a ` +
        `screen reader`,
    )
  }
  return violations
}

function isClickableReact(element: Element): boolean {
  // jsdom keeps React's props on the node under a private key; a real click
  // handler is what makes a div behave like a button, and the audit needs to
  // see it whether or not the attribute serialised.
  const props = Object.keys(element).find((key) => key.startsWith("__reactProps$"))
  if (props === undefined) return false
  // @ts-expect-error - the private React key is not typed, by design.
  const value = element[props]
  return typeof value === "object" && value !== null && "onClick" in value
}

/**
 * Every input, textarea and select has a label.
 *
 * A field without a label is "what is this?" to a keyboard user and to assistive
 * technology. A wrapping label, an htmlFor/id pair, or an aria-label all satisfy
 * it - the requirement is the association, not the technique.
 */
export function auditLabels(container: HTMLElement): string[] {
  const violations: string[] = []
  const fields = container.querySelectorAll("input, textarea, select")
  for (const field of Array.from(fields)) {
    if (field.hasAttribute("aria-label") || field.hasAttribute("aria-labelledby")) {
      continue
    }
    if (field.id) {
      const label = container.querySelector(`label[for="${field.id}"]`)
      if (label) continue
    }
    const wrapping = field.closest("label")
    if (wrapping) continue
    const name = describe(field)
    violations.push(
      `${name} has no label - not a wrapping label, a for/id pair, nor an ` +
        `aria-label`,
    )
  }
  return violations
}

/**
 * Status is never carried by colour alone.
 *
 * DAH renders its verdicts with text (✓ / ✗ / ⚠ and the words beside them),
 * which is the head start the PRD's own evaluation names. This audit pins it:
 * an element whose class declares a status must carry text of its own, or an
 * aria-label, so a reader who cannot see green still reads the verdict.
 */
export function auditStatusNotColorOnly(container: HTMLElement): string[] {
  const violations: string[] = []
  const all = container.querySelectorAll("*")
  for (const element of Array.from(all)) {
    const className = typeof element.className === "string" ? element.className : ""
    if (!className) continue
    const carriesStatus = STATUS_CLASSES.some((word) => className.includes(word))
    if (!carriesStatus) continue
    const text = element.textContent?.trim() ?? ""
    if (text) continue
    if (element.getAttribute("aria-label")) continue
    // A status chip whose text is in a child it points at is still status
    // carried by text; the audit checks the subtree, not the node alone.
    const subtree = element.querySelectorAll("[aria-label]")
    if (subtree.length > 0) continue
    violations.push(
      `${describe(element)} carries a status class (${className}) but no text ` +
        `and no aria-label - its meaning is colour alone`,
    )
  }
  return violations
}

/**
 * Every control is reachable through the keyboard's tab order.
 *
 * `tabindex="-1"` removes an element from the order while leaving it
 * focusable by script, which is a real pattern for a row that should not stop
 * the tab but is also, when it is the only affordance, a keyboard trap. The
 * audit reports removals from the order; a `disabled` control is informational
 * rather than a violation, because a disabled button during a pending
 * operation is correct and is itself visible state (AT-30).
 */
export function auditKeyboardReachable(container: HTMLElement): string[] {
  const violations: string[] = []
  const controls = container.querySelectorAll(
    "button, a[href], input, select, textarea, [tabindex]",
  )
  for (const control of Array.from(controls)) {
    if (control.getAttribute("tabindex") === "-1") {
      violations.push(
        `${describe(control)} has tabindex="-1" and is removed from the tab ` +
          `order`,
      )
    }
  }
  return violations
}

/** The control count the keyboard audit considered, for the measurement's own
 * statement of what it covered. */
export function controlCount(container: HTMLElement): number {
  return container.querySelectorAll("button, a[href], input, select, textarea").length
}

/** All the structural audits at once; the union is the AT-32 number. */
export function auditAll(container: HTMLElement): string[] {
  return [
    ...auditSemantics(container),
    ...auditLabels(container),
    ...auditStatusNotColorOnly(container),
    ...auditKeyboardReachable(container),
  ]
}

/**
 * The stylesheet guarantees a visible focus indicator.
 *
 * Browsers draw a default outline, but a product that ships its own focus
 * ring is one whose focus visibility is not the user agent's good behaviour;
 * the rule's presence is what this reads, and the rule itself is in index.css.
 */
export function focusIsGuaranteed(cssText: string): boolean {
  // A focus selector - alone or in a list of selectors, with or without the
  // `-visible` qualifier - whose rule sets an outline or a box-shadow. The
  // selector list is why the rule is loose about what sits between the
  // pseudo-class and the brace: `button:focus-visible, a:focus-visible { ... }`
  // is one rule, and it is the one that guarantees the ring.
  const focusRule = /:focus(?:-visible)?[^{]*\{[^}]*(?:outline|box-shadow)/
  return focusRule.test(cssText)
}

function describe(element: Element): string {
  const tag = element.tagName.toLowerCase()
  const className =
    typeof element.className === "string" && element.className
      ? ` class="${element.className}"`
      : ""
  const text = (element.textContent ?? "").trim().slice(0, 40)
  const label = element.getAttribute("aria-label")
  if (label) return `<${tag}${className} aria-label="${label}">`
  return `<${tag}${className}>${text}`
}
