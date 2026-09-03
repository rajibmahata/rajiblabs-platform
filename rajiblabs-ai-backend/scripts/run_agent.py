"""Manual daily-agent trigger. Usage: python scripts/run_agent.py"""
import asyncio
import sys
sys.path.insert(0, ".")
from app.agents.daily_agent import run_daily_agent


if __name__ == "__main__":
    print(asyncio.run(run_daily_agent(triggered_by="manual")))
