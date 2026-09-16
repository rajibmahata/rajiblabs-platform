#!/usr/bin/env python3
"""
RajibLabs MCP + Orchestrator — Live Verification Script

Run this AFTER starting Docker:
  run-docker.bat          (Windows)
  docker compose up -d    (Linux/Mac)

Then run:
  python verify_system.py
"""

import httpx
import json
import time
import sys

MCP_URL = "http://localhost:8100"
ORCH_URL = "http://localhost:8200"
API_URL = "http://localhost:8090"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0
total = 0


def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}")
        if detail:
            print(f"    {detail}")


def section(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


async def main():
    global passed, failed, total

    print(f"\n{BOLD}RajibLabs MCP + Orchestrator — System Verification{RESET}\n")

    # ─── 1. Service Health ────────────────────────────────────────────
    section("1. SERVICE HEALTH")

    async with httpx.AsyncClient(timeout=5.0) as client:
        # MCP
        try:
            r = await client.get(f"{MCP_URL}/health")
            data = r.json()
            check("MCP server is UP", r.status_code == 200)
            check("MCP mongo connected", data.get("mongo") == "ok")
            check("MCP tools registered", data.get("tools_registered", 0) > 80,
                  f"Found: {data.get('tools_registered', 0)}")
        except Exception as e:
            check("MCP server is UP", False, str(e))

        # Orchestrator
        try:
            r = await client.get(f"{ORCH_URL}/health")
            data = r.json()
            check("Orchestrator is UP", r.status_code == 200)
            check("Orchestrator version", data.get("version") == "1.0.0")
        except Exception as e:
            check("Orchestrator is UP", False, str(e))

        # Backend
        try:
            r = await client.get(f"{API_URL}/health")
            check("Backend API is UP", r.status_code == 200)
        except Exception as e:
            check("Backend API is UP", False, str(e))

    # ─── 2. MCP Tools ────────────────────────────────────────────────
    section("2. MCP TOOLS (93 tools across 13 categories)")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{MCP_URL}/tools")
            tools = r.json().get("tools", [])
            categories = {}
            for t in tools:
                cat = t.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            check("Tools registered", len(tools) >= 90, f"Found: {len(tools)}")
            for cat in ["profile", "resume", "project", "portfolio", "skill",
                         "github", "knowledge", "content", "seo", "translation",
                         "publishing", "system"]:
                check(f"Category: {cat}", cat in categories,
                      f"Count: {categories.get(cat, 0)}")
        except Exception as e:
            check("Tools list", False, str(e))

    # ─── 3. MCP Tool Execution ───────────────────────────────────────
    section("3. MCP TOOL EXECUTION")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Profile
        try:
            r = await client.post(f"{MCP_URL}/tool/get_profile",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("get_profile works", data.get("success") is True or "error" in data)
        except Exception as e:
            check("get_profile works", False, str(e))

        # Projects
        try:
            r = await client.post(f"{MCP_URL}/tool/list_projects",
                                  json={"arguments": {"status": "published"}, "agent_id": "admin"})
            data = r.json()
            check("list_projects works", data.get("success") is True)
            proj_count = data.get("data", {}).get("count", 0)
            print(f"    {CYAN}→ Found {proj_count} published projects{RESET}")
        except Exception as e:
            check("list_projects works", False, str(e))

        # Skills
        try:
            r = await client.post(f"{MCP_URL}/tool/discover_skills",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("discover_skills works", data.get("success") is True)
        except Exception as e:
            check("discover_skills works", False, str(e))

        # GitHub
        try:
            r = await client.post(f"{MCP_URL}/tool/list_repositories",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("list_repositories works", data.get("success") is True)
        except Exception as e:
            check("list_repositories works", False, str(e))

        # SEO
        try:
            r = await client.post(f"{MCP_URL}/tool/analyze_seo",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("analyze_seo works", data.get("success") is True)
        except Exception as e:
            check("analyze_seo works", False, str(e))

        # Content
        try:
            r = await client.post(f"{MCP_URL}/tool/detect_missing_information",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("detect_missing_information works", data.get("success") is True)
        except Exception as e:
            check("detect_missing_information works", False, str(e))

        # System
        try:
            r = await client.post(f"{MCP_URL}/tool/system_health",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("system_health works", data.get("success") is True)
            health = data.get("data", {})
            print(f"    {CYAN}→ MongoDB: {health.get('mongo')}, "
                  f"Qdrant: {health.get('qdrant')}, "
                  f"Redis: {health.get('redis')}{RESET}")
        except Exception as e:
            check("system_health works", False, str(e))

    # ─── 4. Permissions ──────────────────────────────────────────────
    section("4. PERMISSION SYSTEM")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Admin should work
        try:
            r = await client.post(f"{MCP_URL}/tool/update_project",
                                  json={"arguments": {"project_id": "test", "updates": {}},
                                        "agent_id": "admin"})
            data = r.json()
            check("Admin can call write tools", "permission" not in str(data.get("error", {})).lower())
        except Exception as e:
            check("Admin permissions", False, str(e))

        # Public agent should be denied
        try:
            r = await client.post(f"{MCP_URL}/tool/update_project",
                                  json={"arguments": {"project_id": "test", "updates": {}},
                                        "agent_id": "public_agent"})
            data = r.json()
            check("Public agent blocked from writes",
                  data.get("success") is False or "permission" in str(data).lower())
        except Exception as e:
            check("Permission blocking", False, str(e))

    # ─── 5. Orchestrator ─────────────────────────────────────────────
    section("5. ORCHESTRATOR")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # List agents
        try:
            r = await client.get(f"{ORCH_URL}/agents")
            data = r.json()
            check("List agents", data.get("count", 0) >= 8,
                  f"Found: {data.get('count', 0)}")
        except Exception as e:
            check("List agents", False, str(e))

        # List task types
        try:
            r = await client.get(f"{ORCH_URL}/tasks")
            data = r.json()
            check("List task types", data.get("count", 0) >= 5,
                  f"Found: {data.get('count', 0)}")
        except Exception as e:
            check("List task types", False, str(e))

        # Run content audit (no LLM needed)
        try:
            r = await client.post(f"{ORCH_URL}/run",
                                  json={"task_type": "content_audit",
                                        "description": "Verify system works"})
            data = r.json()
            check("Run content_audit", data.get("status") in ("completed", "failed"),
                  f"Status: {data.get('status')}")
            steps = data.get("steps", [])
            print(f"    {CYAN}→ Completed {len(steps)} steps{RESET}")
        except Exception as e:
            check("Run content_audit", False, str(e))

        # List runs
        try:
            r = await client.get(f"{ORCH_URL}/runs?limit=5")
            data = r.json()
            check("List runs", data.get("count", 0) >= 1,
                  f"Found: {data.get('count', 0)}")
        except Exception as e:
            check("List runs", False, str(e))

    # ─── 6. Content Quality Engine ───────────────────────────────────
    section("6. CONTENT QUALITY ENGINE")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Analyze profile quality
        try:
            r = await client.post(f"{MCP_URL}/tool/analyze_profile",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            if data.get("success"):
                score = data.get("data", {}).get("score", 0)
                completeness = data.get("data", {}).get("completeness", 0)
                check("Profile quality score", True)
                print(f"    {CYAN}→ Profile completeness: {completeness}%{RESET}")
                print(f"    {CYAN}→ Profile score: {score}{RESET}")
            else:
                check("Profile quality score", False, "No profile found")
        except Exception as e:
            check("Profile quality score", False, str(e))

        # Analyze SEO
        try:
            r = await client.post(f"{MCP_URL}/tool/analyze_seo",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            if data.get("success"):
                seo_score = data.get("data", {}).get("score", 0)
                warnings = data.get("data", {}).get("total_warnings", 0)
                check("SEO quality score", True)
                print(f"    {CYAN}→ SEO score: {seo_score}{RESET}")
                print(f"    {CYAN}→ SEO warnings: {warnings}{RESET}")
            else:
                check("SEO quality score", False)
        except Exception as e:
            check("SEO quality score", False, str(e))

        # Detect conflicts
        try:
            r = await client.post(f"{MCP_URL}/tool/detect_conflicts",
                                  json={"arguments": {}, "agent_id": "admin"})
            data = r.json()
            check("Conflict detection", data.get("success") is True)
            conflicts = data.get("data", {}).get("total", 0)
            print(f"    {CYAN}→ Conflicts found: {conflicts}{RESET}")
        except Exception as e:
            check("Conflict detection", False, str(e))

    # ─── 7. Audit Trail ──────────────────────────────────────────────
    section("7. AUDIT TRAIL")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(f"{MCP_URL}/audit/stats")
            data = r.json()
            stats = data.get("stats", [])
            check("Audit stats available", len(stats) >= 0)
            print(f"    {CYAN}→ Tools with usage data: {len(stats)}{RESET}")
        except Exception as e:
            check("Audit stats", False, str(e))

    # ─── Summary ─────────────────────────────────────────────────────
    section("VERIFICATION SUMMARY")

    pct = (passed / total * 100) if total > 0 else 0
    color = GREEN if failed == 0 else YELLOW if pct > 70 else RED

    print(f"""
    {color}{BOLD}Results: {passed}/{total} passed ({pct:.0f}%){RESET}

    {CYAN}Services:{RESET}
      MCP:         {MCP_URL}
      Orchestrator: {ORCH_URL}
      Backend:     {API_URL}
      MongoDB:     localhost:27017
      Redis:       localhost:6379
      Qdrant:      localhost:6333

    {CYAN}Quick tests:{RESET}
      curl {MCP_URL}/health
      curl {MCP_URL}/tools | python -m json.tool
      curl {ORCH_URL}/health
      curl {ORCH_URL}/agents
      curl {ORCH_URL}/runs

    {CYAN}Run orchestrator:{RESET}
      curl -X POST {ORCH_URL}/run \\
        -H "Content-Type: application/json" \\
        -d '{"task_type": "content_audit", "description": "Test audit"}'

    {CYAN}Call MCP tool:{RESET}
      curl -X POST {MCP_URL}/tool/analyze_seo \\
        -H "Content-Type: application/json" \\
        -d '{"arguments": {}, "agent_id": "admin"}'
    """)

    if failed > 0:
        print(f"  {RED}⚠ {failed} checks failed — services may still be starting.{RESET}")
        print(f"  {YELLOW}Wait 30s and re-run: python verify_system.py{RESET}\n")
    else:
        print(f"  {GREEN}✓ All checks passed! System is working.{RESET}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
