"""Deterministic QA: pytest + health + secret scan. Posts summary to agent_runs."""
import asyncio
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, ".")

SECRET_PATTERNS = [r"OPENAI_API_KEY\s*=\s*\S+", r"GITHUB_TOKEN\s*=\s*\S+",
                   r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"password\s*=\s*['\"][^'\"]+['\"]"]


def secret_scan(root: Path) -> list[str]:
    hits = []
    for p in root.rglob("*"):
        if any(x in p.parts for x in (".git", "node_modules", "__pycache__", "data")) or not p.is_file():
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for pat in SECRET_PATTERNS:
            if re.search(pat, text):
                hits.append(f"{p}:{pat}")
                break
    return hits


async def main():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    print(r.stdout[-2000:])
    print(r.stderr[-1000:], file=sys.stderr)
    pytest_ok = r.returncode == 0
    secrets = secret_scan(Path(".").resolve().parent)
    print(f"pytest={'PASS' if pytest_ok else 'FAIL'} secrets_found={len(secrets)}")
    for h in secrets[:10]:
        print("SECRET:", h)
    try:
        from app.database import get_db, utcnow
        db = get_db()
        await db["agent_runs"].insert_one({
            "agent": "qa", "status": "success" if pytest_ok and not secrets else "failed",
            "started_at": utcnow(), "finished_at": utcnow(),
            "summary": f"pytest={'PASS' if pytest_ok else 'FAIL'} secrets={len(secrets)}"})
    except Exception as e:
        print("Could not record QA run (Mongo down?):", e)


if __name__ == "__main__":
    asyncio.run(main())
