/* Minimal safe markdown renderer: escapes all HTML first, then supports
   ##/### headings, **bold**, - lists, and [text](http(s)://...) links only.
   Anything else renders as plain paragraphs. No raw HTML ever passes through. */
import React from "react";

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s: string, key: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;
  let last = 0, i = 0, m: RegExpExecArray | null;
  while ((m = re.exec(s))) {
    if (m.index > last) parts.push(<React.Fragment key={`${key}-${i++}`}>{s.slice(last, m.index)}</React.Fragment>);
    const tok = m[0];
    if (tok.startsWith("**")) {
      parts.push(<strong key={`${key}-${i++}`}>{tok.slice(2, -2)}</strong>);
    } else {
      const label = tok.slice(1, tok.indexOf("]"));
      const url = tok.slice(tok.indexOf("](") + 2, -1).replace(/&amp;/g, "&");
      parts.push(<a key={`${key}-${i++}`} href={url} target="_blank" rel="noopener noreferrer" className="underline">{label}</a>);
    }
    last = m.index + tok.length;
  }
  if (last < s.length) parts.push(<React.Fragment key={`${key}-tail`}>{s.slice(last)}</React.Fragment>);
  return <>{parts}</>;
}

export default function Markdown({ text, className }: { text?: string | null; className?: string }) {
  const lines = esc(text || "").split("\n");
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];
  const flush = (k: string) => {
    if (list.length) {
      blocks.push(<ul key={k} className="list-disc ml-5 mt-2 space-y-1">{list.map((li, j) => <li key={j}>{inline(li, `${k}-${j}`)}</li>)}</ul>);
      list = [];
    }
  };
  lines.forEach((ln, i) => {
    const t = ln.trim();
    const li = t.match(/^[-*]\s+(.*)$/);
    if (li) { list.push(li[1]); return; }
    flush(`l${i}`);
    if (!t) return;
    const h3 = t.match(/^###\s+(.*)$/);
    if (h3) { blocks.push(<h4 key={i} className="text-lg font-semibold mt-4">{inline(h3[1], `h${i}`)}</h4>); return; }
    const h2 = t.match(/^##\s+(.*)$/);
    if (h2) { blocks.push(<h3 key={i} className="text-xl font-semibold mt-4">{inline(h2[1], `h${i}`)}</h3>); return; }
    blocks.push(<p key={i} className="mt-2">{inline(t, `p${i}`)}</p>);
  });
  flush("end");
  return <div className={className}>{blocks}</div>;
}
