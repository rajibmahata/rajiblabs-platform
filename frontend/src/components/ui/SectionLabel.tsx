interface SectionLabelProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export default function SectionLabel({ children, className = '', style }: SectionLabelProps) {
  return (
    <span className={`section-label ${className}`} style={style}>
      {children}
    </span>
  );
}
