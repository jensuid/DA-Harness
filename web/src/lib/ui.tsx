/**
 * The design system's foundation (P9-F1-001).
 *
 * Two things live here, and neither is a styled component yet: the light
 * theme as named tokens, and the primitives the panels will be built on in
 * F2. The values are the palette the hand-written CSS already used, named
 * rather than invented - the CSS stayed because it was a good light theme,
 * and because dark is a swap of these same names rather than a second theme
 * to maintain.
 *
 * F1 ships this and uses it nowhere; F2 pays the debt.
 */

import type { PropsWithChildren, ElementType, ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

// The tokens are plain class strings so a className composes them without a
// runtime dependency on a styled library. DEC-001's "no new dependency" is
// about the browser contract - the frontend never touches the filesystem or
// DuckDB directly - and a class vocabulary does not touch it.
export const tokens = {
  // The page and the surfaces on it.
  bg: 'bg-[#fafafa]',
  surface: 'bg-white',
  surfaceMuted: 'bg-[#f4f4f4]',
  // The hairlines that separate them.
  border: 'border-[#ddd]',
  // The ink.
  text: 'text-[#1a1a1a]',
  textMuted: 'text-[#666]',
  // The one accent the current CSS uses for its rules and links.
  accent: '#4a6fa5',
  accentText: 'text-[#1a4a7a]',
  // The three statuses DAH renders as text-plus-chip, never as colour alone
  // (accessibility.ts's STATUS_CLASSES audit pins this). Each is a pair: the
  // ink and the tint it sits on, so a chip reads at any size.
  ok: { text: 'text-[#2a7a2a]', bg: 'bg-[#f2f9f2]', border: 'border-[#9cc29c]' },
  warn: {
    text: 'text-[#8a6a1a]',
    bg: 'bg-[#faf6ec]',
    border: 'border-[#d9c48a]',
  },
  danger: {
    text: 'text-[#a03a2a]',
    bg: 'bg-[#faf0ee]',
    border: 'border-[#d9a094]',
  },
} as const

// The four button shapes the current CSS defines: `button`, `button.link`,
// `button.small` and `button.danger`. class-variance-authority types the
// variants so a typo is a compile error rather than an unstyled button.
export const buttonVariants = cva('button', {
  variants: {
    variant: {
      default: '',
      link: 'link',
      small: 'small',
      danger: 'danger',
    },
  },
  defaultVariants: { variant: 'default' },
})

export type ButtonVariantProps = VariantProps<typeof buttonVariants>

/**
 * The panel primitive: a bordered card with a heading and a body.
 *
 * Every surface in the workspace is a panel; F2 rebuilds each one on this
 * rather than on its own `<section className="panel">`, so the border, the
 * radius and the padding are one decision rather than thirty.
 */
export function Panel({
  children,
  className,
  as: Tag = 'section',
  ...rest
}: PropsWithChildren<{
  className?: string
  // A panel is a section by default; a form or an aside is still a panel.
  as?: ElementType
}>) {
  return (
    <Tag className={className ?? 'panel'} {...rest}>
      {children}
    </Tag>
  )
}

/**
 * The button primitive: the four shapes the CSS has today, typed.
 *
 * `type="button"` is the default because a panel's button that submits a
 * form it is not part of is a bug that reads as a page reload.
 */
export function Button({
  variant,
  className,
  type = 'button',
  ...rest
}: ButtonVariantProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={className ?? buttonVariants({ variant })}
      {...rest}
    />
  )
}

/**
 * The card primitive: a panel whose content is a titled block. The case list
 * rows and the run rows are cards; the workspace's surfaces are panels.
 */
export function Card({
  children,
  className,
  as: Tag = 'section',
  ...rest
}: PropsWithChildren<{
  className?: string
  as?: ElementType
}>) {
  return (
    <Tag className={className ?? 'panel'} {...rest}>
      {children}
    </Tag>
  )
}
