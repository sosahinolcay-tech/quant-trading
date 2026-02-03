import { MarketStatusIndicator } from "@/components/ui/MarketStatusIndicator";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { SearchInput } from "@/components/ui/SearchInput";

export function TopNav() {
  return (
    <header className="h-16 border-b border-border bg-panel/80 backdrop-blur">
      <div className="flex h-full items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-accent to-accent2 text-sm font-semibold text-background grid place-items-center shadow-soft">
            QT
          </div>
          <div>
            <div className="text-sm font-semibold">Quant Platform</div>
            <div className="text-xs text-muted">Data + Research Console</div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <SearchInput />
          <MarketStatusIndicator />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
