#!/usr/bin/env python3
"""Static smoke validation for critical frontend Next.js routes.

This check verifies that the core route files expected by proof and
release workflows are present in the frontend app tree.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_APP = REPO_ROOT / "frontend" / "app"

REQUIRED_ROUTE_FILES: tuple[str, ...] = (
    "page.tsx",
    "login/page.tsx",
    "dashboard/page.tsx",
    "map/page.tsx",
    "sources/page.tsx",
    "cases/page.tsx",
    "cases/[id]/page.tsx",
    "judges/page.tsx",
    "judges/[id]/page.tsx",
    "defendants/page.tsx",
    "defendants/[id]/page.tsx",
    "admin/layout.tsx",
    "admin/review/page.tsx",
    "admin/sources/page.tsx",
    "admin/status/page.tsx",
    "admin/ai-checks/page.tsx",
)


def main() -> int:
    if not FRONTEND_APP.exists():
        print("RESULT: FAIL")
        print(f"  missing frontend app root: {FRONTEND_APP}")
        return 1

    missing: list[str] = []
    for rel in REQUIRED_ROUTE_FILES:
        if not (FRONTEND_APP / rel).is_file():
            missing.append(f"frontend/app/{rel}")

    if missing:
        print("RESULT: FAIL")
        print("  missing critical route files:")
        for rel in missing:
            print(f"    - {rel}")
        return 1

    print("RESULT: PASS")
    print(f"  checked_route_files: {len(REQUIRED_ROUTE_FILES)}")
    print("  critical_routes_present: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())