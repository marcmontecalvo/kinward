import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "pill";

type NativeButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children">;

export type ButtonProps = NativeButtonProps & {
  variant?: ButtonVariant;
  children: ReactNode;
};

const variantClass: Record<ButtonVariant, string> = {
  primary: "kw-button-primary",
  secondary: "secondary-action",
  pill: "kw-button-pill",
};

/**
 * Always a real <button> — disabled state uses the native `disabled`
 * attribute (never aria-disabled-only), so it's excluded from the tab
 * order and announced correctly without extra wiring. Minimum target size
 * comes from the global `button, input { min-height: var(--kw-target-min) }`
 * rule, not repeated here.
 */
export function Button({ variant = "primary", children, ...nativeProps }: ButtonProps) {
  return (
    <button type="button" className={variantClass[variant]} {...nativeProps}>
      {children}
    </button>
  );
}
