import type { ElementType, ReactNode } from "react";

export type HeadingLevel = 1 | 2 | 3;

const headingTag: Record<HeadingLevel, ElementType> = { 1: "h1", 2: "h2", 3: "h3" };

export type HeadingProps = {
  level: HeadingLevel;
  id?: string;
  className?: string;
  children: ReactNode;
};

/** Semantic heading — the level prop always maps to a real h1/h2/h3, never a styled div. */
export function Heading({ level, id, className, children }: HeadingProps) {
  const Tag = headingTag[level];
  return <Tag id={id} className={className}>{children}</Tag>;
}

export type TextProps = {
  tone?: "primary" | "secondary" | "faint";
  as?: "p" | "span";
  id?: string;
  className?: string;
  children: ReactNode;
};

const toneClass: Record<NonNullable<TextProps["tone"]>, string> = {
  primary: "",
  secondary: "muted",
  faint: "kw-text-faint",
};

export function Text({ tone = "primary", as = "p", id, className, children }: TextProps) {
  const Tag = as;
  const classes = [toneClass[tone], className].filter(Boolean).join(" ");
  return <Tag id={id} className={classes || undefined}>{children}</Tag>;
}

export type EyebrowProps = {
  className?: string;
  children: ReactNode;
};

/** The small tracked uppercase label used for section/moment eyebrows. */
export function Eyebrow({ className, children }: EyebrowProps) {
  return <p className={["eyebrow", className].filter(Boolean).join(" ")}>{children}</p>;
}
