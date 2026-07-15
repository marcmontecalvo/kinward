import type { ReactNode } from "react";

export type StackProps = {
  gap?: "xs" | "sm" | "md";
  className?: string;
  children: ReactNode;
};

const stackGapClass: Record<NonNullable<StackProps["gap"]>, string> = {
  xs: "kw-stack-xs",
  sm: "kw-stack-sm",
  md: "kw-stack-md",
};

/** Vertical flex composition with a tokenized gap — never an inline style. */
export function Stack({ gap = "sm", className, children }: StackProps) {
  return <div className={["kw-stack", stackGapClass[gap], className].filter(Boolean).join(" ")}>{children}</div>;
}

export type ClusterProps = {
  gap?: "xs" | "sm";
  className?: string;
  children: ReactNode;
};

const clusterGapClass: Record<NonNullable<ClusterProps["gap"]>, string> = {
  xs: "kw-cluster-xs",
  sm: "kw-cluster-sm",
};

/** Horizontal, wrapping flex composition with a tokenized gap. */
export function Cluster({ gap = "sm", className, children }: ClusterProps) {
  return <div className={["kw-cluster", clusterGapClass[gap], className].filter(Boolean).join(" ")}>{children}</div>;
}
