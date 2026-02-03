import { cn } from "@/utils/format";

type TabButtonProps = {
  label: string;
  active?: boolean;
  onClick?: () => void;
};

export function TabButton({ label, active, onClick }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-xl px-3 py-2 text-sm transition",
        active ? "bg-accent text-background" : "bg-white/5 text-muted hover:text-text"
      )}
    >
      {label}
    </button>
  );
}
