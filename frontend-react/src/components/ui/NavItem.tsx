import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/utils/format";

type NavItemProps = {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  active?: boolean;
  tooltip?: string;
};

export function NavItem({ label, onClick, disabled, active, tooltip }: NavItemProps) {
  return (
    <Tooltip label={tooltip ?? label}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-disabled={disabled}
        className={cn(
          "w-full rounded-xl px-3 py-2 text-left text-sm transition",
          active ? "bg-card text-text shadow-soft" : "text-muted hover:bg-card hover:text-text",
          disabled && "cursor-not-allowed opacity-60 hover:bg-transparent hover:text-muted"
        )}
      >
        {label}
      </button>
    </Tooltip>
  );
}
