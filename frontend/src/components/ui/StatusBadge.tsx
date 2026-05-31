type StatusVariant = 'live' | 'wip' | 'beta' | 'offline' | 'complete';

interface StatusBadgeProps {
  variant: StatusVariant;
  label?: string;
  className?: string;
}

const variantConfig: Record<StatusVariant, { color: string; defaultLabel: string; pulse: boolean }> = {
  live:     { color: 'var(--c-accent-teal)',  defaultLabel: 'LIVE',     pulse: true },
  wip:      { color: 'var(--c-accent-blue)',  defaultLabel: 'WIP',      pulse: false },
  beta:     { color: '#F59E0B',               defaultLabel: 'BETA',     pulse: false },
  offline:  { color: '#6B7280',               defaultLabel: 'OFFLINE',  pulse: false },
  complete: { color: 'var(--c-accent-teal)',  defaultLabel: 'COMPLETE', pulse: false },
};

export default function StatusBadge({ variant, label, className = '' }: StatusBadgeProps) {
  const config = variantConfig[variant];
  const displayLabel = label || config.defaultLabel;

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider ${className}`}
      style={{ letterSpacing: '0.08em' }}
      aria-label={`Status: ${displayLabel}`}
    >
      <span
        className={`inline-block w-2 h-2 rounded-full ${config.pulse ? 'pulse-dot' : ''}`}
        style={{
          backgroundColor: config.color,
          animation: config.pulse ? undefined : 'none',
        }}
      />
      <span style={{ color: config.color }}>
        {displayLabel}
      </span>
    </span>
  );
}
