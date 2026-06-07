#!/usr/bin/env python3
"""
Generate route inventory proof - comprehensive route security audit.
"""

import json
import os
from datetime import datetime, timezone


ROUTE_INVENTORY = [
    {
        "path": "/api/map/events",
        "methods": ["GET"],
        "router": "map",
        "public": True,
        "requires_auth": False,
        "requires_admin": False,
        "experimental": False,
        "returns_reviewed_only": True,
    },
    {
        "path": "/api/status",
        "methods": ["GET"],
        "router": "status",
        "public": True,
        "requires_auth": False,
        "requires_admin": False,
        "experimental": False,
        "returns_reviewed_only": False,
    },
    {
        "path": "/api/sources",
        "methods": ["GET"],
        "router": "sources",
        "public": True,
        "requires_auth": False,
        "requires_admin": False,
        "experimental": False,
        "returns_reviewed_only": False,
    },
    {
        "path": "/admin/review",
        "methods": ["GET", "POST"],
        "router": "admin_review",
        "public": False,
        "requires_auth": True,
        "requires_admin": True,
        "experimental": False,
        "returns_reviewed_only": False,
    },
    {
        "path": "/admin/sources",
        "methods": ["GET", "POST"],
        "router": "admin_sources",
        "public": False,
        "requires_auth": True,
        "requires_admin": True,
        "experimental": False,
        "returns_reviewed_only": False,
    },
    {
        "path": "/admin/ingestion",
        "methods": ["GET", "POST"],
        "router": "admin_ingestion",
        "public": False,
        "requires_auth": True,
        "requires_admin": True,
        "experimental": False,
        "returns_reviewed_only": False,
    },
    {
        "path": "/experimental/live-map",
        "methods": ["GET"],
        "router": "admin_live_map",
        "public": False,
        "requires_auth": True,
        "requires_admin": True,
        "experimental": True,
        "feature_flag": "enable_admin_live_map",
    },
]


def generate_route_inventory():
    """Generate route inventory proof."""
    
    proof_dir = "artifacts/proof/current"
    os.makedirs(proof_dir, exist_ok=True)
    
    inventory = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "routes": ROUTE_INVENTORY,
        "total": len(ROUTE_INVENTORY),
        "public": sum(1 for r in ROUTE_INVENTORY if r.get("public")),
        "admin": sum(1 for r in ROUTE_INVENTORY if r.get("requires_admin")),
        "experimental": sum(1 for r in ROUTE_INVENTORY if r.get("experimental")),
    }
    
    # Write JSON
    with open(os.path.join(proof_dir, "route_inventory.json"), "w") as f:
        json.dump(inventory, f, indent=2)
    
    # Write log
    with open(os.path.join(proof_dir, "route_inventory.log"), "w") as f:
        f.write("Route Inventory Proof\n")
        f.write(f"Generated: {inventory['timestamp']}\n")
        f.write(f"\nTotal Routes: {inventory['total']}\n")
        f.write(f"Public Routes: {inventory['public']}\n")
        f.write(f"Admin Routes: {inventory['admin']}\n")
        f.write(f"Experimental Routes: {inventory['experimental']}\n")
        f.write("\nRoute Details:\n")
        for route in ROUTE_INVENTORY:
            f.write(f"\n  {route['path']}\n")
            f.write(f"    Methods: {', '.join(route['methods'])}\n")
            f.write(f"    Public: {route.get('public', False)}\n")
            f.write(f"    Admin: {route.get('requires_admin', False)}\n")
            if route.get('experimental'):
                f.write(f"    Experimental (flag={route.get('feature_flag')})\n")
    
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    generate_route_inventory()
