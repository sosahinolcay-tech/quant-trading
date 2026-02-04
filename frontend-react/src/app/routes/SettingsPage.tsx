import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Tooltip as Hint } from "@/components/ui/Tooltip";
import { cn, formatNumber } from "@/utils/format";

type SettingsState = {
  simulation: {
    startingCash: number;
    leverage: number;
    slippageModel: "none" | "fixed" | "volume";
  };
  costs: {
    commissionBps: number;
    borrowBps: number;
  };
  risk: {
    varLimit: number;
    maxLeverage: number;
    stopLoss: number;
  };
  interface: {
    denseMode: boolean;
    showTooltips: boolean;
    showMarketStatus: boolean;
  };
};

const defaultSettings: SettingsState = {
  simulation: {
    startingCash: 250000,
    leverage: 2,
    slippageModel: "fixed",
  },
  costs: {
    commissionBps: 1.2,
    borrowBps: 8,
  },
  risk: {
    varLimit: 2.5,
    maxLeverage: 3,
    stopLoss: 4,
  },
  interface: {
    denseMode: true,
    showTooltips: true,
    showMarketStatus: true,
  },
};

const STORAGE_KEY = "qt-settings-v1";

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as SettingsState;
        setSettings({ ...defaultSettings, ...parsed });
      }
    } catch {
      setSettings(defaultSettings);
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // ignore storage errors for local-only preferences
    }
  }, [settings]);

  const updateSection = <K extends keyof SettingsState>(
    section: K,
    field: keyof SettingsState[K],
    value: SettingsState[K][typeof field]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [section]: { ...prev[section], [field]: value },
    }));
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <div className="text-sm font-semibold">Global Configuration</div>
        <div className="text-xs text-muted">Defaults that shape everything else</div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="space-y-3">
          <div className="text-sm font-semibold">Simulation</div>
          <div className="space-y-2 text-xs">
            <Hint label="Starting cash balance for every run">
              <label className="text-muted">Starting cash</label>
            </Hint>
            <input
              type="number"
              value={settings.simulation.startingCash}
              onChange={(event) =>
                updateSection("simulation", "startingCash", Number(event.target.value))
              }
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />

            <Hint label="Portfolio leverage multiplier">
              <label className="text-muted">Leverage</label>
            </Hint>
            <input
              type="number"
              step={0.1}
              value={settings.simulation.leverage}
              onChange={(event) =>
                updateSection("simulation", "leverage", Number(event.target.value))
              }
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />

            <Hint label="Execution slippage model">
              <label className="text-muted">Slippage model</label>
            </Hint>
            <select
              value={settings.simulation.slippageModel}
              onChange={(event) =>
                updateSection("simulation", "slippageModel", event.target.value as SettingsState["simulation"]["slippageModel"])
              }
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            >
              <option value="none">None</option>
              <option value="fixed">Fixed bps</option>
              <option value="volume">Volume weighted</option>
            </select>
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-sm font-semibold">Costs</div>
          <div className="space-y-2 text-xs">
            <Hint label="Commission per trade in basis points">
              <label className="text-muted">Commission (bps)</label>
            </Hint>
            <input
              type="number"
              step={0.1}
              value={settings.costs.commissionBps}
              onChange={(event) =>
                updateSection("costs", "commissionBps", Number(event.target.value))
              }
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />

            <Hint label="Borrow cost for short positions">
              <label className="text-muted">Borrow (bps)</label>
            </Hint>
            <input
              type="number"
              step={0.5}
              value={settings.costs.borrowBps}
              onChange={(event) => updateSection("costs", "borrowBps", Number(event.target.value))}
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-sm font-semibold">Risk</div>
          <div className="space-y-2 text-xs">
            <Hint label="Value-at-risk limit as % of equity">
              <label className="text-muted">VaR limit (%)</label>
            </Hint>
            <input
              type="number"
              step={0.1}
              value={settings.risk.varLimit}
              onChange={(event) => updateSection("risk", "varLimit", Number(event.target.value))}
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />

            <Hint label="Maximum gross leverage">
              <label className="text-muted">Max leverage</label>
            </Hint>
            <input
              type="number"
              step={0.1}
              value={settings.risk.maxLeverage}
              onChange={(event) =>
                updateSection("risk", "maxLeverage", Number(event.target.value))
              }
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />

            <Hint label="Hard stop loss for strategy drawdown">
              <label className="text-muted">Stop loss (%)</label>
            </Hint>
            <input
              type="number"
              step={0.5}
              value={settings.risk.stopLoss}
              onChange={(event) => updateSection("risk", "stopLoss", Number(event.target.value))}
              className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-accent/60"
            />
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-sm font-semibold">Interface</div>
          <div className="space-y-2 text-xs">
            {[
              {
                key: "denseMode",
                label: "Dense mode",
                desc: "Higher information density layout",
              },
              {
                key: "showTooltips",
                label: "Tooltips",
                desc: "Concise technical hints on hover",
              },
              {
                key: "showMarketStatus",
                label: "Market status indicator",
                desc: "Show live market session status",
              },
            ].map((option) => {
              const checked = settings.interface[option.key as keyof SettingsState["interface"]];
              return (
                <label
                  key={option.key}
                  className="flex items-center justify-between rounded-lg border border-border bg-panel/60 px-3 py-2"
                >
                  <div>
                    <div className="text-sm font-semibold">{option.label}</div>
                    <div className="text-[11px] text-muted">{option.desc}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      updateSection("interface", option.key as keyof SettingsState["interface"], !checked)
                    }
                    className={cn(
                      "h-6 w-12 rounded-full border border-border p-1 transition",
                      checked ? "bg-accent/40" : "bg-panel"
                    )}
                  >
                    <span
                      className={cn(
                        "block h-4 w-4 rounded-full bg-white transition",
                        checked && "translate-x-6"
                      )}
                    />
                  </button>
                </label>
              );
            })}
            <div className="text-[11px] text-muted">
              Settings are stored locally. Current leverage: {formatNumber(settings.simulation.leverage)}x
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
