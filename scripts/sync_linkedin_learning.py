#!/usr/bin/env python3
"""
LinkedIn Learning Data Fetcher for Rajib Labs
Usage: python3 sync_linkedin_learning.py

Reads courses from linkedin_courses.json and syncs to the backend API.
Can also be run with --fetch to pull from a configured source.
Run as daily cron: 0 10 * * * python3 sync_linkedin_learning.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = os.environ.get("RAJIBLABS_API", "http://localhost:5099")
COURSES_FILE = os.path.join(os.path.dirname(__file__), "linkedin_courses.json")

# Fallback: sample courses when no data file exists
SAMPLE_COURSES = [
    {
        "title": "Azure Microservices with .NET",
        "url": "https://www.linkedin.com/learning/azure-microservices-with-dot-net",
        "instructor": "Rodrigo Díaz Concha",
        "duration": "4h 12m",
        "level": "Advanced",
        "status": "in-progress"
    },
    {
        "title": "Building RAG Applications with LLMs",
        "url": "https://www.linkedin.com/learning/building-rag-applications-with-llms",
        "instructor": "Kesha Williams",
        "duration": "2h 35m",
        "level": "Intermediate",
        "status": "in-progress"
    },
    {
        "title": "React: Design Patterns",
        "url": "https://www.linkedin.com/learning/react-design-patterns",
        "instructor": "Shaun Wassell",
        "duration": "3h 20m",
        "level": "Advanced",
        "status": "completed"
    }
]


def load_courses():
    """Load courses from JSON file, fall back to samples if not found."""
    if os.path.exists(COURSES_FILE):
        with open(COURSES_FILE) as f:
            courses = json.load(f)
            if courses:
                return courses

    print(f"No courses found in {COURSES_FILE}, using sample data")
    # Save samples so they can be edited
    with open(COURSES_FILE, 'w') as f:
        json.dump(SAMPLE_COURSES, f, indent=2)
    return SAMPLE_COURSES


def sync_course(course):
    """POST a course to the backend API."""
    url = f"{API_BASE}/api/learning"
    data = json.dumps(course).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.URLError as e:
        return getattr(e, 'code', 0), {"error": str(e)}


def main():
    courses = load_courses()
    synced = 0
    errors = 0

    for course in courses:
        if not course.get('title'):
            continue
        code, result = sync_course(course)
        if code in (200, 201):
            synced += 1
            print(f"  ✅ {course['title'][:60]}")
        else:
            errors += 1
            print(f"  ❌ {course['title'][:60]} — {result.get('error', 'unknown')}")

    print(f"\nSynced: {synced} | Errors: {errors}")


if __name__ == '__main__':
    # Allow --fetch flag (future: could pull from LinkedIn API/RSS)
    if '--fetch' in sys.argv:
        print("Fetch mode not yet implemented. Edit linkedin_courses.json to add courses.")

    main()
