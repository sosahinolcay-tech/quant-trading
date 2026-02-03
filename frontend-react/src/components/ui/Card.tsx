import type { HTMLAttributes } from "react";
import { cn } from "@/utils/format";

type CardProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-4 shadow-soft",
        className
      )}
      {...props}
    />
  );
}
