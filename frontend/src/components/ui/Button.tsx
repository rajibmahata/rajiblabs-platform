import type { ReactNode, ButtonHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'gold';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  asLink?: boolean;
  href?: string;
}

const baseStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 6,
  fontFamily: 'var(--font-heading)',
  fontWeight: 500,
  borderRadius: 'var(--radius-md)',
  cursor: 'pointer',
  transition: 'all 200ms var(--ease-out)',
  border: 'none',
  textDecoration: 'none',
  whiteSpace: 'nowrap',
};

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--c-accent-blue)',
    color: '#fff',
    border: '1px solid transparent',
  },
  outline: {
    backgroundColor: 'transparent',
    color: 'var(--c-accent-blue)',
    border: '1px solid var(--c-accent-blue)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--c-text-secondary)',
    border: '1px solid var(--c-border)',
  },
  gold: {
    backgroundColor: 'transparent',
    color: 'var(--c-accent-gold)',
    border: '1px solid var(--c-accent-gold)',
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: { padding: '6px 14px', fontSize: 12 },
  md: { padding: '10px 20px', fontSize: 14 },
  lg: { padding: '13px 28px', fontSize: 15 },
};

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  asLink = false,
  href,
  style,
  ...props
}: ButtonProps) {
  const combined: React.CSSProperties = {
    ...baseStyle,
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  };

  const handleMouseEnter = (e: React.MouseEvent) => {
    const el = e.currentTarget as HTMLElement;
    if (variant === 'primary') {
      el.style.backgroundColor = 'var(--c-accent-blue-l)';
      el.style.boxShadow = 'var(--shadow-glow-blue)';
      el.style.transform = 'translateY(-1px)';
    } else if (variant === 'outline') {
      el.style.backgroundColor = 'var(--c-accent-blue)';
      el.style.color = '#fff';
      el.style.transform = 'translateY(-1px)';
    } else if (variant === 'ghost') {
      el.style.borderColor = 'var(--c-accent-blue)';
      el.style.color = 'var(--c-text-primary)';
      el.style.transform = 'translateY(-1px)';
    } else if (variant === 'gold') {
      el.style.backgroundColor = 'var(--c-accent-gold)';
      el.style.color = 'var(--c-bg-primary)';
      el.style.transform = 'translateY(-1px)';
    }
  };

  const handleMouseLeave = (e: React.MouseEvent) => {
    const el = e.currentTarget as HTMLElement;
    el.style.backgroundColor = variantStyles[variant].backgroundColor || '';
    el.style.color = variantStyles[variant].color || '';
    el.style.boxShadow = '';
    el.style.borderColor = variantStyles[variant].borderColor || '';
    el.style.transform = '';
  };

  if (asLink && href) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={combined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </a>
    );
  }

  return (
    <button
      style={combined}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {children}
    </button>
  );
}
