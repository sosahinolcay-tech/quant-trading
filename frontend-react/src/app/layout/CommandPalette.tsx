import { useEffect, useMemo, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { useTabsStore } from "@/state/useTabsStore";

const commands = [
  { id: "dashboard", label: "Open Dashboard" },
  { id: "chart", label: "Open Charts" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const { setActiveTabByView } = useTabsStore();

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = useMemo(() => {
    return commands.filter((cmd) => cmd.label.toLowerCase().includes(query.toLowerCase()));
  }, [query]);

  return (
    <Modal open={open} onClose={() => setOpen(false)}>
      <div className="space-y-3">
        <div className="text-sm text-muted">Command Palette</div>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search commands..."
          className="w-full rounded-xl border border-border bg-panel px-3 py-2 text-sm"
        />
        <div className="space-y-2">
          {filtered.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => {
                setActiveTabByView(cmd.id);
                setOpen(false);
                setQuery("");
              }}
              className="w-full rounded-xl bg-card px-3 py-2 text-left text-sm hover:bg-panel transition"
            >
              {cmd.label}
            </button>
          ))}
        </div>
      </div>
    </Modal>
  );
}
