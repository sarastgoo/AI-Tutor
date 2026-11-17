export function Progress({ value, max = 100 }: { value: number; max?: number }) {
    const pct = Math.min(100, Math.max(0, (value / max) * 100));
    return (
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    );
  }