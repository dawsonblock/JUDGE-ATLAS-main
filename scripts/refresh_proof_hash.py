#!/usr/bin/env python3
"""Refresh proof_input_tree_hash across canonical artifacts after status doc sync.

Called from build_for_upload.sh after render_proof_status_docs.py updates
derived markdown files that are also proof inputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# scripts/ is on path for the import below when running from repo root,
# but allow running from any cwd by prepending the repo scripts dir.
_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir))

from check_proof_freshness import metadata_payload  # noqa: E402


CURRENT_PROOF_HASH_RE = re.compile(
    r"^(- proof_input_tree_hash:\s+)[a-f0-9]+", re.MULTILINE
)
CURRENT_PROOF_COUNT_RE = re.compile(
    r"^(- proof_input_file_count:\s+)\d+", re.MULTILINE
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    if not repo_root.is_dir():
        print(f"ERROR: root is not a directory: {repo_root}", file=sys.stderr)
        return 2

    payload = metadata_payload(repo_root)
    hash_value = payload["proof_input_tree_hash"]
    count_value = str(payload["proof_input_file_count"])

    # Update CURRENT_PROOF.md files (root and artifacts/proof/current/)
    for cp_rel in ("CURRENT_PROOF.md", "artifacts/proof/current/CURRENT_PROOF.md"):
        cp_path = repo_root / cp_rel
        if not cp_path.exists():
            continue
        cp_text = cp_path.read_text(encoding="utf-8")
        cp_text = CURRENT_PROOF_HASH_RE.sub(rf"\g<1>{hash_value}", cp_text)
        cp_text = CURRENT_PROOF_COUNT_RE.sub(rf"\g<1>{count_value}", cp_text)
        cp_path.write_text(cp_text, encoding="utf-8")

    # Update release_gate.json
    gate_path = repo_root / "artifacts" / "proof" / "current" / "release_gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate["proof_input_tree_hash"] = payload["proof_input_tree_hash"]
    gate["proof_input_file_list"] = payload["proof_input_file_list"]
    gate["proof_input_file_fingerprints"] = payload["proof_input_file_fingerprints"]
    gate["proof_input_file_count"] = payload["proof_input_file_count"]
    gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")

    # Update proof_manifest.json
    manifest_path = repo_root / "artifacts" / "proof" / "current" / "proof_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["proof_input_tree_hash"] = payload["proof_input_tree_hash"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("Proof hash refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
