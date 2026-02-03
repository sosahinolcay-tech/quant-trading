import { CommandPalette } from "@/app/layout/CommandPalette";
import { SideNav } from "@/app/layout/SideNav";
import { TabWorkspace } from "@/app/layout/TabWorkspace";
import { TopNav } from "@/app/layout/TopNav";

export function AppShell() {
  return (
    <div className="h-full bg-background text-text">
      <TopNav />
      <div className="flex h-[calc(100%-64px)]">
        <SideNav />
        <main className="flex-1 overflow-hidden">
          <TabWorkspace />
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
