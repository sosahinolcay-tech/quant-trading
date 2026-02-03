import { Tooltip } from "@/components/ui/Tooltip";

type NavItemProps = {
  label: string;
};

export function NavItem({ label }: NavItemProps) {
  return (
    <Tooltip label={label}>
      <button className="w-full rounded-xl px-3 py-2 text-left text-sm text-muted hover:bg-card hover:text-text transition">
        {label}
      </button>
    </Tooltip>
  );
}
