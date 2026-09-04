/**
 * UI-07 support: the icon half of every "colour + icon + words" signal.
 *
 * These replace the bare text glyphs (checkmark / warning sign / cross) the
 * app used previously. Those are CJK-ambiguous codepoints: with a Chinese
 * font active the browser often picks a full-width or emoji-styled variant,
 * so the same warning rendered at a different size and weight in EN and ZH.
 * Inline SVG renders identically in both languages, scales without blurring,
 * and inherits `currentColor` so it can never drift from its text label.
 *
 * All are decorative -- every caller pairs them with a real text label, so
 * they carry aria-hidden and are invisible to screen readers.
 */

export type IconName =
  | "shield"
  | "check"
  | "warning"
  | "cross"
  | "question"
  | "dash"
  | "text"
  | "link"
  | "image"
  | "sparkle";

const PATHS: Record<IconName, React.ReactNode> = {
  // Brand mark: a shield with a check inside -- verification, not decoration.
  shield: (
    <>
      <path d="M12 3 4.5 6v5.5c0 4.3 3.2 8.3 7.5 9.5 4.3-1.2 7.5-5.2 7.5-9.5V6L12 3Z" />
      <path d="m8.75 11.75 2.25 2.25 4.25-4.25" />
    </>
  ),
  check: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </>
  ),
  warning: (
    <>
      <path d="M12 4.5 3.5 19h17L12 4.5Z" />
      <path d="M12 10v4" />
      <path d="M12 16.75h.01" />
    </>
  ),
  cross: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m9.25 9.25 5.5 5.5M14.75 9.25l-5.5 5.5" />
    </>
  ),
  question: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M9.75 9.5a2.25 2.25 0 1 1 2.9 2.15c-.55.18-.9.7-.9 1.28v.32" />
      <path d="M12 16.75h.01" />
    </>
  ),
  dash: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M8.5 12h7" />
    </>
  ),
  text: (
    <>
      <path d="M5 5.5h14" />
      <path d="M5 10.5h14" />
      <path d="M5 15.5h9" />
    </>
  ),
  link: (
    <>
      <path d="M10.5 13.5a3.5 3.5 0 0 0 5 0l2.5-2.5a3.54 3.54 0 0 0-5-5l-1.4 1.4" />
      <path d="M13.5 10.5a3.5 3.5 0 0 0-5 0L6 13a3.54 3.54 0 0 0 5 5l1.4-1.4" />
    </>
  ),
  image: (
    <>
      <rect x="3.75" y="5.25" width="16.5" height="13.5" rx="2" />
      <circle cx="8.75" cy="10.25" r="1.25" />
      <path d="m4.5 16.5 4.25-4 3 2.75 2.75-2.5 5 4.75" />
    </>
  ),
  sparkle: <path d="M12 4.5l1.9 4.6 4.6 1.9-4.6 1.9L12 17.5l-1.9-4.6-4.6-1.9 4.6-1.9L12 4.5Z" />,
};

export default function Icon({
  name,
  className = "h-5 w-5",
  strokeWidth = 1.75,
}: {
  name: IconName;
  className?: string;
  strokeWidth?: number;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  );
}
