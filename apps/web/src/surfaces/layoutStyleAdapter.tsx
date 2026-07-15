import type { CSSProperties, ReactNode } from "react";

/**
 * THE audited layout-style adapter (AC2). This is the one file in the
 * codebase allowed to set inline JSX styles — enforced by eslint.config.js's
 * file-scoped exception — and even here it may only set the declared layout
 * custom properties below. It accepts no arbitrary style object; every
 * value it can set is named and typed. The actual visual rules those
 * properties feed (grid-template-columns, gap, grid-column, grid-row) live
 * in styles.css, referencing them as any other token.
 */

export type LayoutGridProps = {
  columns: number;
  gapPx: number;
  className?: string;
  "aria-label"?: string;
  children: ReactNode;
};

export function LayoutGrid({ columns, gapPx, className, children, ...aria }: LayoutGridProps) {
  const style = {
    "--kw-layout-columns": columns,
    "--kw-layout-gap": `${gapPx}px`,
  } as CSSProperties;
  return (
    <section className={className} style={style} {...aria}>
      {children}
    </section>
  );
}

export type LayoutItemProps = {
  id: string;
  column: number;
  row: number;
  columns: number;
  rows: number;
  className?: string;
  "data-instance-id"?: string;
  children: ReactNode;
};

export function LayoutItem({ id, column, row, columns, rows, className, children, ...data }: LayoutItemProps) {
  const style = {
    "--kw-layout-column-start": column,
    "--kw-layout-column-span": columns,
    "--kw-layout-row-start": row,
    "--kw-layout-row-span": rows,
  } as CSSProperties;
  return (
    <div id={id} className={className} style={style} {...data}>
      {children}
    </div>
  );
}
