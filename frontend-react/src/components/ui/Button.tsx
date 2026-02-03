import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/utils/format";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  const styles =
    variant === "primary"
      ? "bg-accent text-background hover:bg-accent/90"
      : "bg-white/5 text-text hover:bg-white/10";
  return (
    <button
      className={cn(
        "rounded-xl px-3 py-2 text-sm font-semibold transition",
        styles,
        className
      )}
      {...props}
    />
  );
}
