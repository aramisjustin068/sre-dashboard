#!/usr/bin/env python3
"""Validate a Grafana dashboard JSON definition.

Checks that every panel has the fields an on-call engineer needs to
understand at 03:00: title, type, datasource, gridPos, and at least one
target with an expression. Also checks for duplicate panel IDs and
missing top-level fields.

Usage:
    python3 validate.py dashboard.json
    python3 validate.py dashboard.json --strict

Exit codes:
    0 — all checks passed
    1 — validation errors found (printed to stderr)
    2 — file could not be read or parsed
"""

import json
import sys
from pathlib import Path

REQUIRED_PANEL_FIELDS = {"id", "title", "type", "datasource", "gridPos", "targets"}
REQUIRED_DASHBOARD_FIELDS = {"title", "schemaVersion", "panels", "refresh"}
REQUIRED_TARGET_FIELDS = {"expr", "refId"}


def validate_dashboard(data: dict, strict: bool = False) -> list[str]:
    errors: list[str] = []

    # Top-level fields
    for field in REQUIRED_DASHBOARD_FIELDS:
        if field not in data:
            errors.append(f"missing top-level field: {field}")

    panels = data.get("panels", [])
    if not panels:
        errors.append("dashboard has no panels")
        return errors

    seen_ids: set[int] = set()

    for i, panel in enumerate(panels):
        prefix = f"panel[{i}] (id={panel.get('id', '?')})"

        # Required fields
        for field in REQUIRED_PANEL_FIELDS:
            if field not in panel:
                errors.append(f"{prefix}: missing field '{field}'")

        # Title must not be empty
        title = panel.get("title", "")
        if not title or not title.strip():
            errors.append(f"{prefix}: empty title")

        # Type must be a known Grafana panel type
        ptype = panel.get("type", "")
        valid_types = {
            "timeseries", "stat", "table", "gauge", "bar gauge",
            "heatmap", "graph", "singlestat", "barplot", "row",
        }
        if ptype and ptype not in valid_types and strict:
            errors.append(f"{prefix}: unknown panel type '{ptype}'")

        # gridPos must have x, y, w, h
        grid = panel.get("gridPos", {})
        for gp_field in ("x", "y", "w", "h"):
            if gp_field not in grid:
                errors.append(f"{prefix}: gridPos missing '{gp_field}'")

        # Duplicate IDs
        pid = panel.get("id")
        if pid is not None:
            if pid in seen_ids:
                errors.append(f"{prefix}: duplicate panel id {pid}")
            seen_ids.add(pid)

        # Targets: at least one with an expression
        targets = panel.get("targets", [])
        if ptype != "row" and not targets:
            errors.append(f"{prefix}: no targets defined")
        else:
            for j, t in enumerate(targets):
                tpref = f"{prefix}.target[{j}]"
                for tf in REQUIRED_TARGET_FIELDS:
                    if tf not in t:
                        errors.append(f"{tpref}: missing '{tf}'")
                expr = t.get("expr", "")
                if not expr or not expr.strip():
                    errors.append(f"{tpref}: empty expression")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate.py <dashboard.json> [--strict]", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 2

    errors = validate_dashboard(data, strict=strict)

    if errors:
        print(f"{len(errors)} validation error(s) in {path.name}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    panels = data.get("panels", [])
    print(f"OK: {len(panels)} panel(s) validated, all required fields present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
