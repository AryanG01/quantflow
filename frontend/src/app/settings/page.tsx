"use client";

import { useCallback } from "react";
import { api, SystemConfig } from "@/lib/api";
import { usePolling } from "@/hooks/usePolling";

const sectionMeta: Record<string, { label: string; description: string }> = {
  universe: {
    label: "Universe",
    description: "Trading pairs and exchange configuration",
  },
  risk: {
    label: "Risk Management",
    description: "Position limits, drawdown guards, kill switch",
  },
  execution: {
    label: "Execution",
    description: "Order types, slippage model, retry policy",
  },
  features: {
    label: "Features",
    description: "Technical indicators and normalization",
  },
  model: {
    label: "Model",
    description: "LightGBM parameters and walk-forward config",
  },
  regime: {
    label: "Regime Detection",
    description: "HMM states and transition thresholds",
  },
};

function renderValue(value: unknown, depth: number = 0): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-[var(--color-text-muted)]">null</span>;
  }
  if (typeof value === "boolean") {
    return (
      <span
        className={
          value
            ? "text-[var(--color-accent-green)]"
            : "text-[var(--color-accent-red)]"
        }
      >
        {String(value)}
      </span>
    );
  }
  if (typeof value === "number") {
    return <span className="text-[var(--color-accent-cyan)]">{value}</span>;
  }
  if (typeof value === "string") {
    return (
      <span className="text-[var(--color-text-primary)]">&quot;{value}&quot;</span>
    );
  }
  if (Array.isArray(value)) {
    return (
      <span className="text-[var(--color-text-secondary)]">
        [{value.map((v, i) => (
          <span key={i}>
            {i > 0 && ", "}
            {renderValue(v, depth + 1)}
          </span>
        ))}]
      </span>
    );
  }
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (depth > 1) {
      return <span className="text-[var(--color-text-muted)]">{`{${entries.length} keys}`}</span>;
    }
    return (
      <div className="ml-4 border-l border-[var(--color-border)] pl-3 space-y-1">
        {entries.map(([k, v]) => (
          <div key={k} className="flex items-start gap-2">
            <span className="text-[var(--color-text-muted)] shrink-0">{k}:</span>
            <span>{renderValue(v, depth + 1)}</span>
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

export default function SettingsPage() {
  const { data: config } = usePolling(
    useCallback(() => api.config(), []),
    30000,
  );

  return (
    <>
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm px-6 py-4 mb-4 animate-fade-in">
        <h2 className="text-sm font-semibold">System Configuration</h2>
        <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
          Read-only view of the current runtime configuration. Edit{" "}
          <code className="text-[var(--color-accent-cyan)]">config/default.yaml</code>{" "}
          to change values.
        </p>
      </div>

      {config ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger">
          {Object.keys(sectionMeta).map((key) => {
            const meta = sectionMeta[key];
            const data = config[key as keyof SystemConfig];
            return (
              <div
                key={key}
                className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4"
              >
                <div className="mb-3">
                  <h3 className="text-xs font-semibold">{meta.label}</h3>
                  <p className="text-[10px] text-[var(--color-text-muted)]">
                    {meta.description}
                  </p>
                </div>
                <div className="text-[11px] font-mono space-y-1">
                  {data && typeof data === "object" ? (
                    Object.entries(data as Record<string, unknown>).map(
                      ([k, v]) => (
                        <div key={k} className="flex items-start gap-2">
                          <span className="text-[var(--color-text-muted)] shrink-0">
                            {k}:
                          </span>
                          <span>{renderValue(v)}</span>
                        </div>
                      ),
                    )
                  ) : (
                    <span className="text-[var(--color-text-muted)]">
                      No data
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-8 text-center text-[var(--color-text-muted)] text-sm">
          Loading configuration...
        </div>
      )}

      {/* System note */}
      <div className="card-glow bg-[var(--color-bg-card)] rounded-sm p-4 mt-4">
        <h3 className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-text-muted)] mb-2">
          Note
        </h3>
        <p className="text-[10px] text-[var(--color-text-muted)]">
          Configuration is loaded at startup from YAML + environment variables.
          Changes require a service restart. The API exposes a read-only view
          for monitoring purposes.
        </p>
      </div>
    </>
  );
}
