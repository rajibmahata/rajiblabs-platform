type ChipCategory = 'backend' | 'cloud' | 'frontend' | 'ai' | 'tools';

interface TechChipProps {
  label: string;
  category?: ChipCategory;
  className?: string;
}

const categoryColors: Record<ChipCategory, string> = {
  backend: 'var(--c-accent-blue)',
  cloud: 'var(--c-accent-teal)',
  frontend: 'var(--c-accent-gold)',
  ai: '#8B5CF6',
  tools: 'var(--c-text-muted)',
};

export default function TechChip({ label, category = 'tools', className = '' }: TechChipProps) {
  const borderColor = categoryColors[category];

  return (
    <span
      className={`inline-block font-mono text-[11px] px-2 py-0.5 border rounded-sm transition-colors ${className}`}
      style={{
        fontFamily: 'var(--font-mono)',
        backgroundColor: 'var(--c-bg-tertiary)',
        borderColor: 'var(--c-border)',
        borderRadius: 'var(--radius-sm)',
        color: 'var(--c-text-secondary)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = borderColor;
        e.currentTarget.style.color = 'var(--c-text-primary)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--c-border)';
        e.currentTarget.style.color = 'var(--c-text-secondary)';
      }}
    >
      {label}
    </span>
  );
}
