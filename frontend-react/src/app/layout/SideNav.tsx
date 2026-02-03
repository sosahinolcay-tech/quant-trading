import { NavItem } from "@/components/ui/NavItem";
import { useUiStore } from "@/state/useUiStore";

const items = [
  { label: "Dashboards", id: "dashboard" },
  { label: "Screener", id: "screener" },
  { label: "Charts", id: "charts" },
  { label: "Strategies", id: "strategies" },
  { label: "Portfolio", id: "portfolio" },
  { label: "Settings", id: "settings" },
];

export function SideNav() {
  const { sidebarCollapsed, toggleSidebar } = useUiStore();
  return (
    <aside
      className={`border-r border-border bg-panel/90 py-6 transition-all ${
        sidebarCollapsed ? "w-16 px-2" : "w-60 px-4"
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-muted">{sidebarCollapsed ? "Nav" : "Workspace"}</span>
        <button onClick={toggleSidebar} className="text-xs text-muted hover:text-text">
          {sidebarCollapsed ? "›" : "‹"}
        </button>
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <NavItem key={item.id} label={sidebarCollapsed ? item.label[0] : item.label} />
        ))}
      </div>
    </aside>
  );
}
