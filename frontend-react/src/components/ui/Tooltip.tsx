import type { ReactNode } from "react";

type TooltipProps = {
  label: string;
  children: ReactNode;
};

export function Tooltip({ label, children }: TooltipProps) {
  return (
    <span className="group relative inline-flex items-center">
      {children}
      <span className="pointer-events-none absolute bottom-full mb-2 hidden whitespace-nowrap rounded-lg border border-border bg-panel px-2 py-1 text-xs text-muted shadow-soft group-hover:block">
        {label}
      </span>
    </span>
  );
}
