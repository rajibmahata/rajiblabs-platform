import { useState, useEffect } from 'react';

interface CommitRowProps {
  hash: string;
  message: string;
  repoName: string;
  timestamp: string;
  isNew?: boolean;
}

export default function CommitRow({ hash, message, repoName, timestamp, isNew = false }: CommitRowProps) {
  const [show, setShow] = useState(!isNew);

  useEffect(() => {
    if (!isNew) return;
    const timer = setTimeout(() => setShow(true), 50);
    return () => clearTimeout(timer);
  }, [isNew]);

  const shortHash = hash.slice(0, 7);
  const truncatedMsg = message.length > 60 ? message.slice(0, 57) + '...' : message;

  return (
    <div
      className="group border-b px-4 py-3 transition-all"
      style={{
        borderColor: 'var(--c-border)',
        opacity: show ? 1 : 0,
        transform: show ? 'translateY(0)' : 'translateY(-12px)',
        transition: 'opacity 200ms var(--ease-out), transform 200ms var(--ease-out)',
        backgroundColor: isNew ? 'rgba(10,123,108,0.05)' : 'transparent',
      }}
      onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--c-bg-tertiary)'; }}
      onMouseLeave={e => {
        e.currentTarget.style.backgroundColor = isNew ? 'rgba(10,123,108,0.05)' : 'transparent';
      }}
    >
      <div className="flex items-center gap-3">
        <code style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--c-accent-blue)',
          flexShrink: 0,
        }}>
          {shortHash}
        </code>
        <span style={{
          fontFamily: 'var(--font-body)',
          fontSize: 13,
          color: 'var(--c-text-secondary)',
          flex: 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {truncatedMsg}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--c-text-muted)',
          flexShrink: 0,
          textAlign: 'right',
        }}>
          {timestamp}
        </span>
      </div>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--c-text-muted)',
        paddingLeft: 86,
        marginTop: 2,
      }}>
        {repoName}
      </div>
    </div>
  );
}
